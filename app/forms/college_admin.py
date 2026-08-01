"""Flask-WTF forms for College Admin CRUD operations over departments, resources, faculty, and students."""
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, IntegerField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, Length, Optional, NumberRange


class DepartmentForm(FlaskForm):
    """Department creation and modification form."""
    name = StringField('Department Full Name', validators=[DataRequired(), Length(min=2, max=100)])
    code = StringField('Abbreviated Code (e.g., CSE, ECE)', validators=[DataRequired(), Length(min=2, max=15)])
    head_name = StringField('Department Head / HOD Name', validators=[Optional(), Length(max=100)])
    description = TextAreaField('Overview & Scope', validators=[Optional(), Length(max=300)])
    submit = SubmitField('Save Department')


class ResourceForm(FlaskForm):
    """Campus resource allocation and configuration form."""
    name = StringField('Resource Name (e.g. Advanced AI GPU Lab)', validators=[DataRequired(), Length(min=3, max=150)])
    resource_type = SelectField('Resource Classification', choices=[
        ('Computer Lab', 'Computer Lab'),
        ('Classroom', 'Lecture Classroom'),
        ('Seminar Hall', 'Seminar Hall'),
        ('Conference Room', 'Conference Room'),
        ('Projector', 'Portable Projector'),
        ('Equipment', 'Specialized Equipment')
    ], validators=[DataRequired()])
    capacity = IntegerField('Seating / Workstation Capacity', validators=[DataRequired(), NumberRange(min=1, max=1000)])
    location = StringField('Campus Location (Block, Floor, Room)', validators=[DataRequired(), Length(min=4, max=120)])
    description = TextAreaField('Hardware Specs & Facilities Description', validators=[Optional(), Length(max=500)])
    image_url = StringField('High-Res Photo URL (Optional Unsplash Link)', validators=[Optional(), Length(max=350)])
    is_active = BooleanField('Available For Direct Booking Requests', default=True)
    submit = SubmitField('Deploy Campus Asset')


class MemberAddForm(FlaskForm):
    """Form to onboard a new Student or Faculty inside the college workspace."""
    first_name = StringField('First Name', validators=[DataRequired(), Length(min=2, max=60)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(min=2, max=60)])
    email = StringField('Academic Email Address', validators=[DataRequired(), Email()])
    phone = StringField('Contact Telephone', validators=[DataRequired(), Length(min=8, max=25)])
    department_id = SelectField('Department Alignment', coerce=int, validators=[DataRequired()])
    identifier = StringField('Enrollment Number / Employee Staff ID', validators=[DataRequired(), Length(min=3, max=60)])
    extra_field = StringField('Course Program / Designation', validators=[DataRequired(), Length(min=2, max=100)])
    submit = SubmitField('Register Member to Workspace')


class BookingApprovalForm(FlaskForm):
    """Form to record administrative feedback note when approving or rejecting."""
    admin_remark = TextAreaField('Administrative Feedback Note / Instructions', validators=[Optional(), Length(max=250)])
    submit = SubmitField('Submit Decision')
