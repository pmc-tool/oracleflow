from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, scoped_session
from app.oracleflow.models.base import Base

_engine = None
_session_factory = None

def _migrate_add_columns(engine):
    """Add missing columns to existing tables (lightweight migration)."""
    migrations = [
        ("signals", "organization_id", "INTEGER"),
        ("monitored_sites", "organization_id", "INTEGER"),
        ("entities", "organization_id", "INTEGER"),
        ("alerts", "organization_id", "INTEGER"),
        ("simulations", "organization_id", "INTEGER"),
    ]
    with engine.connect() as conn:
        for table, column, col_type in migrations:
            try:
                # Use IF NOT EXISTS to avoid blocking ALTER TABLE on existing columns
                conn.execute(text(
                    f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS {column} {col_type}"
                ))
                conn.commit()
            except Exception:
                conn.rollback()

        # Add composite index for category + timestamp filtering
        try:
            conn.execute(text(
                "CREATE INDEX IF NOT EXISTS ix_signals_category_timestamp ON signals(category, timestamp DESC)"
            ))
            conn.commit()
        except Exception:
            conn.rollback()

        # Additional indexes for query performance
        _additional_indexes = [
            "CREATE INDEX IF NOT EXISTS ix_signals_source ON signals(source)",
            "CREATE INDEX IF NOT EXISTS ix_signals_title_timestamp ON signals(title, timestamp DESC)",
            "CREATE INDEX IF NOT EXISTS ix_page_snapshots_page_captured ON page_snapshots(page_id, captured_at DESC)",
            "CREATE INDEX IF NOT EXISTS ix_page_diffs_page_id ON page_diffs(page_id)",
            "CREATE INDEX IF NOT EXISTS ix_notifications_user_read ON notifications(user_id, is_read)",
        ]
        for idx_sql in _additional_indexes:
            try:
                conn.execute(text(idx_sql))
                conn.commit()
            except Exception:
                conn.rollback()

def init_db(app):
    """Initialize SQLAlchemy with Flask app config."""
    global _engine, _session_factory
    db_url = app.config.get('DATABASE_URL', 'sqlite:///oracleflow.db')
    pool_args = {}
    if 'sqlite' not in db_url:
        pool_args = {
            'pool_size': 20,
            'max_overflow': 30,
            'pool_timeout': 30,
            'pool_recycle': 1800,
            'pool_pre_ping': True,
        }
    _engine = create_engine(db_url, echo=app.config.get('DEBUG', False), **pool_args)
    _session_factory = scoped_session(sessionmaker(bind=_engine))
    # Import all models so tables are registered
    from app.oracleflow.models import signal, site, entity
    from app.oracleflow.auth import models as auth_models  # noqa: F841
    Base.metadata.create_all(_engine)
    _migrate_add_columns(_engine)

def get_session():
    """Get a scoped session."""
    return _session_factory()

def close_session(exception=None):
    """Remove scoped session."""
    if _session_factory:
        _session_factory.remove()
