"""Utility functions, security helpers, and RBAC decorators for CampusHub."""
from functools import wraps
from flask import flash, redirect, url_for, request, abort, render_template
from flask_login import current_user
import random
import string
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo


def role_required(*roles):
    """Decorator to enforce role-based authorization for route access."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash("Please sign in to continue.", "warning")
                return redirect(url_for('auth.login', next=request.url))
            
            if current_user.role not in roles and current_user.role != 'platform_admin':
                # Platform admins have superuser privileges; otherwise check role
                if current_user.role not in roles:
                    flash("You do not have sufficient permissions to access this workspace.", "danger")
                    return redirect(url_for_default_dashboard())
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def tenant_required(f):
    """
    Decorator to verify that the authenticated user belongs to an active college workspace.
    Platform admins are exempt from college_id requirement.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
            
        if current_user.role == 'platform_admin':
            return f(*args, **kwargs)
            
        if not current_user.college_id or not current_user.college:
            flash("Your account is not linked to any registered college workspace.", "danger")
            return redirect(url_for('auth.login'))
            
        if current_user.college.status != 'active':
            flash(f"Your college workspace is currently [{current_user.college.status.upper()}]. Contact Platform Support.", "warning")
            return redirect(url_for('main.landing'))
            
        return f(*args, **kwargs)
    return decorated_function


def url_for_default_dashboard():
    """Returns the correct dashboard routing destination based on user role."""
    if not current_user.is_authenticated:
        return url_for('auth.login')
    role = current_user.role
    if role == 'platform_admin':
        return url_for('platform_admin.dashboard')
    elif role == 'college_admin':
        return url_for('college_admin.dashboard')
    elif role == 'faculty':
        return url_for('faculty.dashboard')
    elif role == 'student':
        return url_for('student.dashboard')
    return url_for('main.landing')


def generate_otp(length=6):
    """Generates a numeric One-Time Password for email authentication."""
    return ''.join(random.choices(string.digits, k=length))


def format_timestamp(dt):
    """Jinja filters for elegant date/time representation."""
    if not dt:
        return ""
    # Convert naive datetimes (assumed UTC) to India Standard Time for display
    try:
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=ZoneInfo('UTC'))
        ist = dt.astimezone(ZoneInfo('Asia/Kolkata'))
        return ist.strftime('%b %d, %Y • %I:%M %p')
    except Exception:
        # Fallback to naive formatting
        return dt.strftime('%b %d, %Y • %I:%M %p')


def format_date(dt):
    """Jinja filters for date representation."""
    if not dt:
        return ""
    try:
        if hasattr(dt, 'tzinfo') and dt.tzinfo is not None:
            # Convert to IST and format date portion
            ist = dt.astimezone(ZoneInfo('Asia/Kolkata'))
            return ist.strftime('%B %d, %Y')
        # If dt is date or naive datetime, just format date
        return dt.strftime('%B %d, %Y')
    except Exception:
        return dt.strftime('%B %d, %Y')
