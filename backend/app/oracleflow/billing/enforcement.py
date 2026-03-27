"""Plan enforcement decorators — check usage limits before allowing actions."""

from functools import wraps

from flask import g, jsonify
from sqlalchemy import select, func

from app.oracleflow.database import get_session
from app.oracleflow.auth.models import Organization, PLAN_LIMITS
from app.oracleflow.models.site import MonitoredSite


def check_site_limit(f):
    """Reject request if organization has reached its site limit."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not hasattr(g, 'org_id'):
            return f(*args, **kwargs)
        db = get_session()
        try:
            org = db.execute(
                select(Organization).where(Organization.id == g.org_id)
            ).scalar_one_or_none()
            if org:
                sites_count = db.execute(
                    select(func.count())
                    .select_from(MonitoredSite)
                    .where(MonitoredSite.organization_id == g.org_id)
                ).scalar() or 0
                if sites_count >= org.max_sites:
                    return jsonify({
                        "success": False,
                        "error": f"Site limit reached ({sites_count}/{org.max_sites}). Upgrade your plan.",
                        "upgrade": True,
                    }), 403
        finally:
            db.close()
        return f(*args, **kwargs)
    return decorated


def check_simulation_limit(f):
    """Reject request if organization cannot run simulations on current plan."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not hasattr(g, 'org_id'):
            return f(*args, **kwargs)
        db = get_session()
        try:
            org = db.execute(
                select(Organization).where(Organization.id == g.org_id)
            ).scalar_one_or_none()
            if org and org.max_simulations_per_month <= 0 and org.plan == 'free':
                return jsonify({
                    "success": False,
                    "error": "Simulations not available on Free plan. Upgrade to Watch or higher.",
                    "upgrade": True,
                }), 403
        finally:
            db.close()
        return f(*args, **kwargs)
    return decorated
