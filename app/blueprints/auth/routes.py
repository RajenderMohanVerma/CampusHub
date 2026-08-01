"""Authentication controller handling password login, OTP verification, OAuth simulation, and onboarding."""
from datetime import datetime, timedelta
from flask import render_template, redirect, url_for, flash, request, session, current_app
from flask_login import login_user, logout_user, current_user, login_required
from flask_mail import Message
from app.extensions import db, mail
from app.blueprints.auth import auth_bp
from app.forms.auth import LoginForm, OTPRequestForm, OTPVerifyForm, UserRegistrationForm
from app.models import User, College, Department, Student, Faculty, ActivityLog
from app.utils import url_for_default_dashboard, generate_otp


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Main login interface supporting Password sign-in and OTP triggers."""
    if current_user.is_authenticated:
        return redirect(url_for_default_dashboard())
        
    form = LoginForm()
    otp_form = OTPRequestForm()
    
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.strip().lower()).first()
        if user and user.check_password(form.password.data):
            if not user.is_active:
                flash("Your account has been deactivated. Please reach out to Campus Support.", "danger")
                return render_template('auth/login.html', form=form, otp_form=otp_form)
                
            login_user(user, remember=form.remember.data)
            ActivityLog.log("LOGIN", user_id=user.id, college_id=user.college_id, details="Successful password authentication.")
            db.session.commit()
            
            flash(f"Welcome back, {user.first_name}! Logged in successfully.", "success")
            next_page = request.args.get('next')
            return redirect(next_page or url_for_default_dashboard())
        else:
            flash("Invalid credentials. Please verify your email and password.", "danger")
            
    return render_template('auth/login.html', form=form, otp_form=otp_form)


@auth_bp.route('/request-otp', methods=['POST'])
def request_otp():
    """Generates and dispatches a One-Time Password via email or dev terminal."""
    otp_form = OTPRequestForm()
    if otp_form.validate_on_submit():
        email = otp_form.email.data.strip().lower()
        user = User.query.filter_by(email=email).first()
        if not user or not user.is_active:
            flash("No active account discovered with that email address.", "danger")
            return redirect(url_for('auth.login'))
            
        code = generate_otp(6)
        expiry = datetime.utcnow() + timedelta(minutes=current_app.config.get('OTP_EXPIRY_MINUTES', 10))
        user.otp_code = code
        user.otp_expiry = expiry
        db.session.commit()
        
        session['otp_auth_email'] = user.email
        
        # In simulation mode, print clearly to console and notify user
        if current_app.config.get('SIMULATION_MODE', True) or current_app.debug:
            print(f"\n==============================================")
            print(f"📧 [DEV EMAIL OTP SIMULATOR] For: {user.email}")
            print(f"🔑 ONE-TIME VERIFICATION CODE: >> {code} <<")
            print(f"⏰ Valid until: {expiry.strftime('%H:%M:%S')} UTC")
            print(f"==============================================\n")
            flash(f"[Dev simulation] OTP sent! Your code is {code} (Check console logs).", "info")
        else:
            try:
                msg = Message("Your CampusHub Login Verification Code",
                              recipients=[user.email],
                              body=f"Hello {user.first_name},\n\nYour One-Time Password for CampusHub is: {code}\nThis code expires in 10 minutes.\n\nDo not share this code with anyone.")
                mail.send(msg)
                flash("A verification code has been dispatched to your email address.", "success")
            except Exception as e:
                current_app.logger.error(f"Mail delivery failure: {e}")
                flash(f"[Mail fallback] Could not send via SMTP. Your dev OTP code is: {code}", "warning")
                
        return redirect(url_for('auth.verify_otp'))
    
    flash("Please enter a valid email address.", "warning")
    return redirect(url_for('auth.login'))


@auth_bp.route('/verify-otp', methods=['GET', 'POST'])
def verify_otp():
    """Verifies numeric OTP submitted by the user."""
    email = session.get('otp_auth_email')
    if not email:
        flash("No active OTP session found. Please request a new code.", "warning")
        return redirect(url_for('auth.login'))
        
    form = OTPVerifyForm()
    user = User.query.filter_by(email=email).first()
    
    if form.validate_on_submit():
        if not user or not user.otp_code or not user.otp_expiry:
            flash("Invalid OTP state. Request a fresh code.", "danger")
            return redirect(url_for('auth.login'))
            
        if datetime.utcnow() > user.otp_expiry:
            user.otp_code = None
            db.session.commit()
            flash("Verification code expired! Please generate a new OTP.", "danger")
            return redirect(url_for('auth.login'))
            
        if form.otp_code.data.strip() == user.otp_code:
            # Clear used code and login
            user.otp_code = None
            user.otp_expiry = None
            login_user(user)
            session.pop('otp_auth_email', None)
            
            ActivityLog.log("LOGIN_OTP", user_id=user.id, college_id=user.college_id, details="Verified login via One-Time Password.")
            db.session.commit()
            
            flash(f"OTP Verified! Welcome back, {user.first_name}.", "success")
            return redirect(url_for_default_dashboard())
        else:
            flash("Incorrect verification code. Please check and re-enter.", "danger")
            
    return render_template('auth/verify_otp.html', form=form, email=email)


@auth_bp.route('/google-simulate', methods=['GET', 'POST'])
def google_simulate():
    """
    Enterprise OAuth 2.0 simulation gateway.
    Allows testing seamless Google sign-in workflows without external credentials or SSL certs.
    """
    if current_user.is_authenticated:
        return redirect(url_for_default_dashboard())
        
    # List sample simulated active Google accounts from existing users
    test_users = User.query.filter_by(is_active=True).all()
    
    if request.method == 'POST':
        selected_user_id = request.form.get('user_id', type=int)
        user = User.query.get(selected_user_id)
        if user:
            login_user(user)
            ActivityLog.log("LOGIN_GOOGLE", user_id=user.id, college_id=user.college_id, details="Authenticated via Google OAuth simulator.")
            db.session.commit()
            
            flash(f"Successfully connected via Google OAuth! Welcome, {user.first_name}.", "success")
            return redirect(url_for_default_dashboard())
        else:
            flash("OAuth authorization rejected.", "danger")
            
    return render_template('auth/google_sim.html', users=test_users)


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Public registration interface for Students and Faculty members."""
    if current_user.is_authenticated:
        return redirect(url_for_default_dashboard())
        
    form = UserRegistrationForm()
    # Populate choices from active colleges
    active_colleges = College.query.filter_by(status='active').all()
    form.college_id.choices = [(c.id, f"{c.name} ({c.code})") for c in active_colleges]
    
    # Populate departments for selected or initial college
    all_depts = Department.query.all()
    form.department_id.choices = [(d.id, f"{d.name} ({d.college.code})") for d in all_depts]
    if not form.department_id.choices:
        form.department_id.choices = [(0, 'General / No Specific Dept')]

    if form.validate_on_submit():
        existing_user = User.query.filter_by(email=form.email.data.strip().lower()).first()
        if existing_user:
            flash("That email address is already registered. Try signing in.", "warning")
            return render_template('auth/register.html', form=form)
            
        selected_college_id = form.college_id.data
        role = form.role.data
        dept_id = form.department_id.data if form.department_id.data != 0 else None
        
        # Construct core User record
        new_user = User(
            email=form.email.data.strip().lower(),
            first_name=form.first_name.data.strip(),
            last_name=form.last_name.data.strip(),
            phone=form.phone.data.strip(),
            role=role,
            college_id=selected_college_id,
            is_active=True
        )
        new_user.set_password(form.password.data)
        db.session.add(new_user)
        db.session.flush()
        
        # Construct domain profile based on selected role
        if role == 'student':
            profile = Student(
                user_id=new_user.id,
                college_id=selected_college_id,
                department_id=dept_id,
                enrollment_number=form.identifier_number.data.strip().upper(),
                course_name=form.course_or_designation.data.strip(),
                semester=1
            )
            db.session.add(profile)
        elif role == 'faculty':
            profile = Faculty(
                user_id=new_user.id,
                college_id=selected_college_id,
                department_id=dept_id,
                employee_id=form.identifier_number.data.strip().upper(),
                designation=form.course_or_designation.data.strip(),
                specialization="General Academic Studies"
            )
            db.session.add(profile)
            
        ActivityLog.log("USER_REGISTERED", user_id=new_user.id, college_id=selected_college_id, details=f"Onboarded new {role}: {new_user.email}")
        db.session.commit()
        
        flash("Your CampusHub account has been created successfully! Please sign in below.", "success")
        return redirect(url_for('auth.login'))
        
    return render_template('auth/register.html', form=form)


@auth_bp.route('/logout')
@login_required
def logout():
    """Terminates authenticated user session."""
    ActivityLog.log("LOGOUT", user_id=current_user.id, college_id=current_user.college_id, details="User signed out.")
    db.session.commit()
    logout_user()
    flash("You have securely signed out of your CampusHub workspace.", "info")
    return redirect(url_for('main.landing'))
