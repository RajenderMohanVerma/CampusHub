"""Flask-WTF forms for Faculty profile maintenance."""
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, Length, Optional


class FacultyProfileForm(FlaskForm):
    """Faculty profile updating form."""
    phone = StringField('Contact Telephone / Lab Ext', validators=[DataRequired(), Length(min=8, max=25)])
    designation = StringField('Academic Designation (e.g., Professor of AI)', validators=[DataRequired(), Length(min=2, max=100)])
    specialization = StringField('Research Specialization', validators=[Optional(), Length(max=120)])
    submit = SubmitField('Update Faculty Metadata')
