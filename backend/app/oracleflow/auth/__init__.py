from flask import Blueprint
auth_bp = Blueprint('of_auth', __name__)
from . import routes
