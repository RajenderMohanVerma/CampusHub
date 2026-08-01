"""Flask-WTF form classes for secure Authentication and User Registration."""
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField, IntegerField
from wtforms.validators import DataRequired, Email, Length, EqualTo, Optional


class LoginForm(FlaskForm):
    """Standard Password Login Form."""
    email = StringField('Email Address', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=4, message="Password must be at least 4 characters.")])
    remember = BooleanField('Remember me on this device')
    submit = SubmitField('Sign In')


class OTPRequestForm(FlaskForm):
    """Form to trigger Email OTP sent to user."""
    email = StringField('Registered Email Address', validators=[DataRequired(), Email()])
    submit = SubmitField('Send One-Time OTP')


class OTPVerifyForm(FlaskForm):
    """Form to enter and validate the 6-digit numeric OTP."""
    otp_code = StringField('6-Digit Verification Code', validators=[DataRequired(), Length(min=6, max=6, message="OTP must be exactly 6 digits.")])
    submit = SubmitField('Verify & Sign In')


class UserRegistrationForm(FlaskForm):
    """Student and Faculty onboarding registration form."""
    first_name = StringField('First Name', validators=[DataRequired(), Length(min=2, max=60)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(min=2, max=60)])
    email = StringField('Academic Email', validators=[DataRequired(), Email()])
    phone = StringField('Contact Number', validators=[DataRequired(), Length(min=10, max=15)])
    
    role = SelectField('Registering As', choices=[
        ('student', 'Student'),
        ('faculty', 'Faculty Member')
    ], validators=[DataRequired()])
    
    college_id = SelectField('Institution / College', coerce=int, validators=[DataRequired(message="Select your registered university.")])
    department_id = SelectField('Department', coerce=int, validators=[Optional()])
    
    # Academic specific identifiers
    identifier_number = StringField('Enrollment / Faculty ID', validators=[DataRequired(), Length(min=4, max=50)])
    course_or_designation = StringField('Course Name / Academic Designation', validators=[DataRequired()])
    
    password = PasswordField('Create Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password', message='Passwords must match!')])
    
    submit = SubmitField('Create CampusHub Account')
