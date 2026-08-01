"""Platform Admin Controller handling university approval workflows and systemic monitoring."""
from datetime import datetime, timedelta
from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.extensions import db
from app.blueprints.platform_admin import platform_admin_bp
from app.utils import role_required
from app.models import College, User, Resource, Booking, Notification, ActivityLog, Report


@platform_admin_bp.route('/dashboard')
@login_required
@role_required('platform_admin')
def dashboard():
    """HQ Executive Control Dashboard for Platform Superadmins."""
    total_colleges = College.query.count()
    active_colleges = College.query.filter_by(status='active').count()
    pending_colleges = College.query.filter_by(status='pending').count()
    suspended_colleges = College.query.filter_by(status='suspended').count()
    
    total_resources = Resource.query.count()
    total_bookings = Booking.query.count()
    total_users = User.query.filter(User.role != 'platform_admin').count()
    
    # Recent pending applications
    pending_list = College.query.filter_by(status='pending').order_by(College.created_at.desc()).all()
    
    # Recent systemic audit logs
    recent_logs = ActivityLog.query.order_by(ActivityLog.timestamp.desc()).limit(10).all()
    
    return render_template('platform_admin/dashboard.html',
                           total_colleges=total_colleges,
                           active_colleges=active_colleges,
                           pending_colleges=pending_colleges,
                           suspended_colleges=suspended_colleges,
                           total_resources=total_resources,
                           total_bookings=total_bookings,
                           total_users=total_users,
                           pending_list=pending_list,
                           recent_logs=recent_logs)


@platform_admin_bp.route('/colleges')
@login_required
@role_required('platform_admin')
def colleges():
    """List and govern all registered campus institutions."""
    status_filter = request.args.get('status', 'all')
    if status_filter in ['active', 'pending', 'suspended', 'rejected']:
        colleges_list = College.query.filter_by(status=status_filter).order_by(College.name.asc()).all()
    else:
        colleges_list = College.query.order_by(College.created_at.desc()).all()
        
    return render_template('platform_admin/colleges.html', colleges_list=colleges_list, status_filter=status_filter)


@platform_admin_bp.route('/college/<int:college_id>/approve', methods=['POST'])
@login_required
@role_required('platform_admin')
def approve_college(college_id):
    """Activates a college workspace and authorizes its admin account."""
    college = College.query.get_or_404(college_id)
    college.status = 'active'
    
    # Ensure college admin users inside this tenant become active
    admin_users = User.query.filter_by(college_id=college.id, role='college_admin').all()
    for au in admin_users:
        au.is_active = True
        Notification.create_notification(
            user_id=au.id,
            college_id=college.id,
            title="Workspace Activated!",
            message=f"Your application for '{college.name}' has been approved by Platform HQ. You can now manage campus resources.",
            category="success",
            link_url="/admin/dashboard"
        )
        
    ActivityLog.log("COLLEGE_APPROVED", user_id=current_user.id, entity_type="College", entity_id=college.id, details=f"Approved college: {college.name} ({college.code})")
    db.session.commit()
    
    flash(f"Institution '{college.name}' ({college.code}) is now [ACTIVE]! College admin credentials unlocked.", "success")
    return redirect(request.referrer or url_for('platform_admin.colleges'))


@platform_admin_bp.route('/college/<int:college_id>/reject', methods=['POST'])
@login_required
@role_required('platform_admin')
def reject_college(college_id):
    """Rejects a pending college application."""
    college = College.query.get_or_404(college_id)
    college.status = 'rejected'
    
    ActivityLog.log("COLLEGE_REJECTED", user_id=current_user.id, entity_type="College", entity_id=college.id, details=f"Rejected college application: {college.name}")
    db.session.commit()
    
    flash(f"Institution application for '{college.name}' has been rejected.", "warning")
    return redirect(request.referrer or url_for('platform_admin.colleges'))


@platform_admin_bp.route('/college/<int:college_id>/suspend', methods=['POST'])
@login_required
@role_required('platform_admin')
def suspend_college(college_id):
    """Suspends an active university workspace (freezes student/faculty actions)."""
    college = College.query.get_or_404(college_id)
    college.status = 'suspended'
    
    ActivityLog.log("COLLEGE_SUSPENDED", user_id=current_user.id, entity_type="College", entity_id=college.id, details=f"Suspended workspace: {college.name}")
    db.session.commit()
    
    flash(f"Workspace '{college.name}' has been SUSPENDED. All user sessions inside this college are now frozen.", "danger")
    return redirect(request.referrer or url_for('platform_admin.colleges'))


@platform_admin_bp.route('/college/<int:college_id>/view')
@login_required
@role_required('platform_admin')
def view_college(college_id):
    """Detailed inspection of a college's resource usage, faculty, and departments."""
    college = College.query.get_or_404(college_id)
    dept_count = college.departments.count()
    res_count = college.resources.count()
    booking_count = college.bookings.count()
    faculty_count = User.query.filter_by(college_id=college.id, role='faculty').count()
    student_count = User.query.filter_by(college_id=college.id, role='student').count()
    
    recent_bookings = college.bookings.order_by(Booking.created_at.desc()).limit(10).all()
    
    return render_template('platform_admin/view_college.html',
                           college=college,
                           dept_count=dept_count,
                           res_count=res_count,
                           booking_count=booking_count,
                           faculty_count=faculty_count,
                           student_count=student_count,
                           recent_bookings=recent_bookings)


@platform_admin_bp.route('/reports')
@login_required
@role_required('platform_admin')
def reports():
    """System-wide analytical overview and Chart.js datasets across all universities."""
    active_colleges = College.query.filter_by(status='active').all()
    labels = [c.code for c in active_colleges]
    res_counts = [c.resources.count() for c in active_colleges]
    book_counts = [c.bookings.count() for c in active_colleges]
    
    return render_template('platform_admin/reports.html',
                           active_colleges=active_colleges,
                           labels=labels,
                           res_counts=res_counts,
                           book_counts=book_counts)


@platform_admin_bp.route('/audit-logs')
@login_required
@role_required('platform_admin')
def audit_logs():
    """Systemic audit log inspection across all tenants."""
    logs = ActivityLog.query.order_by(ActivityLog.timestamp.desc()).limit(200).all()
    return render_template('platform_admin/audit_logs.html', logs=logs)
