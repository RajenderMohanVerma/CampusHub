"""Database seeding script generating enterprise multi-tenant sample data for CampusHub."""
from datetime import datetime, timedelta, date, time
from app import create_app
from app.extensions import db
from app.models import (
    User, PlatformAdmin, College, CollegeAdmin, Department,
    Faculty, Student, Resource, Booking, Notification, ActivityLog
)

app = create_app('dev')

with app.app_context():
    print("[INIT] Initializing CampusHub Database Seeding...")
    db.drop_all()
    db.create_all()

    # 1. Create Platform Super Admin (No College)
    print("[STEP 1] Creating Platform Admin...")
    p_admin_user = User(
        email="superadmin@campushub.edu",
        first_name="Rajender",
        last_name="Mohan",
        phone="+91 9876543210",
        role="platform_admin",
        is_active=True
    )
    p_admin_user.set_password("admin123")
    db.session.add(p_admin_user)
    db.session.flush()

    p_admin = PlatformAdmin(user_id=p_admin_user.id, permissions_level="superadmin")
    db.session.add(p_admin)

    # 2. Create Colleges (Multi-Tenant Isolation demonstration)
    print("[STEP 2] Creating Colleges...")
    c1 = College(
        name="Indian Institute of Technology, Delhi",
        code="IITD",
        email="contact@iitd.ac.in",
        phone="+91 11 2659 7135",
        address="Hauz Khas, New Delhi, Delhi 110016",
        website="https://home.iitd.ac.in",
        status="active",
        logo_url="https://ui-avatars.com/api/?name=IIT+Delhi&background=0d6efd&color=fff&size=200"
    )
    c2 = College(
        name="Stanford University India Research Campus",
        code="STAN",
        email="admin@stanford.edu",
        phone="+1 650-723-2300",
        address="Silicon Valley Hub, Bengaluru, Karnataka",
        website="https://www.stanford.edu",
        status="active",
        logo_url="https://ui-avatars.com/api/?name=Stanford&background=dc3545&color=fff&size=200"
    )
    c3 = College(
        name="MIT Bengaluru Institute of Technology",
        code="MITB",
        email="registrar@mitbangalore.edu",
        phone="+91 80 2345 6789",
        address="Whitefield, Bengaluru, Karnataka",
        status="pending",
        logo_url="https://ui-avatars.com/api/?name=MIT+B&background=ffc107&color=000&size=200"
    )
    db.session.add_all([c1, c2, c3])
    db.session.flush()

    c1.college_id = c1.id
    c2.college_id = c2.id
    c3.college_id = c3.id

    # 3. Create College Admins
    print("[STEP 3] Creating College Admins...")
    ca_user1 = User(
        email="admin.iitd@campushub.edu",
        first_name="Aravind",
        last_name="Kumar",
        phone="+91 9811112222",
        role="college_admin",
        college_id=c1.id,
        is_active=True
    )
    ca_user1.set_password("admin123")
    
    ca_user2 = User(
        email="admin.stanford@campushub.edu",
        first_name="Jennifer",
        last_name="Gates",
        phone="+1 650-555-0199",
        role="college_admin",
        college_id=c2.id,
        is_active=True
    )
    ca_user2.set_password("admin123")
    db.session.add_all([ca_user1, ca_user2])
    db.session.flush()

    ca1 = CollegeAdmin(user_id=ca_user1.id, college_id=c1.id, designation="Chief Registrar")
    ca2 = CollegeAdmin(user_id=ca_user2.id, college_id=c2.id, designation="Director of Resource Ops")
    db.session.add_all([ca1, ca2])

    # 4. Create Departments
    print("[STEP 4] Creating Departments...")
    dept_iit_cse = Department(college_id=c1.id, name="Computer Science & Engineering", code="CSE", head_name="Dr. H. N. Mahabala")
    dept_iit_ece = Department(college_id=c1.id, name="Electronics & Communication Engineering", code="ECE", head_name="Dr. S. K. Koul")
    dept_iit_mba = Department(college_id=c1.id, name="Department of Management Studies", code="DMS", head_name="Dr. Sushil Kumar")
    
    dept_stan_ai = Department(college_id=c2.id, name="Artificial Intelligence & Robotics", code="AIR", head_name="Dr. Andrew Ng")
    dept_stan_bio = Department(college_id=c2.id, name="Genomic Sciences & Biotechnology", code="BIO", head_name="Dr. Jennifer Doudna")
    
    db.session.add_all([dept_iit_cse, dept_iit_ece, dept_iit_mba, dept_stan_ai, dept_stan_bio])
    db.session.flush()

    # 5. Create Faculty
    print("[STEP 5] Creating Faculty Members...")
    fac_user1 = User(
        email="faculty.iitd@campushub.edu",
        first_name="Dr. Rajesh",
        last_name="Sharma",
        phone="+91 9988776655",
        role="faculty",
        college_id=c1.id
    )
    fac_user1.set_password("faculty123")
    
    fac_user2 = User(
        email="anita.desai@iitd.ac.in",
        first_name="Dr. Anita",
        last_name="Desai",
        phone="+91 9988776644",
        role="faculty",
        college_id=c1.id
    )
    fac_user2.set_password("faculty123")
    
    fac_user3 = User(
        email="faculty.stanford@campushub.edu",
        first_name="Dr. Robert",
        last_name="Oppenheimer",
        phone="+1 415-555-8888",
        role="faculty",
        college_id=c2.id
    )
    fac_user3.set_password("faculty123")
    db.session.add_all([fac_user1, fac_user2, fac_user3])
    db.session.flush()

    fac1 = Faculty(user_id=fac_user1.id, college_id=c1.id, department_id=dept_iit_cse.id, employee_id="EMP-CSE-101", designation="Associate Professor", specialization="Machine Learning & Quantum Computing")
    fac2 = Faculty(user_id=fac_user2.id, college_id=c1.id, department_id=dept_iit_ece.id, employee_id="EMP-ECE-102", designation="Senior Professor", specialization="VLSI Design & Robotics")
    fac3 = Faculty(user_id=fac_user3.id, college_id=c2.id, department_id=dept_stan_ai.id, employee_id="STAN-AI-01", designation="Department Chair", specialization="Autonomous Deep Learning Systems")
    db.session.add_all([fac1, fac2, fac3])

    # 6. Create Students
    print("[STEP 6] Creating Students...")
    stud_user1 = User(
        email="student.iitd@campushub.edu",
        first_name="Vikram",
        last_name="Verma",
        phone="+91 9777788888",
        role="student",
        college_id=c1.id
    )
    stud_user1.set_password("student123")
    
    stud_user2 = User(
        email="sneha.iitd@campushub.edu",
        first_name="Sneha",
        last_name="Kapoor",
        phone="+91 9777788899",
        role="student",
        college_id=c1.id
    )
    stud_user2.set_password("student123")

    stud_user3 = User(
        email="john.doe@stanford.edu",
        first_name="John",
        last_name="Doe",
        phone="+1 650-888-9999",
        role="student",
        college_id=c2.id
    )
    stud_user3.set_password("student123")
    db.session.add_all([stud_user1, stud_user2, stud_user3])
    db.session.flush()

    stud1 = Student(user_id=stud_user1.id, college_id=c1.id, department_id=dept_iit_cse.id, enrollment_number="IITD/2024/MCA001", course_name="Master of Computer Applications (MCA)", semester=4)
    stud2 = Student(user_id=stud_user2.id, college_id=c1.id, department_id=dept_iit_cse.id, enrollment_number="IITD/2024/MCA015", course_name="Master of Computer Applications (MCA)", semester=4)
    stud3 = Student(user_id=stud_user3.id, college_id=c2.id, department_id=dept_stan_ai.id, enrollment_number="STAN-AI-2025-08", course_name="M.S. Artificial Intelligence", semester=2)
    db.session.add_all([stud1, stud2, stud3])

    # 7. Create Campus Resources
    print("[STEP 7] Creating Campus Resources...")
    res_iit1 = Resource(
        college_id=c1.id,
        name="NVIDIA Deep Learning Super Lab",
        resource_type="Computer Lab",
        capacity=60,
        location="Block VI, Room 302 (CSE Dept)",
        description="State-of-the-art laboratory equipped with 60 workstations featuring NVIDIA RTX 4090 GPUs, 128GB RAM, and high-speed fiber internet for ML training.",
        image_url="https://images.unsplash.com/photo-1581092160607-ee22621dd758?w=800&auto=format&fit=crop&q=80",
        is_active=True
    )
    res_iit2 = Resource(
        college_id=c1.id,
        name="Tagore Executive Seminar Hall",
        resource_type="Seminar Hall",
        capacity=250,
        location="Main Academic Auditorium Building, Gate 3",
        description="Accoustically treated grand hall featuring Dolby Atmos audio system, dual 4K projection screens, and automated climate control.",
        image_url="https://images.unsplash.com/photo-1517457373958-b7bdd4587205?w=800&auto=format&fit=crop&q=80",
        is_active=True
    )
    res_iit3 = Resource(
        college_id=c1.id,
        name="Smart VR & Augmented Reality Workspace",
        resource_type="Computer Lab",
        capacity=35,
        location="Innovation Tech Park, 2nd Floor",
        description="Equipped with Oculus Quest 3, HTC Vive Pro headsets, 3D motion cameras, and specialized simulation suites.",
        image_url="https://images.unsplash.com/photo-1592478411213-6153e4ebc07d?w=800&auto=format&fit=crop&q=80",
        is_active=True
    )
    res_iit4 = Resource(
        college_id=c1.id,
        name="Boardroom A (Senate Lounge)",
        resource_type="Conference Room",
        capacity=20,
        location="Administrative Block, 4th Floor",
        description="Premium boardroom featuring Cisco Video Conferencing unit, smart interactive digital whiteboard, and plush leather seating.",
        image_url="https://images.unsplash.com/photo-1431540015161-0bf868a2d407?w=800&auto=format&fit=crop&q=80",
        is_active=True
    )
    res_iit5 = Resource(
        college_id=c1.id,
        name="Epson 4K Ultra-Short Throw Laser Projector",
        resource_type="Projector",
        capacity=1,
        location="Audio-Visual Equipment Desk, Library Basement",
        description="Portable high-lumens HDR laser projector with wireless Miracast/AirPlay streaming capability.",
        image_url="https://images.unsplash.com/photo-1584438784894-089d6a62b8fa?w=800&auto=format&fit=crop&q=80",
        is_active=True
    )
    res_iit6 = Resource(
        college_id=c1.id,
        name="Tektronix High-Frequency Digital Oscilloscope",
        resource_type="Equipment",
        capacity=4,
        location="ECE Advanced Instrumentation Lab, Block II",
        description="100 GHz sampling digital storage oscilloscope for high-precision VLSI and RF circuits experiments.",
        image_url="https://images.unsplash.com/photo-1581092580497-e0d23cbdf1dc?w=800&auto=format&fit=crop&q=80",
        is_active=True
    )

    res_stan1 = Resource(
        college_id=c2.id,
        name="Stanford Autonomous Robotics & Drone Dome",
        resource_type="Computer Lab",
        capacity=80,
        location="Gates Computer Science Building, Wing B",
        description="High-ceiling netted testing indoor arena for quadcopter swarms and Boston Dynamics automated legged robotic units.",
        image_url="https://images.unsplash.com/photo-1485827404703-89b55fcc595e?w=800&auto=format&fit=crop&q=80",
        is_active=True
    )
    db.session.add_all([res_iit1, res_iit2, res_iit3, res_iit4, res_iit5, res_iit6, res_stan1])
    db.session.flush()

    # 8. Create Realistic Bookings
    print("[STEP 8] Creating Sample Bookings...")
    today = date.today()
    tomorrow = today + timedelta(days=1)
    day_after = today + timedelta(days=2)

    b1 = Booking(
        college_id=c1.id,
        resource_id=res_iit1.id,
        user_id=stud_user1.id,
        department_id=dept_iit_cse.id,
        purpose="MCA Final Semester Deep Learning Project Presentation Setup",
        booking_date=tomorrow,
        start_time=time(10, 0),
        end_time=time(13, 0),
        status="approved",
        admin_remark="Approved for MCA research demonstration.",
        approved_by_id=ca_user1.id
    )
    b2 = Booking(
        college_id=c1.id,
        resource_id=res_iit2.id,
        user_id=fac_user1.id,
        department_id=dept_iit_cse.id,
        purpose="National Symposium on Quantum Supremacy & Cryptography",
        booking_date=day_after,
        start_time=time(14, 0),
        end_time=time(17, 30),
        status="approved",
        admin_remark="VIP guest lectures arranged. AV support informed.",
        approved_by_id=ca_user1.id
    )
    b3 = Booking(
        college_id=c1.id,
        resource_id=res_iit3.id,
        user_id=stud_user2.id,
        department_id=dept_iit_cse.id,
        purpose="VR Game Development Prototype Testing for ACM Hackathon",
        booking_date=tomorrow,
        start_time=time(15, 0),
        end_time=time(18, 0),
        status="pending",
        admin_remark=None
    )
    b4 = Booking(
        college_id=c1.id,
        resource_id=res_iit4.id,
        user_id=fac_user2.id,
        department_id=dept_iit_ece.id,
        purpose="Department Curriculum Review Committee Meeting",
        booking_date=today,
        start_time=time(11, 0),
        end_time=time(12, 30),
        status="approved",
        approved_by_id=ca_user1.id
    )
    db.session.add_all([b1, b2, b3, b4])
    db.session.flush()

    # 9. Create Notifications and Activity Logs
    print("[STEP 9] Generating Audit Logs & Notifications...")
    Notification.create_notification(
        user_id=stud_user1.id,
        college_id=c1.id,
        title="Booking Approved!",
        message="Your request for 'NVIDIA Deep Learning Super Lab' tomorrow has been approved by Admin.",
        category="success",
        link_url="/student/bookings"
    )
    Notification.create_notification(
        user_id=stud_user2.id,
        college_id=c1.id,
        title="Booking Under Review",
        message="Your request for 'Smart VR & Augmented Reality Workspace' is awaiting College Admin review.",
        category="info",
        link_url="/student/bookings"
    )
    Notification.create_notification(
        user_id=ca_user1.id,
        college_id=c1.id,
        title="New Booking Request",
        message="Student Sneha Kapoor has requested 'Smart VR Workspace' for tomorrow.",
        category="warning",
        link_url="/admin/bookings"
    )
    
    ActivityLog.log(action="COLLEGE_REGISTERED", user_id=p_admin_user.id, entity_type="College", entity_id=c1.id, details="IIT Delhi onboarded successfully.")
    ActivityLog.log(action="BOOKING_APPROVED", user_id=ca_user1.id, college_id=c1.id, entity_type="Booking", entity_id=b1.id, details="Approved AI Lab booking for Vikram Verma.")

    db.session.commit()
    print("[SUCCESS] CampusHub Database Seeding completed successfully with enterprise data!")
    print("\n--- TEST LOGIN CREDENTIALS ---")
    print("Platform Admin : superadmin@campushub.edu / admin123")
    print("IIT Delhi Admin: admin.iitd@campushub.edu   / admin123")
    print("Stanford Admin : admin.stanford@campushub.edu / admin123")
    print("Faculty (IITD) : faculty.iitd@campushub.edu / faculty123")
    print("Student (IITD) : student.iitd@campushub.edu / student123")
    print("--------------------------------")
