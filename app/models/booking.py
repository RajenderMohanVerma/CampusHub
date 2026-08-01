"""Booking model and time-slot collision validation logic."""
from datetime import datetime, time
from app.extensions import db


class Booking(db.Model):
    """
    Resource booking entity tracking time-slots, user requests, and administrative approval state.
    Strictly isolated per college_id.
    """
    __tablename__ = 'bookings'

    id = db.Column(db.Integer, primary_key=True)
    college_id = db.Column(db.Integer, db.ForeignKey('colleges.id'), nullable=False, index=True)
    resource_id = db.Column(db.Integer, db.ForeignKey('resources.id'), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=True)
    
    purpose = db.Column(db.String(255), nullable=False)
    booking_date = db.Column(db.Date, nullable=False, index=True)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    
    status = db.Column(db.String(20), default='pending', index=True)
    # Status values: 'pending', 'approved', 'rejected', 'cancelled'
    
    admin_remark = db.Column(db.Text, nullable=True)
    approved_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    college = db.relationship('College', back_populates='bookings')
    resource = db.relationship('Resource', back_populates='bookings')
    user = db.relationship('User', back_populates='bookings', foreign_keys=[user_id])
    approved_by = db.relationship('User', foreign_keys=[approved_by_id])

    @classmethod
    def check_collision(cls, college_id, resource_id, booking_date, start_time, end_time, exclude_booking_id=None):
        """
        Checks if a requested booking slot overlaps with any existing approved or pending booking.
        Returns the conflicting Booking object if an overlap exists, otherwise None.
        """
        query = cls.query.filter(
            cls.college_id == college_id,
            cls.resource_id == resource_id,
            cls.booking_date == booking_date,
            cls.status.in_(['approved', 'pending'])
        )
        if exclude_booking_id:
            query = query.filter(cls.id != exclude_booking_id)
            
        existing_bookings = query.all()
        for b in existing_bookings:
            # Overlap happens when (start1 < end2) AND (end1 > start2)
            if start_time < b.end_time and end_time > b.start_time:
                return b
        return None

    @property
    def status_badge(self):
        """Returns bootstrap badge styling based on booking state."""
        badges = {
            'pending': 'bg-warning text-dark',
            'approved': 'bg-success',
            'rejected': 'bg-danger',
            'cancelled': 'bg-secondary'
        }
        return badges.get(self.status, 'bg-secondary')

    @property
    def duration_hours(self):
        """Calculates duration in decimal hours."""
        if not self.start_time or not self.end_time:
            return 0
        start_dt = datetime.combine(self.booking_date, self.start_time)
        end_dt = datetime.combine(self.booking_date, self.end_time)
        diff = (end_dt - start_dt).total_seconds() / 3600.0
        return round(diff, 1)

    def __repr__(self):
        return f"<Booking {self.id} Resource:{self.resource_id} [{self.booking_date} {self.start_time}-{self.end_time}] ({self.status})>"
