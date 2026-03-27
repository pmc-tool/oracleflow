"""
MiroFish Backend - Flask Application Factory
"""

import os
import warnings

# Suppress multiprocessing resource_tracker warnings (from third-party libraries like transformers)
# Must be set before all other imports
warnings.filterwarnings("ignore", message=".*resource_tracker.*")

from flask import Blueprint, Flask, jsonify, redirect, request, url_for
from flask_cors import CORS

from .config import Config
from .utils.logger import setup_logger, get_logger


def create_app(config_class=Config):
    """Flask application factory function"""
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Configure JSON encoding: ensure Chinese displays directly (not as \uXXXX)
    # Flask >= 2.3 uses app.json.ensure_ascii, older versions use JSON_AS_ASCII config
    if hasattr(app, 'json') and hasattr(app.json, 'ensure_ascii'):
        app.json.ensure_ascii = False

    # Setup logging
    logger = setup_logger('mirofish')

    # Only print startup info in reloader subprocess (avoid printing twice in debug mode)
    is_reloader_process = os.environ.get('WERKZEUG_RUN_MAIN') == 'true'
    debug_mode = app.config.get('DEBUG', False)
    should_log_startup = not debug_mode or is_reloader_process

    if should_log_startup:
        logger.info("=" * 50)
        logger.info("MiroFish-Offline Backend starting...")
        logger.info("=" * 50)

    # Enable CORS
    CORS(app, resources={r"/api/*": {"origins": ["http://localhost:3000", "http://localhost:3002", "http://localhost:5173", os.environ.get("FRONTEND_URL", "http://localhost:3002")]}})

    # --- Initialize Neo4jStorage singleton (DI via app.extensions) ---
    from .storage import Neo4jStorage
    try:
        neo4j_storage = Neo4jStorage()
        app.extensions['neo4j_storage'] = neo4j_storage
        if should_log_startup:
            logger.info("Neo4jStorage initialized (connected to %s)", Config.NEO4J_URI)
    except Exception as e:
        logger.error("Neo4jStorage initialization failed: %s", e)
        # Store None so endpoints can return 503 gracefully
        app.extensions['neo4j_storage'] = None

    # Initialize OracleFlow SQL database
    from .oracleflow.database import init_db, close_session
    init_db(app)
    app.teardown_appcontext(close_session)

    # Register simulation process cleanup function (ensure all simulation processes terminate on server shutdown)
    from .services.simulation_runner import SimulationRunner
    SimulationRunner.register_cleanup()
    if should_log_startup:
        logger.info("Simulation process cleanup function registered")

    # Request logging middleware
    @app.before_request
    def log_request():
        logger = get_logger('mirofish.request')
        logger.debug(f"Request: {request.method} {request.path}")
        if request.content_type and 'json' in request.content_type:
            logger.debug(f"Request body: {request.get_json(silent=True)}")

    @app.after_request
    def log_response(response):
        logger = get_logger('mirofish.request')
        logger.debug(f"Response: {response.status_code}")
        return response

    # Register blueprints
    from .api import graph_bp, simulation_bp, report_bp
    app.register_blueprint(graph_bp, url_prefix='/api/graph')
    app.register_blueprint(simulation_bp, url_prefix='/api/simulation')
    app.register_blueprint(report_bp, url_prefix='/api/report')

    # OracleFlow Intelligence Blueprints
    from .oracleflow.api import (
        sites_bp, signals_bp, chaos_bp,
        entities_bp, countries_bp, alerts_bp,
    )
    app.register_blueprint(sites_bp, url_prefix='/api/sites')
    app.register_blueprint(signals_bp, url_prefix='/api/signals')
    app.register_blueprint(chaos_bp, url_prefix='/api/chaos')
    # Also register under /api/chaos-index for clients using the longer URL
    chaos_index_bp = Blueprint('of_chaos_index', __name__)

    @chaos_index_bp.route('/', methods=['GET'])
    def chaos_index_redirect_root():
        return redirect(url_for('of_chaos.get_latest_chaos'), code=307)

    @chaos_index_bp.route('/history', methods=['GET'])
    def chaos_index_redirect_history():
        return redirect(url_for('of_chaos.get_chaos_history', **request.args), code=307)

    app.register_blueprint(chaos_index_bp, url_prefix='/api/chaos-index')
    app.register_blueprint(entities_bp, url_prefix='/api/entities')
    app.register_blueprint(countries_bp, url_prefix='/api/countries')
    app.register_blueprint(alerts_bp, url_prefix='/api/alerts')

    # OracleFlow Auth Blueprint
    from .oracleflow.auth import auth_bp
    from .oracleflow.auth import models as auth_models  # noqa: F841 — ensure tables are created
    app.register_blueprint(auth_bp, url_prefix='/api/auth')

    # OracleFlow Billing Blueprint
    from .oracleflow.billing import billing_bp
    app.register_blueprint(billing_bp, url_prefix='/api/billing')

    # Initialize OracleFlow real-time layer (WebSocket + SSE)
    from .oracleflow.realtime import init_realtime
    init_realtime(app)

    # Start OracleFlow background scheduler
    from .oracleflow.scheduler import start_scheduler
    start_scheduler(app)

    # Global error handlers
    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"success": False, "error": "Not found"}), 404

    @app.errorhandler(500)
    def internal_error(e):
        return jsonify({"success": False, "error": "Internal server error"}), 500

    @app.errorhandler(405)
    def method_not_allowed(e):
        return jsonify({"success": False, "error": "Method not allowed"}), 405

    # Health check
    @app.route('/health')
    def health():
        return {'status': 'ok', 'service': 'MiroFish-Offline Backend'}

    if should_log_startup:
        logger.info("MiroFish-Offline Backend startup complete")

    return app

