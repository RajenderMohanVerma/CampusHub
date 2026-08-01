"""Database Models for CampusHub Platform."""
from app.models.user import User, PlatformAdmin, CollegeAdmin, Faculty, Student
from app.models.campus import College, Department, Resource
from app.models.booking import Booking
from app.models.system import Notification, Report, ActivityLog

__all__ = [
    'User',
    'PlatformAdmin',
    'CollegeAdmin',
    'Faculty',
    'Student',
    'College',
    'Department',
    'Resource',
    'Booking',
    'Notification',
    'Report',
    'ActivityLog'
]
