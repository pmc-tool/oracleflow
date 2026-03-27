from flask import Blueprint
billing_bp = Blueprint('of_billing', __name__)
from . import routes
