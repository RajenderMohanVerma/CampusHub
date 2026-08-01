"""Platform Superadmin Blueprint Initialization."""
from flask import Blueprint

platform_admin_bp = Blueprint('platform_admin', __name__, template_folder='../../templates/platform_admin')

from app.blueprints.platform_admin import routes
