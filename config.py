import os
from datetime import timedelta

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    """Base configuration settings for CampusHub platform."""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'campushub-enterprise-super-secret-key-2026'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///' + os.path.join(basedir, 'campushub.db')
    
    # Security & Session management
    SESSION_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_DURATION = timedelta(days=14)
    WTF_CSRF_ENABLED = True
    
    # Email configuration (Flask-Mail)
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.googlemail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME', 'no-reply@campushub.edu')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD', 'secret-pass')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', 'CampusHub Platform <no-reply@campushub.edu>')
    
    # OTP Settings
    OTP_EXPIRY_MINUTES = 10
    SIMULATION_MODE = os.environ.get('SIMULATION_MODE', 'True').lower() in ['true', 'on', '1']


class DevelopmentConfig(Config):
    """Development stage configuration with extra debugging features."""
    DEBUG = True
    TESTING = False
    SQLALCHEMY_ECHO = False


class TestingConfig(Config):
    """Testing configuration utilizing an in-memory database."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    SIMULATION_MODE = True


class ProductionConfig(Config):
    """Production stage configuration."""
    DEBUG = False
    TESTING = False
    # Ensure production uses strong secret keys
    SECRET_KEY = os.environ.get('SECRET_KEY', 'production-fallback-key-requires-env-var')


config_by_name = {
    'dev': DevelopmentConfig,
    'development': DevelopmentConfig,
    'test': TestingConfig,
    'testing': TestingConfig,
    'prod': ProductionConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
