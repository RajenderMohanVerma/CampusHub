"""College Admin Controller enforcing strict tenancy (current_user.college_id) over campus assets and approvals."""
from datetime import date, datetime, timedelta
from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.extensions import db
from app.blueprints.college_admin import college_admin_bp
from app.utils import role_required, tenant_required
from app.forms.college_admin import DepartmentForm, ResourceForm, MemberAddForm, BookingApprovalForm
from app.models import Department, Resource, User, Faculty, Student, Booking, Notification, ActivityLog, Report


@college_admin_bp.route('/dashboard')
@login_required
@role_required('college_admin')
@tenant_required
def dashboard():
    """Tenant Executive Dashboard scoped strictly to current_user.college_id."""
    cid = current_user.college_id
    
    # Strictly scoped metrics
    dept_count = Department.query.filter_by(college_id=cid).count()
    res_count = Resource.query.filter_by(college_id=cid).count()
    faculty_count = User.query.filter_by(college_id=cid, role='faculty').count()
    student_count = User.query.filter_by(college_id=cid, role='student').count()
    
    pending_bookings_count = Booking.query.filter_by(college_id=cid, status='pending').count()
    approved_bookings_count = Booking.query.filter_by(college_id=cid, status='approved').count()
    
    # Pending action queue
    pending_bookings = Booking.query.filter_by(college_id=cid, status='pending').order_by(Booking.created_at.asc()).limit(6).all()
    
    # Recent activity logs for this tenant only
    recent_activity = ActivityLog.query.filter_by(college_id=cid).order_by(ActivityLog.timestamp.desc()).limit(8).all()
    
    # Resource category breakdown for Chart.js
    res_types = ['Computer Lab', 'Classroom', 'Seminar Hall', 'Conference Room', 'Projector', 'Equipment']
    res_type_counts = [Resource.query.filter_by(college_id=cid, resource_type=rt).count() for rt in res_types]
    
    return render_template('college_admin/dashboard.html',
                           dept_count=dept_count,
                           res_count=res_count,
                           faculty_count=faculty_count,
                           student_count=student_count,
                           pending_bookings_count=pending_bookings_count,
                           approved_bookings_count=approved_bookings_count,
                           pending_bookings=pending_bookings,
                           recent_activity=recent_activity,
                           res_types=res_types,
                           res_type_counts=res_type_counts)


@college_admin_bp.route('/departments', methods=['GET', 'POST'])
@login_required
@role_required('college_admin')
@tenant_required
def departments():
    """CRUD manager for campus departments."""
    cid = current_user.college_id
    form = DepartmentForm()
    if form.validate_on_submit():
        dept = Department(
            college_id=cid,
            name=form.name.data.strip(),
            code=form.code.data.strip().upper(),
            head_name=form.head_name.data.strip() if form.head_name.data else None,
            description=form.description.data.strip() if form.description.data else None
        )
        db.session.add(dept)
        ActivityLog.log("DEPT_CREATED", user_id=current_user.id, college_id=cid, entity_type="Department", details=f"Added dept: {dept.name} ({dept.code})")
        db.session.commit()
        flash(f"Department '{dept.name}' (#{dept.code}) successfully established!", "success")
        return redirect(url_for('college_admin.departments'))
        
    dept_list = Department.query.filter_by(college_id=cid).order_by(Department.name.asc()).all()
    return render_template('college_admin/departments.html', form=form, dept_list=dept_list)


@college_admin_bp.route('/resources', methods=['GET', 'POST'])
@login_required
@role_required('college_admin')
@tenant_required
def resources():
    """CRUD manager for physical and digital campus resources."""
    cid = current_user.college_id
    form = ResourceForm()
    if form.validate_on_submit():
        res = Resource(
            college_id=cid,
            name=form.name.data.strip(),
            resource_type=form.resource_type.data,
            capacity=form.capacity.data,
            location=form.location.data.strip(),
            description=form.description.data.strip() if form.description.data else None,
            is_active=form.is_active.data
        )
        if form.image_url.data:
            res.image_url = form.image_url.data.strip()
        db.session.add(res)
        ActivityLog.log("RESOURCE_DEPLOYED", user_id=current_user.id, college_id=cid, entity_type="Resource", details=f"Deployed {res.resource_type}: {res.name}")
        db.session.commit()
        flash(f"Campus Resource '{res.name}' deployed into operational catalog!", "success")
        return redirect(url_for('college_admin.resources'))
        
    res_list = Resource.query.filter_by(college_id=cid).order_by(Resource.resource_type.asc(), Resource.name.asc()).all()
    return render_template('college_admin/resources.html', form=form, res_list=res_list)


@college_admin_bp.route('/faculty', methods=['GET', 'POST'])
@login_required
@role_required('college_admin')
@tenant_required
def faculty_list():
    """Manage faculty directory and onboard new teaching staff."""
    cid = current_user.college_id
    form = MemberAddForm()
    
    # Populate departments for select box
    depts = Department.query.filter_by(college_id=cid).all()
    form.department_id.choices = [(d.id, f"{d.name} ({d.code})") for d in depts]
    if not form.department_id.choices:
        form.department_id.choices = [(0, 'General Campus Hub')]

    if form.validate_on_submit():
        email_lower = form.email.data.strip().lower()
        if User.query.filter_by(email=email_lower).first():
            flash("User with this email already registered in system.", "danger")
            return redirect(url_for('college_admin.faculty_list'))
            
        u = User(
            email=email_lower,
            first_name=form.first_name.data.strip(),
            last_name=form.last_name.data.strip(),
            phone=form.phone.data.strip(),
            role="faculty",
            college_id=cid,
            is_active=True
        )
        u.set_password("faculty123")
        db.session.add(u)
        db.session.flush()
        
        dept_id = form.department_id.data if form.department_id.data != 0 else None
        fac = Faculty(
            user_id=u.id,
            college_id=cid,
            department_id=dept_id,
            employee_id=form.identifier.data.strip().upper(),
            designation=form.extra_field.data.strip(),
            specialization="Academic Faculty Research"
        )
        db.session.add(fac)
        ActivityLog.log("FACULTY_ONBOARDED", user_id=current_user.id, college_id=cid, details=f"Registered faculty: {u.full_name} ({u.email})")
        db.session.commit()
        flash(f"Faculty Professor '{u.full_name}' onboarded successfully! Default sign-in: faculty123", "success")
        return redirect(url_for('college_admin.faculty_list'))
        
    faculties = Faculty.query.filter_by(college_id=cid).join(User).order_by(User.first_name.asc()).all()
    return render_template('college_admin/faculty_list.html', form=form, faculties=faculties)


@college_admin_bp.route('/students', methods=['GET', 'POST'])
@login_required
@role_required('college_admin')
@tenant_required
def student_list():
    """Manage student body directory and enroll new candidates."""
    cid = current_user.college_id
    form = MemberAddForm()
    
    depts = Department.query.filter_by(college_id=cid).all()
    form.department_id.choices = [(d.id, f"{d.name} ({d.code})") for d in depts]
    if not form.department_id.choices:
        form.department_id.choices = [(0, 'General Academic Student')]

    if form.validate_on_submit():
        email_lower = form.email.data.strip().lower()
        if User.query.filter_by(email=email_lower).first():
            flash("User with this email already registered in system.", "danger")
            return redirect(url_for('college_admin.student_list'))
            
        u = User(
            email=email_lower,
            first_name=form.first_name.data.strip(),
            last_name=form.last_name.data.strip(),
            phone=form.phone.data.strip(),
            role="student",
            college_id=cid,
            is_active=True
        )
        u.set_password("student123")
        db.session.add(u)
        db.session.flush()
        
        dept_id = form.department_id.data if form.department_id.data != 0 else None
        stud = Student(
            user_id=u.id,
            college_id=cid,
            department_id=dept_id,
            enrollment_number=form.identifier.data.strip().upper(),
            course_name=form.extra_field.data.strip(),
            semester=1
        )
        db.session.add(stud)
        ActivityLog.log("STUDENT_ENROLLED", user_id=current_user.id, college_id=cid, details=f"Enrolled student: {u.full_name} ({u.email})")
        db.session.commit()
        flash(f"Student '{u.full_name}' enrolled successfully! Default password: student123", "success")
        return redirect(url_for('college_admin.student_list'))
        
    students = Student.query.filter_by(college_id=cid).join(User).order_by(User.first_name.asc()).all()
    return render_template('college_admin/student_list.html', form=form, students=students)


@college_admin_bp.route('/bookings')
@login_required
@role_required('college_admin')
@tenant_required
def bookings():
    """Centralized booking approval management hub."""
    cid = current_user.college_id
    status_filter = request.args.get('status', 'pending')
    if status_filter in ['pending', 'approved', 'rejected', 'all']:
        if status_filter == 'all':
            bookings_list = Booking.query.filter_by(college_id=cid).order_by(Booking.booking_date.desc(), Booking.start_time.asc()).all()
        else:
            bookings_list = Booking.query.filter_by(college_id=cid, status=status_filter).order_by(Booking.booking_date.asc()).all()
    else:
        bookings_list = Booking.query.filter_by(college_id=cid, status='pending').all()
        
    form = BookingApprovalForm()
    return render_template('college_admin/bookings.html', bookings_list=bookings_list, status_filter=status_filter, form=form)


@college_admin_bp.route('/booking/<int:booking_id>/decide/<action>', methods=['POST'])
@login_required
@role_required('college_admin')
@tenant_required
def decide_booking(booking_id, action):
    """Approve or Reject a student/faculty booking request with administrative feedback note."""
    cid = current_user.college_id
    booking = Booking.query.filter_by(id=booking_id, college_id=cid).first_or_404()
    form = BookingApprovalForm()
    
    remark = form.admin_remark.data.strip() if form.admin_remark.data else "Reviewed by College Administrator."
    
    if action == 'approve':
        # Re-check collision just in case another admin approved a conflicting slot
        conflict = Booking.check_collision(
            college_id=cid,
            resource_id=booking.resource_id,
            booking_date=booking.booking_date,
            start_time=booking.start_time,
            end_time=booking.end_time,
            exclude_booking_id=booking.id
        )
        if conflict and conflict.status == 'approved':
            flash(f"Cannot approve! Time-slot conflict detected with Approved Booking #BKG-{conflict.id} ({conflict.start_time.strftime('%H:%M')}-{conflict.end_time.strftime('%H:%M')}).", "danger")
            return redirect(url_for('college_admin.bookings', status='pending'))
            
        booking.status = 'approved'
        booking.approved_by_id = current_user.id
        booking.admin_remark = remark
        
        Notification.create_notification(
            user_id=booking.user_id,
            college_id=cid,
            title="Booking Request Approved! 🎉",
            message=f"Your reservation for '{booking.resource.name}' on {booking.booking_date.strftime('%b %d')} has been APPROVED by Admin. Remark: {remark}",
            category="success",
            link_url="/student/booking-history" if booking.user.role == 'student' else "/faculty/my-bookings"
        )
        ActivityLog.log("BOOKING_APPROVED", user_id=current_user.id, college_id=cid, entity_type="Booking", entity_id=booking.id, details=f"Approved reservation for {booking.user.full_name}")
        flash(f"Booking #BKG-{booking.id} APPROVED! User notified via real-time telemetry.", "success")
        
    elif action == 'reject':
        booking.status = 'rejected'
        booking.approved_by_id = current_user.id
        booking.admin_remark = remark
        
        Notification.create_notification(
            user_id=booking.user_id,
            college_id=cid,
            title="Booking Request Rejected",
            message=f"Your request for '{booking.resource.name}' on {booking.booking_date.strftime('%b %d')} could not be approved. Admin note: {remark}",
            category="danger",
            link_url="/student/booking-history" if booking.user.role == 'student' else "/faculty/my-bookings"
        )
        ActivityLog.log("BOOKING_REJECTED", user_id=current_user.id, college_id=cid, entity_type="Booking", entity_id=booking.id, details=f"Rejected reservation for {booking.user.full_name}")
        flash(f"Booking #BKG-{booking.id} has been REJECTED with note.", "warning")
        
    db.session.commit()
    return redirect(request.referrer or url_for('college_admin.bookings', status='pending'))


@college_admin_bp.route('/reports')
@login_required
@role_required('college_admin')
@tenant_required
def reports():
    """College resource utilization and departmental activity reports."""
    cid = current_user.college_id
    depts = Department.query.filter_by(college_id=cid).all()
    dept_names = [d.code for d in depts]
    dept_bookings = [Booking.query.filter_by(college_id=cid, department_id=d.id).count() for d in depts]
    
    # Status distribution
    statuses = ['approved', 'pending', 'rejected', 'cancelled']
    status_counts = [Booking.query.filter_by(college_id=cid, status=s).count() for s in statuses]
    
    all_resources = Resource.query.filter_by(college_id=cid).all()
    
    return render_template('college_admin/reports.html',
                           depts=depts,
                           dept_names=dept_names,
                           dept_bookings=dept_bookings,
                           statuses=statuses,
                           status_counts=status_counts,
                           all_resources=all_resources)
