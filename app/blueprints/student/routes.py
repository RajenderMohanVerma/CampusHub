"""Student Controller handling conflict-free resource scheduling and academic profile management."""
from datetime import date, datetime
from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.extensions import db
from app.blueprints.student import student_bp
from app.utils import role_required, tenant_required
from app.forms.student import BookingRequestForm, StudentProfileForm
from app.models import Resource, Booking, Student, Notification, ActivityLog, User


@student_bp.route('/dashboard')
@login_required
@role_required('student')
@tenant_required
def dashboard():
    """Student Home Dashboard."""
    cid = current_user.college_id
    total_resources = Resource.query.filter_by(college_id=cid, is_active=True).count()
    my_pending = Booking.query.filter_by(college_id=cid, user_id=current_user.id, status='pending').count()
    my_approved = Booking.query.filter_by(college_id=cid, user_id=current_user.id, status='approved').count()
    
    recent_bookings = Booking.query.filter_by(college_id=cid, user_id=current_user.id).order_by(Booking.created_at.desc()).limit(6).all()
    featured_resources = Resource.query.filter_by(college_id=cid, is_active=True).limit(3).all()
    
    return render_template('student/dashboard.html',
                           total_resources=total_resources,
                           my_pending=my_pending,
                           my_approved=my_approved,
                           recent_bookings=recent_bookings,
                           featured_resources=featured_resources)


@student_bp.route('/catalog')
@login_required
@role_required('student')
@tenant_required
def catalog():
    """Browse available campus resources inside the student's college tenant."""
    cid = current_user.college_id
    type_filter = request.args.get('type', 'all')
    
    if type_filter != 'all':
        resources_list = Resource.query.filter_by(college_id=cid, is_active=True, resource_type=type_filter).order_by(Resource.name.asc()).all()
    else:
        resources_list = Resource.query.filter_by(college_id=cid, is_active=True).order_by(Resource.name.asc()).all()
        
    return render_template('student/catalog.html', resources_list=resources_list, type_filter=type_filter)


@student_bp.route('/book/<int:resource_id>', methods=['GET', 'POST'])
@login_required
@role_required('student')
@tenant_required
def book_resource(resource_id):
    """Interactive conflict-free reservation gateway."""
    cid = current_user.college_id
    res = Resource.query.filter_by(id=resource_id, college_id=cid, is_active=True).first_or_404()
    form = BookingRequestForm()
    
    # Fetch existing approved or pending slots for this resource to display to the student
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
            flash(f"⚠️ TIME SLOT CONFLICT DETECTED! Your requested interval ({form.start_time.data.strftime('%H:%M')} - {form.end_time.data.strftime('%H:%M')}) overlaps with existing {collision.status.upper()} Booking #BKG-{collision.id} ({collision.start_time.strftime('%I:%M %p')} - {collision.end_time.strftime('%I:%M %p')}). Please pick a vacant slot.", "danger")
            return render_template('student/book_resource.html', form=form, resource=res, existing_slots=existing_slots)
            
        student_prof = Student.query.filter_by(user_id=current_user.id).first()
        dept_id = student_prof.department_id if student_prof else None
        
        # Deploy conflict-free booking application
        new_booking = Booking(
            college_id=cid,
            user_id=current_user.id,
            department_id=dept_id,
            resource_id=res.id,
            booking_date=form.booking_date.data,
            start_time=form.start_time.data,
            end_time=form.end_time.data,
            purpose=form.purpose.data.strip(),
            status='pending'
        )
        db.session.add(new_booking)
        db.session.flush()
        
        # Alert College Admin regarding pending reservation
        admins = User.query.filter_by(college_id=cid, role='college_admin').all()
        for admin_user in admins:
            Notification.create_notification(
                user_id=admin_user.id,
                college_id=cid,
                title="New Reservation Request",
                message=f"Student {current_user.full_name} applied for '{res.name}' on {new_booking.booking_date.strftime('%b %d')} ({new_booking.start_time.strftime('%I:%M %p')}).",
                category="warning",
                link_url="/admin/bookings?status=pending"
            )
            
        ActivityLog.log("BOOKING_REQUESTED", user_id=current_user.id, college_id=cid, entity_type="Booking", entity_id=new_booking.id, details=f"Student applied for resource: {res.name}")
        db.session.commit()
        
        flash(f"Reservation application for '{res.name}' submitted successfully! [STATUS: PENDING ADMIN APPROVAL]", "success")
        return redirect(url_for('student.my_bookings'))
        
    return render_template('student/book_resource.html', form=form, resource=res, existing_slots=existing_slots)


@student_bp.route('/my-bookings')
@login_required
@role_required('student')
@tenant_required
def my_bookings():
    """Review student's booking trajectory and approval updates."""
    cid = current_user.college_id
    bookings_list = Booking.query.filter_by(college_id=cid, user_id=current_user.id).order_by(Booking.booking_date.desc(), Booking.start_time.desc()).all()
    return render_template('student/my_bookings.html', bookings_list=bookings_list)


@student_bp.route('/booking/<int:booking_id>/cancel', methods=['POST'])
@login_required
@role_required('student')
@tenant_required
def cancel_booking(booking_id):
    """Cancel a pending reservation slot."""
    cid = current_user.college_id
    booking = Booking.query.filter_by(id=booking_id, college_id=cid, user_id=current_user.id).first_or_404()
    if booking.status in ['pending', 'approved']:
        booking.status = 'cancelled'
        ActivityLog.log("BOOKING_CANCELLED", user_id=current_user.id, college_id=cid, entity_type="Booking", entity_id=booking.id, details="User revoked reservation request.")
        db.session.commit()
        flash(f"Booking #BKG-{booking.id} has been successfully CANCELLED and the time slot is freed.", "info")
    else:
        flash("You cannot cancel a booking that is already processed as rejected or cancelled.", "warning")
    return redirect(request.referrer or url_for('student.my_bookings'))


@student_bp.route('/profile', methods=['GET', 'POST'])
@login_required
@role_required('student')
@tenant_required
def profile():
    """Student profile viewing and configuration."""
    student_record = Student.query.filter_by(user_id=current_user.id).first()
    form = StudentProfileForm()
    
    if request.method == 'GET' and student_record:
        form.phone.data = current_user.phone
        form.course_name.data = student_record.course_name
        
    if form.validate_on_submit():
        current_user.phone = form.phone.data.strip()
        if student_record:
            student_record.course_name = form.course_name.data.strip()
        db.session.commit()
        flash("Academic profile metadata updated successfully!", "success")
        return redirect(url_for('student.profile'))
        
    return render_template('student/profile.html', student_record=student_record, form=form)
