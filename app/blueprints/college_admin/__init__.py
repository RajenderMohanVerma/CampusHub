"""College Admin Blueprint Initialization."""
from flask import Blueprint

college_admin_bp = Blueprint('college_admin', __name__, template_folder='../../templates/college_admin')

from app.blueprints.college_admin import routes
