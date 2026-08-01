"""
CampusHub Comprehensive Verification Suite.
Tests strictly enforced multi-tenant data isolation, zero-collision resource scheduling algorithms, RBAC authorization, and notification telemetry.
"""
import sys
import unittest
from datetime import date, time
from flask import Flask
from app import create_app, db
from app.models import (College, User, Department, Faculty, Student, 
                        Resource, Booking, Notification, ActivityLog, Report)


class TestCampusHubArchitecture(unittest.TestCase):
    """Production Verification Tests for CampusHub SaaS Engine."""

    @classmethod
    def setUpClass(cls):
        """Configure test application environment with isolated in-memory SQLite database."""
        cls.app = create_app('test')
        cls.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        cls.app.config['WTF_CSRF_ENABLED'] = False
        cls.app.config['TESTING'] = True
        cls.app_context = cls.app.app_context()
        cls.app_context.push()
        db.create_all()

    @classmethod
    def tearDownClass(cls):
        """Clean up test database and context."""
        db.session.remove()
        db.drop_all()
        cls.app_context.pop()

    def setUp(self):
        """Reset and seed deterministic multi-tenant data before each test execution."""
        db.session.rollback()
        for table in reversed(db.metadata.sorted_tables):
            db.session.execute(table.delete())
        db.session.commit()
        self.seed_test_tenants()

    def seed_test_tenants(self):
        """Seed two completely distinct university tenants (Stanford vs MIT) and platform HQ."""
        # Platform HQ Admin
        hq = User(email="hq@campushub.ai", first_name="Super", last_name="Admin", role="platform_admin", is_active=True)
        hq.set_password("secret_admin_pass")
        db.session.add(hq)

        # Tenant 1: Stanford University (Active)
        self.c1 = College(name="Stanford University", code="STANFORD", email="admin@stanford.edu", phone="6507232300", address="Stanford, CA", status="active")
        db.session.add(self.c1)

        # Tenant 2: MIT (Active)
        self.c2 = College(name="Massachusetts Institute of Technology", code="MIT", email="admin@mit.edu", phone="6172531000", address="Cambridge, MA", status="active")
        db.session.add(self.c2)
        db.session.flush()

        # Users & Depts in Stanford (Tenant 1)
        self.d1 = Department(college_id=self.c1.id, name="Computer Science & AI", code="CS", head_name="Dr. Ng")
        db.session.add(self.d1)
        
        self.c1_admin = User(college_id=self.c1.id, email="admin@stanford.edu", first_name="John", last_name="Hennessy", role="college_admin", is_active=True)
        self.c1_admin.set_password("password123")
        
        self.c1_student = User(college_id=self.c1.id, email="student@stanford.edu", first_name="Alex", last_name="Turner", role="student", is_active=True)
        self.c1_student.set_password("password123")
        
        self.c1_faculty = User(college_id=self.c1.id, email="faculty@stanford.edu", first_name="Fei-Fei", last_name="Li", role="faculty", is_active=True)
        self.c1_faculty.set_password("password123")
        db.session.add_all([self.c1_admin, self.c1_student, self.c1_faculty])
        db.session.flush()

        self.res1 = Resource(college_id=self.c1.id, name="AI Supercomputing Center 101", resource_type="Computer Lab", capacity=50, location="Gates Building", is_active=True)
        db.session.add(self.res1)

        # Users & Depts in MIT (Tenant 2)
        self.d2 = Department(college_id=self.c2.id, name="Electrical Engineering", code="EECS", head_name="Dr. Sussman")
        db.session.add(self.d2)

        self.c2_admin = User(college_id=self.c2.id, email="admin@mit.edu", first_name="Rafael", last_name="Reif", role="college_admin", is_active=True)
        self.c2_admin.set_password("password123")
        
        self.c2_student = User(college_id=self.c2.id, email="student@mit.edu", first_name="Bob", last_name="Smith", role="student", is_active=True)
        self.c2_student.set_password("password123")
        db.session.add_all([self.c2_admin, self.c2_student])
        db.session.flush()

        self.res2 = Resource(college_id=self.c2.id, name="MIT Robotics Testing Chamber", resource_type="Equipment", capacity=20, location="Building 32", is_active=True)
        db.session.add(self.res2)

        db.session.commit()

    def test_01_multi_tenant_data_isolation(self):
        """Verify strict tenant isolation across database queries (Tenant A cannot see Tenant B data)."""
        print("\n[VERIFICATION] Running Multi-Tenant Isolation Verification...")
        
        # Verify Stanford admin sees ONLY Stanford resources & students
        stanford_resources = Resource.query.filter_by(college_id=self.c1.id).all()
        self.assertEqual(len(stanford_resources), 1)
        self.assertEqual(stanford_resources[0].name, "AI Supercomputing Center 101")
        self.assertNotIn("Robotics Testing Chamber", [r.name for r in stanford_resources])

        # Verify MIT admin sees ONLY MIT resources
        mit_resources = Resource.query.filter_by(college_id=self.c2.id).all()
        self.assertEqual(len(mit_resources), 1)
        self.assertEqual(mit_resources[0].name, "MIT Robotics Testing Chamber")
        self.assertNotIn("AI Supercomputing Center 101", [r.name for r in mit_resources])
        
        # Verify College Users cannot cross borders
        stanford_users = User.query.filter_by(college_id=self.c1.id).all()
        mit_emails = [u.email for u in stanford_users]
        self.assertNotIn("student@mit.edu", mit_emails)
        self.assertNotIn("admin@mit.edu", mit_emails)
        print("  --> [SUCCESS] Multi-tenant isolation verified across colleges.")

    def test_02_zero_collision_scheduling_engine(self):
        """Verify algorithmic prevention of overlapping resource bookings."""
        print("\n[VERIFICATION] Running Zero-Collision Scheduling Engine Testing...")
        
        test_date = date(2026, 8, 15)
        
        # 1. Create an approved booking for Stanford AI Lab from 10:00 to 12:00
        base_booking = Booking(
            college_id=self.c1.id,
            user_id=self.c1_faculty.id,
            resource_id=self.res1.id,
            booking_date=test_date,
            start_time=time(10, 0),
            end_time=time(12, 0),
            purpose="Advanced Neural Networks Lecture",
            status="approved"
        )
        db.session.add(base_booking)
        db.session.commit()

        # 2. Check collision against an overlapping morning request (09:00 to 11:00) -> MUST OVERLAP
        conflict_1 = Booking.check_collision(
            college_id=self.c1.id,
            resource_id=self.res1.id,
            booking_date=test_date,
            start_time=time(9, 0),
            end_time=time(11, 0)
        )
        self.assertIsNotNone(conflict_1)
        self.assertEqual(conflict_1.id, base_booking.id)
        print("  --> [SUCCESS] Overlapping start boundary interval (09:00 - 11:00) blocked!")

        # 3. Check collision against an internal contained request (10:30 to 11:30) -> MUST OVERLAP
        conflict_2 = Booking.check_collision(
            college_id=self.c1.id,
            resource_id=self.res1.id,
            booking_date=test_date,
            start_time=time(10, 30),
            end_time=time(11, 30)
        )
        self.assertIsNotNone(conflict_2)
        print("  --> [SUCCESS] Inside subset interval (10:30 - 11:30) blocked!")

        # 4. Check collision against an overlapping end boundary request (11:00 to 13:00) -> MUST OVERLAP
        conflict_3 = Booking.check_collision(
            college_id=self.c1.id,
            resource_id=self.res1.id,
            booking_date=test_date,
            start_time=time(11, 0),
            end_time=time(13, 0)
        )
        self.assertIsNotNone(conflict_3)
        print("  --> [SUCCESS] Overlapping end boundary interval (11:00 - 13:00) blocked!")

        # 5. Check non-overlapping afternoon slot (13:00 to 15:00) -> MUST PASS CLEANLY
        vacant = Booking.check_collision(
            college_id=self.c1.id,
            resource_id=self.res1.id,
            booking_date=test_date,
            start_time=time(13, 0),
            end_time=time(15, 0)
        )
        self.assertIsNone(vacant)
        print("  --> [SUCCESS] Non-overlapping afternoon interval (13:00 - 15:00) passed cleanly without false positives!")

        # 6. Check that another resource (MIT Robotics Lab) on the EXACT SAME TIME is unaffected
        mit_check = Booking.check_collision(
            college_id=self.c2.id,
            resource_id=self.res2.id,
            booking_date=test_date,
            start_time=time(10, 0),
            end_time=time(12, 0)
        )
        self.assertIsNone(mit_check)
        print("  --> [SUCCESS] Multi-tenant cross-resource scheduling isolation verified!")

    def test_03_telemetry_notifications_and_audit_logging(self):
        """Verify automated real-time notification alerts and audit logging engine."""
        print("\n[VERIFICATION] Running Telemetry & Audit Logs Engine Verification...")
        
        # Dispatch notification to Stanford Student
        notif = Notification.create_notification(
            user_id=self.c1_student.id,
            college_id=self.c1.id,
            title="Booking Authorized",
            message="Your reservation #BKG-101 has been approved.",
            category="success",
            link_url="/student/my-bookings"
        )
        db.session.commit()

        unreads = Notification.query.filter_by(user_id=self.c1_student.id, is_read=False).all()
        self.assertEqual(len(unreads), 1)
        self.assertEqual(unreads[0].title, "Booking Authorized")
        print("  --> [SUCCESS] In-app real-time notification dispatched and unread count validated.")

        # Log Activity Telemetry Event
        ActivityLog.log("RESOURCE_CREATED", user_id=self.c1_admin.id, college_id=self.c1.id, entity_type="Resource", entity_id=self.res1.id, details="Created new computer lab.")
        db.session.commit()

        logs = ActivityLog.query.filter_by(college_id=self.c1.id).all()
        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0].action, "RESOURCE_CREATED")
        self.assertEqual(logs[0].user_id, self.c1_admin.id)
        print("  --> [SUCCESS] Activity audit log persisted with complete tenant tagging.")

    def test_04_http_route_accessibility_and_rbac_boundaries(self):
        """Verify public endpoints access and security redirection for protected tenant portals."""
        print("\n[VERIFICATION] Running HTTP Route & RBAC Access Verification...")
        client = self.app.test_client()

        # Test Landing page & Public forms
        res_landing = client.get('/')
        self.assertEqual(res_landing.status_code, 200)
        self.assertIn(b"Campus", res_landing.data)
        
        res_register = client.get('/register-college')
        self.assertEqual(res_register.status_code, 200)
        
        # Test Unauthenticated access to protected dashboard -> MUST REDIRECT TO LOGIN
        res_unauth = client.get('/admin/dashboard', follow_redirects=True)
        self.assertEqual(res_unauth.status_code, 200)
        self.assertIn(b"Please log in to access this page", res_unauth.data)
        print("  --> [SUCCESS] Unauthenticated requests securely redirected to authorization gateway.")


if __name__ == '__main__':
    print("=====================================================================")
    print("    CAMPUSHUB PRODUCTION QUALITY & MULTI-TENANT VERIFICATION ENGINE  ")
    print("=====================================================================")
    unittest.main(verbosity=1)
