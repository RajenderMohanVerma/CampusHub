"""Flask-WTF forms for College Onboarding and Contact Support."""
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Email, Length, URL, Optional


class CollegeRegistrationForm(FlaskForm):
    """University & College Workspace Onboarding Application Form."""
    name = StringField('Institution Name', validators=[DataRequired(), Length(min=5, max=150, message="Enter full registered university name.")])
    code = StringField('College Code (Abbreviation)', validators=[DataRequired(), Length(min=2, max=15, message="E.g., IITD, STAN, MIT")])
    email = StringField('Official Registrar / Admin Email', validators=[DataRequired(), Email()])
    phone = StringField('Official Contact Phone', validators=[DataRequired(), Length(min=8, max=30)])
    address = TextAreaField('Campus Physical Address', validators=[DataRequired(), Length(min=10, max=300)])
    website = StringField('Official Website URL', validators=[Optional(), Length(max=200)])
    
    # Designated College Admin Details
    admin_first_name = StringField('Admin First Name', validators=[DataRequired(), Length(min=2, max=50)])
    admin_last_name = StringField('Admin Last Name', validators=[DataRequired(), Length(min=2, max=50)])
    admin_email = StringField('Admin Account Email (will be used for login)', validators=[DataRequired(), Email()])
    
    submit = SubmitField('Submit Registration for Approval')


class ContactForm(FlaskForm):
    """Public Contact and Support Form."""
    full_name = StringField('Your Name', validators=[DataRequired(), Length(min=2, max=80)])
    email = StringField('Email Address', validators=[DataRequired(), Email()])
    subject = StringField('Subject / Inquiry Type', validators=[DataRequired(), Length(min=5, max=150)])
    message = TextAreaField('Your Message', validators=[DataRequired(), Length(min=15, max=1000)])
    submit = SubmitField('Send Message to Support HQ')
