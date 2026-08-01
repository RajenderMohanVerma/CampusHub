"""Flask Application Factory for CampusHub platform."""
import os
from flask import Flask, render_template, g, request
from flask_login import current_user
from app.extensions import db, login_manager, mail, bcrypt, csrf
from app.utils import format_timestamp, format_date
from config import config_by_name


def create_app(config_name=None):
    """Initializes and builds the Flask web application instance."""
    if not config_name:
        config_name = os.environ.get('FLASK_ENV', 'default')

    app = Flask(__name__)
    app.config.from_object(config_by_name[config_name])

    # Initialize extensions with app instance
    db.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)
    bcrypt.init_app(app)
    csrf.init_app(app)

    # Register custom Jinja template filters and context processors
    app.jinja_env.filters['format_timestamp'] = format_timestamp
    app.jinja_env.filters['format_date'] = format_date
    
    @app.context_processor
    def inject_global_vars():
        """Injects global branding, user role helpers, and counts to all templates."""
        unread_notifications_count = 0
        if current_user.is_authenticated:
            unread_notifications_count = current_user.notifications.filter_by(is_read=False).count()
            
        return {
            'app_name': 'CampusHub',
            'app_tagline': 'Connecting Students, Faculty & Resources.',
            'current_user': current_user,
            'unread_notifications_count': unread_notifications_count
        }

    # Setup Flask-Login user loader
    from app.models import User
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Register Blueprints
    from app.blueprints.auth import auth_bp
    from app.blueprints.main import main_bp
    from app.blueprints.platform_admin import platform_admin_bp
    from app.blueprints.college_admin import college_admin_bp
    from app.blueprints.student import student_bp
    from app.blueprints.faculty import faculty_bp
    from app.blueprints.notifications import notifications_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(platform_admin_bp, url_prefix='/platform')
    app.register_blueprint(college_admin_bp, url_prefix='/admin')
    app.register_blueprint(faculty_bp, url_prefix='/faculty')
    app.register_blueprint(student_bp, url_prefix='/student')
    app.register_blueprint(notifications_bp, url_prefix='/notifications')

    # Global HTTP error handlers
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('errors/404.html'), 404

    @app.errorhandler(403)
    def forbidden_access(e):
        return render_template('errors/403.html'), 403

    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('errors/500.html'), 500

    # Ensure tables exist on startup
    with app.app_context():
        # Ensure database tables exist
        db.create_all()

    return app
