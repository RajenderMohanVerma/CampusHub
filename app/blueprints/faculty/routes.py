"""Faculty Controller managing research equipment reservation, classroom schedules, and academic staff profiles."""
from datetime import date, datetime
from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.extensions import db
from app.blueprints.faculty import faculty_bp
from app.utils import role_required, tenant_required
from app.forms.student import BookingRequestForm # Reuse robust collision-validated booking form
from app.forms.faculty import FacultyProfileForm
from app.models import Resource, Booking, Faculty, Notification, ActivityLog, User, Department


@faculty_bp.route('/dashboard')
@login_required
@role_required('faculty')
@tenant_required
def dashboard():
    """Faculty Professor Portal Dashboard."""
    cid = current_user.college_id
    total_resources = Resource.query.filter_by(college_id=cid, is_active=True).count()
    my_pending = Booking.query.filter_by(college_id=cid, user_id=current_user.id, status='pending').count()
    my_approved = Booking.query.filter_by(college_id=cid, user_id=current_user.id, status='approved').count()
    
    # Upcoming scheduled teaching and lab sessions
    my_schedule = Booking.query.filter(
        Booking.college_id == cid,
        Booking.user_id == current_user.id,
        Booking.booking_date >= date.today()
    ).order_by(Booking.booking_date.asc(), Booking.start_time.asc()).limit(6).all()
    
    # Priority campus resources suitable for faculty
    featured = Resource.query.filter_by(college_id=cid, is_active=True).order_by(Resource.capacity.desc()).limit(3).all()
    
    return render_template('faculty/dashboard.html',
                           total_resources=total_resources,
                           my_pending=my_pending,
                           my_approved=my_approved,
                           my_schedule=my_schedule,
                           featured=featured)


@faculty_bp.route('/catalog')
@login_required
@role_required('faculty')
@tenant_required
def catalog():
    """Browse high-end facilities and laboratories inside the university workspace."""
    cid = current_user.college_id
    type_filter = request.args.get('type', 'all')
    if type_filter != 'all':
        resources_list = Resource.query.filter_by(college_id=cid, is_active=True, resource_type=type_filter).order_by(Resource.name.asc()).all()
    else:
        resources_list = Resource.query.filter_by(college_id=cid, is_active=True).order_by(Resource.name.asc()).all()
    return render_template('faculty/catalog.html', resources_list=resources_list, type_filter=type_filter)


@faculty_bp.route('/book/<int:resource_id>', methods=['GET', 'POST'])
@login_required
@role_required('faculty')
@tenant_required
def book_resource(resource_id):
    """Faculty reservation wizard featuring instantaneous time slot collision interception."""
    cid = current_user.college_id
    res = Resource.query.filter_by(id=resource_id, college_id=cid, is_active=True).first_or_404()
    form = BookingRequestForm()
    
    existing_slots = Booking.query.filter(
        Booking.resource_id == res.id,
        Booking.booking_date >= date.today(),
        Booking.status.in_(['approved', 'pending'])
    ).order_by(Booking.booking_date.asc(), Booking.start_time.asc()).all()

    if form.validate_on_submit():
        # RUN REALTIME ZERO-COLLISION CHECK
        collision = Booking.check_collision(
            college_id=cid,
            resource_id=res.id,
            booking_date=form.booking_date.data,
            start_time=form.start_time.data,
            end_time=form.end_time.data
        )
        if collision:
            flash(f"⚠️ TIME SLOT CONFLICT DETECTED! Your faculty scheduling interval overlaps with existing {collision.status.upper()} Booking #BKG-{collision.id} ({collision.start_time.strftime('%I:%M %p')} - {collision.end_time.strftime('%I:%M %p')}). Please choose another timeline.", "danger")
            return render_template('faculty/book_resource.html', form=form, resource=res, existing_slots=existing_slots)
            
        fac_prof = Faculty.query.filter_by(user_id=current_user.id).first()
        dept_id = fac_prof.department_id if fac_prof else None
        
        new_booking = Booking(
            college_id=cid,
            user_id=current_user.id,
            department_id=dept_id,
            resource_id=res.id,
            booking_date=form.booking_date.data,
            start_time=form.start_time.data,
            end_time=form.end_time.data,
            purpose=f"[FACULTY PRIORITY] {form.purpose.data.strip()}",
            status='pending'
        )
        db.session.add(new_booking)
        db.session.flush()
        
        # Alert College Admin regarding high-priority faculty request
        admins = User.query.filter_by(college_id=cid, role='college_admin').all()
        for au in admins:
            Notification.create_notification(
                user_id=au.id,
                college_id=cid,
                title="Priority Faculty Booking Request",
                message=f"Prof. {current_user.full_name} applied for '{res.name}' on {new_booking.booking_date.strftime('%b %d')} ({new_booking.start_time.strftime('%I:%M %p')}).",
                category="info",
                link_url="/admin/bookings?status=pending"
            )
            
        ActivityLog.log("FACULTY_BOOKING_REQUESTED", user_id=current_user.id, college_id=cid, entity_type="Booking", entity_id=new_booking.id, details=f"Faculty booked resource: {res.name}")
        db.session.commit()
        
        flash(f"Faculty priority booking for '{res.name}' submitted successfully! [STATUS: PENDING ADMIN APPROVAL]", "success")
        return redirect(url_for('faculty.my_bookings'))
        
    return render_template('faculty/book_resource.html', form=form, resource=res, existing_slots=existing_slots)


@faculty_bp.route('/my-bookings')
@login_required
@role_required('faculty')
@tenant_required
def my_bookings():
    """Review faculty teaching schedule and reservation trajectory."""
    cid = current_user.college_id
    bookings_list = Booking.query.filter_by(college_id=cid, user_id=current_user.id).order_by(Booking.booking_date.desc(), Booking.start_time.desc()).all()
    return render_template('faculty/my_bookings.html', bookings_list=bookings_list)


@faculty_bp.route('/booking/<int:booking_id>/cancel', methods=['POST'])
@login_required
@role_required('faculty')
@tenant_required
def cancel_booking(booking_id):
    """Revoke a faculty reservation slot."""
    cid = current_user.college_id
    booking = Booking.query.filter_by(id=booking_id, college_id=cid, user_id=current_user.id).first_or_404()
    if booking.status in ['pending', 'approved']:
        booking.status = 'cancelled'
        ActivityLog.log("FACULTY_BOOKING_CANCELLED", user_id=current_user.id, college_id=cid, entity_type="Booking", entity_id=booking.id, details="Faculty cancelled reservation.")
        db.session.commit()
        flash(f"Faculty Booking #BKG-{booking.id} has been CANCELLED and the resource freed.", "info")
    else:
        flash("You cannot cancel an inactive or rejected reservation.", "warning")
    return redirect(request.referrer or url_for('faculty.my_bookings'))


@faculty_bp.route('/profile', methods=['GET', 'POST'])
@login_required
@role_required('faculty')
@tenant_required
def profile():
    """Manage faculty profile metadata and staff designation."""
    fac_record = Faculty.query.filter_by(user_id=current_user.id).first()
    form = FacultyProfileForm()
    
    if request.method == 'GET' and fac_record:
        form.phone.data = current_user.phone
        form.designation.data = fac_record.designation
        form.specialization.data = fac_record.specialization
        
    if form.validate_on_submit():
        current_user.phone = form.phone.data.strip()
        if fac_record:
            fac_record.designation = form.designation.data.strip()
            if form.specialization.data:
                fac_record.specialization = form.specialization.data.strip()
        db.session.commit()
        flash("Faculty academic metadata updated successfully!", "success")
        return redirect(url_for('faculty.profile'))
        
    return render_template('faculty/profile.html', fac_record=fac_record, form=form)
