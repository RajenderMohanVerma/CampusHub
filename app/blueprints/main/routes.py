"""Main Controller for Public SaaS Landing Page, Features, About, Support, and College Onboarding."""
from flask import render_template, redirect, url_for, flash, request
from flask_login import current_user
from app.extensions import db
from app.blueprints.main import main_bp
from app.forms.main import CollegeRegistrationForm, ContactForm
from app.models import College, User, CollegeAdmin, Notification, ActivityLog


@main_bp.route('/')
def landing():
    """High-conversion modern SaaS landing page."""
    if current_user.is_authenticated:
        # We still let them view landing page if desired, or show quick actions
        pass
    active_colleges_count = College.query.filter_by(status='active').count()
    return render_template('main/landing.html', active_colleges_count=active_colleges_count)


@main_bp.route('/features')
def features():
    """Detailed feature review and system capabilities page."""
    return render_template('main/features.html')


@main_bp.route('/about')
def about():
    """About Platform architecture and enterprise tenancy security."""
    return render_template('main/about.html')


@main_bp.route('/contact', methods=['GET', 'POST'])
def contact():
    """Customer Support desk and inquiries interface."""
    form = ContactForm()
    if form.validate_on_submit():
        ActivityLog.log(
            action="SUPPORT_INQUIRY",
            details=f"Contact msg from {form.full_name.data} ({form.email.data}): {form.subject.data}"
        )
        db.session.commit()
        flash("Thank you! Your message has been received by CampusHub Support HQ. A technician will reply within 24 hours.", "success")
        return redirect(url_for('main.contact'))
    return render_template('main/contact.html', form=form)


@main_bp.route('/register-college', methods=['GET', 'POST'])
def register_college():
    """
    University registration gateway.
    Creates a pending college workspace and college admin account waiting for Platform Superadmin approval.
    """
    form = CollegeRegistrationForm()
    if form.validate_on_submit():
        code_upper = form.code.data.strip().upper()
        existing_code = College.query.filter_by(code=code_upper).first()
        existing_name = College.query.filter_by(name=form.name.data.strip()).first()
        
        if existing_code or existing_name:
            flash("An institution with this code or registered name already exists in CampusHub.", "danger")
            return render_template('main/register_college.html', form=form)
            
        existing_admin = User.query.filter_by(email=form.admin_email.data.strip().lower()).first()
        if existing_admin:
            flash("The provided Admin Email is already associated with an active user account.", "warning")
            return render_template('main/register_college.html', form=form)
            
        # Create pending College workspace
        new_college = College(
            name=form.name.data.strip(),
            code=code_upper,
            email=form.email.data.strip().lower(),
            phone=form.phone.data.strip(),
            address=form.address.data.strip(),
            website=form.website.data.strip() if form.website.data else None,
            status='pending',
            logo_url=f"https://ui-avatars.com/api/?name={code_upper}&background=6366f1&color=fff&size=200"
        )
        db.session.add(new_college)
        db.session.flush()
        new_college.college_id = new_college.id # Set self-referential tenant column
        
        # Create College Admin account (inactive / pending approval)
        ca_user = User(
            email=form.admin_email.data.strip().lower(),
            first_name=form.admin_first_name.data.strip(),
            last_name=form.admin_last_name.data.strip(),
            phone=form.phone.data.strip(),
            role='college_admin',
            college_id=new_college.id,
            is_active=True # Will be blocked by tenant_required until college status == active
        )
        # Set default initial temporary password
        ca_user.set_password("admin123")
        db.session.add(ca_user)
        db.session.flush()
        
        ca_profile = CollegeAdmin(user_id=ca_user.id, college_id=new_college.id, designation='Founding Registrar')
        db.session.add(ca_profile)
        
        # Alert all Platform Admins about the pending application
        platform_admins = User.query.filter_by(role='platform_admin').all()
        for p in platform_admins:
            Notification.create_notification(
                user_id=p.id,
                title="New College Registration",
                message=f"{new_college.name} ({new_college.code}) has applied for workspace activation.",
                category="warning",
                link_url="/platform/colleges"
            )
            
        ActivityLog.log("COLLEGE_APPLIED", entity_type="College", entity_id=new_college.id, details=f"New institution applied: {new_college.name}")
        db.session.commit()
        
        flash(f"Application for '{new_college.name}' submitted! Status: [PENDING APPROVAL]. Our Platform Superadmin will review your credentials shortly. Default admin login: admin123", "success")
        return redirect(url_for('auth.login'))
        
    return render_template('main/register_college.html', form=form)
