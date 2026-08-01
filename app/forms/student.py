"""Flask-WTF forms for Student Resource Bookings and Profile maintenance."""
from datetime import date, datetime
from flask_wtf import FlaskForm
from wtforms import DateField, TimeField, TextAreaField, StringField, SubmitField
from wtforms.validators import DataRequired, Length, ValidationError


class BookingRequestForm(FlaskForm):
    """Resource booking application form with automated collision validation."""
    booking_date = DateField('Target Date of Reservation', validators=[DataRequired()], format='%Y-%m-%d', default=date.today)
    start_time = TimeField('Start Time (HH:MM 24hr)', validators=[DataRequired()], format='%H:%M')
    end_time = TimeField('End Time (HH:MM 24hr)', validators=[DataRequired()], format='%H:%M')
    purpose = TextAreaField('Academic Purpose & Objectives', validators=[DataRequired(), Length(min=10, max=250, message="Please describe why this asset is required.")])
    submit = SubmitField('Request Slot Authorization')

    def validate_booking_date(self, field):
        """Prevent scheduling in past temporal intervals."""
        if field.data < date.today():
            raise ValidationError("You cannot request reservation slots for past dates.")

    def validate_end_time(self, field):
        """Ensure start time strictly precedes end time."""
        if hasattr(self, 'start_time') and self.start_time.data and field.data:
            if field.data <= self.start_time.data:
                raise ValidationError("End time must fall after the requested start time.")
            # Calculate duration in minutes
            dt_start = datetime.combine(date.today(), self.start_time.data)
            dt_end = datetime.combine(date.today(), field.data)
            duration_minutes = (dt_end - dt_start).total_seconds() / 60.0
            if duration_minutes < 15:
                raise ValidationError("Minimum booking slot duration is 15 minutes.")
            if duration_minutes > 480:
                raise ValidationError("Single booking duration cannot exceed 8 continuous hours.")


class StudentProfileForm(FlaskForm):
    """Student profile updates."""
    phone = StringField('Contact Mobile', validators=[DataRequired(), Length(min=8, max=25)])
    course_name = StringField('Enrolled Program / Degree', validators=[DataRequired(), Length(min=2, max=100)])
    submit = SubmitField('Update Profile Metadata')
