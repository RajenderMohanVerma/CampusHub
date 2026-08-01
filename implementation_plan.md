# CampusHub - Multi-College Campus Resource Management System

A multi-tenant SaaS platform where Colleges and Universities can register, manage campus resources (labs, seminar halls, equipment), and streamline bookings between students, faculty, and administrators with strict workspace isolation and modern SaaS aesthetics.

## User Review Required

> [!IMPORTANT]  
> **Multi-Tenant Isolation Architecture**: Every database table (except `PlatformAdmin` and global system tables) includes a `college_id` column. We enforce strict data isolation by utilizing a custom repository pattern and query filtering in all Blueprint controllers (`query.filter_by(college_id=current_user.college_id)`).

> [!NOTE]  
> **Authentication & OTP Demonstration**: To ensure the application is 100% functional out of the box without requiring paid external SMS or SMTP services, Email OTPs and simulating Google OAuth login will fall back to local logging and a test-developer modal when live credentials are not present in `.env`.

---

## Open Questions

All requirements specified in the project concept are comprehensive. The build will execute module-by-module continuously upon approval until all 14 phases are fully realized and tested with sample seeding.

---

## Proposed Changes

We will develop the application using a clean, scalable Application Factory pattern with modular Blueprints.

### Core Application Setup & Extensions
- `app/__init__.py`: Flask application factory with extensions initialization and error handler registration.
- `app/extensions.py`: Initializations for SQLAlchemy, LoginManager, Bcrypt, WTF, CSRF, and Mail.
- `config.py`: Development, Testing, and Production configuration profiles with environment variable support.
- `seed.py`: Enterprise seeding script creating sample colleges (to test data isolation), Platform Admin, College Admins, Faculty, Students, Departments, Resources, and sample bookings.

### Database Models (`app/models/`)
- `user.py`: Unified authentication abstraction (`User`, `PlatformAdmin`, `CollegeAdmin`, `Faculty`, `Student`). Incorporates role-based privileges, OTP tokens, and `college_id` foreign keys.
- `college.py`: `College` and `Department` models with approval status (`pending`, `active`, `suspended`).
- `resource.py`: `Resource` model covering Computer Labs, Classrooms, Seminar Halls, Conference Rooms, Projectors, and Equipment.
- `booking.py`: `Booking` model supporting time slots, approval flow, collision detection, and admin remarks.
- `system.py`: `Notification`, `Report`, and `ActivityLog` models for auditing and live notifications.

### Authentication & Authorization (`app/blueprints/auth/`)
- Role-based decorators: `@login_required`, `@role_required(*roles)`, and tenant check helpers.
- Email OTP login and simulation OAuth 2.0 flow.
- Password hashing via Flask-Bcrypt and CSRF defense via Flask-WTF.

### Public & Landing Modules (`app/blueprints/main/`)
- High-conversion SaaS landing page with animated gradients, glassmorphic cards, feature breakdowns, and College Registration wizard.
- About Us, Contact Us, and public system status.

### Platform Admin Module (`app/blueprints/platform_admin/`)
- Superuser control panel to approve, reject, or suspend registered colleges.
- Cross-tenant system analytical overview and audit log viewer.

### College Admin Module (`app/blueprints/college_admin/`)
- Tenant-scoped dashboard featuring Chart.js visual analytics (Resource usage rates, departmental booking trends).
- CRUD managers for Departments, Faculty members, Students, and physical/digital campus resources.
- Booking management hub to approve or reject pending booking requests with custom feedback notes.

### Student & Faculty Modules (`app/blueprints/student/` & `app/blueprints/faculty/`)
- **Student Dashboard**: Live catalog of campus resources, conflict-free interactive booking wizard, history tracking, and notification center.
- **Faculty Dashboard**: Academic scheduling, prioritized booking interface, department resource logs, and profile management.

### Modern UI/UX Architecture (`app/static/` & `app/templates/`)
- **Styling (`css/style.css`)**: Vanilla CSS custom properties (variables), vibrant dark/light theme switching, glassmorphic card elements, custom scrollbars, toast containers, and responsive animated sidebars.
- **Dynamic UX (`js/main.js`, `js/charts.js`)**: Sidebar toggle controls, real-time table filtering and live instant search, automated form validation, Chart.js visualizations, and dynamic toast alerts.

---

## Development Order & Verification Plan

### Automated Tests
- **Database & Model Isolation Verification**: Write unit testing scripts to verify that User A from College X cannot access or query Resources/Bookings from College Y.
- **Booking Conflict Engine Test**: Ensure overlapping date-time slots for the same resource raise appropriate validation exceptions.

### Manual Verification
- Execute `python seed.py` to generate complete sample data across 2 separate universities and 4 distinct roles.
- Run the Flask development server (`flask run` or `python run.py`) and verify all workflows:
  1. Register a new college -> Platform Admin approves -> College Admin logs in.
  2. College Admin populates departments & resources -> Student books resource -> Admin approves -> Notification fired.
  3. Toggle Dark/Light mode and test responsiveness across mobile/desktop layouts.
