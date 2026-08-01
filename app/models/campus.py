"""Campus, Department, and Resource database models."""
from datetime import datetime
from app.extensions import db


class College(db.Model):
    """
    Registered College / University institution model.
    Serves as the multi-tenant isolation root for all associated campus data.
    """
    __tablename__ = 'colleges'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), unique=True, nullable=False, index=True)
    code = db.Column(db.String(20), unique=True, nullable=False, index=True)
    email = db.Column(db.String(150), nullable=False)
    phone = db.Column(db.String(30), nullable=False)
    address = db.Column(db.Text, nullable=True)
    website = db.Column(db.String(200), nullable=True)
    logo_url = db.Column(db.String(300), default='https://ui-avatars.com/api/?name=College&background=6366f1&color=fff')
    status = db.Column(db.String(20), default='pending', index=True) 
    # Statuses: 'pending', 'active', 'suspended', 'rejected'
    
    # Self-referential college_id column to strictly honor the system tenant schema rule
    college_id = db.Column(db.Integer, db.ForeignKey('colleges.id'), nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    users = db.relationship('User', back_populates='college', foreign_keys='User.college_id', lazy='dynamic')
    departments = db.relationship('Department', back_populates='college', cascade='all, delete-orphan', lazy='dynamic')
    resources = db.relationship('Resource', back_populates='college', cascade='all, delete-orphan', lazy='dynamic')
    bookings = db.relationship('Booking', back_populates='college', cascade='all, delete-orphan', lazy='dynamic')
    reports = db.relationship('Report', back_populates='college', cascade='all, delete-orphan', lazy='dynamic')
    activity_logs = db.relationship('ActivityLog', back_populates='college', lazy='dynamic')

    def __init__(self, **kwargs):
        super(College, self).__init__(**kwargs)
        if self.id and not self.college_id:
            self.college_id = self.id

    def __repr__(self):
        return f"<College {self.code} - {self.name} ({self.status})>"


class Department(db.Model):
    """Academic or administrative department inside a college."""
    __tablename__ = 'departments'

    id = db.Column(db.Integer, primary_key=True)
    college_id = db.Column(db.Integer, db.ForeignKey('colleges.id'), nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(20), nullable=False)
    head_name = db.Column(db.String(100), nullable=True)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    college = db.relationship('College', back_populates='departments')
    bookings = db.relationship('Booking', backref='department', lazy='dynamic')

    def __repr__(self):
        return f"<Department {self.code} [{self.college_id}]>"


class Resource(db.Model):
    """
    Campus shared resource (Lab, Seminar Hall, Classroom, Equipment, etc.).
    """
    __tablename__ = 'resources'

    id = db.Column(db.Integer, primary_key=True)
    college_id = db.Column(db.Integer, db.ForeignKey('colleges.id'), nullable=False, index=True)
    name = db.Column(db.String(150), nullable=False)
    resource_type = db.Column(db.String(50), nullable=False, index=True) 
    # Types: 'Computer Lab', 'Classroom', 'Seminar Hall', 'Conference Room', 'Projector', 'Equipment'
    capacity = db.Column(db.Integer, default=0, nullable=False)
    location = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=True)
    image_url = db.Column(
        db.String(350), 
        default='https://images.unsplash.com/photo-1517646287270-a5a9ca602e5c?auto=format&fit=crop&w=800&q=80'
    )
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    college = db.relationship('College', back_populates='resources')
    bookings = db.relationship('Booking', back_populates='resource', cascade='all, delete-orphan', lazy='dynamic')

    @property
    def type_icon(self):
        """Returns Bootstrap Icon class according to resource type."""
        icons = {
            'Computer Lab': 'bi-pc-display',
            'Classroom': 'bi-easel',
            'Seminar Hall': 'bi-building',
            'Conference Room': 'bi-people',
            'Projector': 'bi-projector',
            'Equipment': 'bi-tools'
        }
        return icons.get(self.resource_type, 'bi-box')

    @property
    def badge_color(self):
        """Returns modern color theme for resource badge."""
        colors = {
            'Computer Lab': 'primary',
            'Classroom': 'info',
            'Seminar Hall': 'success',
            'Conference Room': 'warning',
            'Projector': 'danger',
            'Equipment': 'secondary'
        }
        return colors.get(self.resource_type, 'primary')

    def __repr__(self):
        return f"<Resource {self.name} ({self.resource_type}) College:{self.college_id}>"
