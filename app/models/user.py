"""User authentication and role profile models."""
from datetime import datetime
from flask_login import UserMixin
from app.extensions import db, bcrypt


class User(db.Model, UserMixin):
    """
    Central User authentication entity.
    Stores core login credentials, role assignments, and college association.
    """
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(128), nullable=False)
    first_name = db.Column(db.String(64), nullable=False)
    last_name = db.Column(db.String(64), nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    role = db.Column(db.String(32), nullable=False, index=True) 
    # Roles: 'platform_admin', 'college_admin', 'faculty', 'student'
    
    # Tenancy association (Nullable ONLY for platform_admin)
    college_id = db.Column(db.Integer, db.ForeignKey('colleges.id'), nullable=True, index=True)
    
    # OTP & OAuth attributes
    otp_code = db.Column(db.String(10), nullable=True)
    otp_expiry = db.Column(db.DateTime, nullable=True)
    google_id = db.Column(db.String(128), unique=True, nullable=True)
    
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships to profiles and tenant
    college = db.relationship('College', back_populates='users', foreign_keys=[college_id])
    platform_admin_profile = db.relationship('PlatformAdmin', back_populates='user', uselist=False, cascade='all, delete-orphan')
    college_admin_profile = db.relationship('CollegeAdmin', back_populates='user', uselist=False, cascade='all, delete-orphan')
    faculty_profile = db.relationship('Faculty', back_populates='user', uselist=False, cascade='all, delete-orphan')
    student_profile = db.relationship('Student', back_populates='user', uselist=False, cascade='all, delete-orphan')
    
    bookings = db.relationship('Booking', back_populates='user', foreign_keys='Booking.user_id', lazy='dynamic')
    notifications = db.relationship('Notification', back_populates='user', lazy='dynamic', cascade='all, delete-orphan')
    activity_logs = db.relationship('ActivityLog', back_populates='user', lazy='dynamic')

    def set_password(self, password):
        """Hashes and sets the password."""
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        """Verifies plaintext password against stored hash."""
        return bcrypt.check_password_hash(self.password_hash, password)

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def __repr__(self):
        return f"<User {self.email} [{self.role}] College:{self.college_id}>"


class PlatformAdmin(db.Model):
    """
    Platform superuser model.
    Note: As per database rules, PlatformAdmin is the ONLY table without college_id.
    """
    __tablename__ = 'platform_admin'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    permissions_level = db.Column(db.String(64), default='superadmin')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', back_populates='platform_admin_profile')


class CollegeAdmin(db.Model):
    """College administrator profile with workspace administration scope."""
    __tablename__ = 'college_admin'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    college_id = db.Column(db.Integer, db.ForeignKey('colleges.id'), nullable=False, index=True)
    designation = db.Column(db.String(100), default='Campus Administrator')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', back_populates='college_admin_profile')
    college = db.relationship('College', backref='college_admins')


class Faculty(db.Model):
    """Faculty member profile tied to a specific department and college."""
    __tablename__ = 'faculty'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    college_id = db.Column(db.Integer, db.ForeignKey('colleges.id'), nullable=False, index=True)
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=True)
    employee_id = db.Column(db.String(50), nullable=False, index=True)
    designation = db.Column(db.String(100), default='Assistant Professor')
    specialization = db.Column(db.String(200), nullable=True)
    office_location = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', back_populates='faculty_profile')
    college = db.relationship('College', backref='faculty_members')
    department = db.relationship('Department', backref='faculty_members')


class Student(db.Model):
    """Student academic profile tied to college and department."""
    __tablename__ = 'students'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    college_id = db.Column(db.Integer, db.ForeignKey('colleges.id'), nullable=False, index=True)
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=True)
    enrollment_number = db.Column(db.String(64), nullable=False, index=True)
    course_name = db.Column(db.String(100), default='MCA / B.Tech / B.Sc')
    semester = db.Column(db.Integer, default=1)
    academic_year = db.Column(db.String(20), default='2025-2026')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', back_populates='student_profile')
    college = db.relationship('College', backref='students')
    department = db.relationship('Department', backref='students')
