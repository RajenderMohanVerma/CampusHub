"""Forms initialization and exports for CampusHub platform."""
from app.forms.auth import LoginForm, OTPRequestForm, OTPVerifyForm, UserRegistrationForm

__all__ = [
    'LoginForm',
    'OTPRequestForm',
    'OTPVerifyForm',
    'UserRegistrationForm'
]
