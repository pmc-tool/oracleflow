"""OracleFlow Intelligence API Blueprints."""

from flask import Blueprint

sites_bp = Blueprint('of_sites', __name__)
signals_bp = Blueprint('of_signals', __name__)
chaos_bp = Blueprint('of_chaos', __name__)
entities_bp = Blueprint('of_entities', __name__)
countries_bp = Blueprint('of_countries', __name__)
alerts_bp = Blueprint('of_alerts', __name__)
feeds_bp = Blueprint('of_feeds', __name__)

from . import sites, signals, chaos, entities, countries, alerts  # noqa: E402, F401
