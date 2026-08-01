"""System audit, messaging, and reporting models."""
from datetime import datetime
from app.extensions import db


class Notification(db.Model):
    """
    In-app notifications for users regarding bookings, approvals, and platform alerts.
    """
    __tablename__ = 'notifications'

    id = db.Column(db.Integer, primary_key=True)
    college_id = db.Column(db.Integer, db.ForeignKey('colleges.id'), nullable=True, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    title = db.Column(db.String(150), nullable=False)
    message = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(30), default='info')
    # Categories: 'info', 'success', 'warning', 'danger'
    link_url = db.Column(db.String(250), nullable=True)
    is_read = db.Column(db.Boolean, default=False, nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    user = db.relationship('User', back_populates='notifications')

    @classmethod
    def create_notification(cls, user_id, title, message, college_id=None, category='info', link_url=None):
        """Helper method to construct and append a notification to session."""
        notif = cls(
            user_id=user_id,
            college_id=college_id,
            title=title,
            message=message,
            category=category,
            link_url=link_url
        )
        db.session.add(notif)
        return notif

    def __repr__(self):
        return f"<Notification {self.id} for User:{self.user_id} ({'Read' if self.is_read else 'Unread'})>"


class Report(db.Model):
    """
    Generated reports (utilization, department activities, booking summaries) for college audit.
    """
    __tablename__ = 'reports'

    id = db.Column(db.Integer, primary_key=True)
    college_id = db.Column(db.Integer, db.ForeignKey('colleges.id'), nullable=False, index=True)
    title = db.Column(db.String(180), nullable=False)
    report_type = db.Column(db.String(50), nullable=False, index=True)
    # Types: 'utilization', 'bookings_summary', 'department_activity'
    period_start = db.Column(db.Date, nullable=True)
    period_end = db.Column(db.Date, nullable=True)
    summary_json = db.Column(db.Text, nullable=True) # JSON stored summary statistics
    generated_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    college = db.relationship('College', back_populates='reports')
    generated_by = db.relationship('User')

    def __repr__(self):
        return f"<Report {self.id} [{self.report_type}] College:{self.college_id}>"


class ActivityLog(db.Model):
    """
    Audit log tracking critical actions, user sign-ins, and data modifications.
    """
    __tablename__ = 'activity_logs'

    id = db.Column(db.Integer, primary_key=True)
    college_id = db.Column(db.Integer, db.ForeignKey('colleges.id'), nullable=True, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    action = db.Column(db.String(100), nullable=False)
    entity_type = db.Column(db.String(60), nullable=True) # e.g. 'Booking', 'College', 'Resource'
    entity_id = db.Column(db.Integer, nullable=True)
    ip_address = db.Column(db.String(45), nullable=True)
    details = db.Column(db.Text, nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    college = db.relationship('College', back_populates='activity_logs')
    user = db.relationship('User', back_populates='activity_logs')

    @classmethod
    def log(cls, action, user_id=None, college_id=None, entity_type=None, entity_id=None, details=None, ip_address=None):
        """Helper function to record an activity in the database."""
        entry = cls(
            action=action,
            user_id=user_id,
            college_id=college_id,
            entity_type=entity_type,
            entity_id=entity_id,
            details=details,
            ip_address=ip_address
        )
        db.session.add(entry)
        return entry

    def __repr__(self):
        return f"<ActivityLog {self.action} User:{self.user_id} at {self.timestamp}>"
