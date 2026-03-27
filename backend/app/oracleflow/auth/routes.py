"""OracleFlow authentication API endpoints."""

import logging
import re
import uuid
from datetime import datetime, timezone

from flask import jsonify, request

from . import auth_bp
from app.oracleflow.database import get_session
from app.oracleflow.auth.models import User, Organization, Subscription, PLAN_LIMITS, UserPreferences
from app.oracleflow.auth.utils import hash_password, verify_password, create_token

logger = logging.getLogger(__name__)
from app.oracleflow.auth.middleware import require_auth
from app.oracleflow.auth.personas import PERSONA_DEFAULTS


def _get_db():
    return get_session()


@auth_bp.route('/register', methods=['POST'])
def register():
    """Create a new user and organization, return JWT token."""
    db = _get_db()
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "Request body is required"}), 400

        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        name = data.get('name', '').strip()
        org_name = data.get('org_name', '').strip() if data.get('org_name') else ''
        persona = data.get('persona')
        interest_categories = data.get('interest_categories')

        if not email or not password or not name:
            return jsonify({"success": False, "error": "email, password, and name are required"}), 400

        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            return jsonify({"success": False, "error": "Invalid email format"}), 400

        # Auto-generate org_name if not provided
        if not org_name:
            org_name = f"{name}'s Workspace"

        if len(password) < 8:
            return jsonify({"success": False, "error": "Password must be at least 8 characters"}), 400

        # Check if email already taken
        existing = db.query(User).filter(User.email == email).first()
        if existing:
            return jsonify({"success": False, "error": "Email already registered"}), 409

        # Create organization with free plan defaults
        plan = 'free'
        limits = PLAN_LIMITS[plan]
        slug = org_name.lower().replace(' ', '-')[:40] + '-' + uuid.uuid4().hex[:6]

        org = Organization(
            name=org_name,
            slug=slug,
            plan=plan,
            max_users=limits['max_users'],
            max_sites=limits['max_sites'],
            max_simulations_per_month=limits['max_simulations'],
        )
        db.add(org)
        db.flush()

        # Create user with hashed password
        user = User(
            email=email,
            password_hash=hash_password(password),
            name=name,
            organization_id=org.id,
            role='admin',
        )
        db.add(user)
        db.flush()

        # Create user preferences
        persona_key = persona if persona in PERSONA_DEFAULTS else None
        if persona_key and not interest_categories:
            interest_categories = PERSONA_DEFAULTS[persona_key]['categories']
        dashboard_config = {}
        if persona_key:
            dashboard_config = {'panel_order': PERSONA_DEFAULTS[persona_key]['panels'], 'removed_panels': []}

        prefs = UserPreferences(
            user_id=user.id,
            persona_shortcut=persona_key,
            interest_categories=interest_categories or [],
            dashboard_config=dashboard_config,
            onboarding_completed=False,
        )
        db.add(prefs)

        # Create default alert rule for the user's selected categories
        from app.oracleflow.models.signal import AlertRuleDB
        categories = interest_categories or []
        default_rule = AlertRuleDB(
            user_id=user.id,
            organization_id=org.id,
            name="Default anomaly alert",
            condition_type="anomaly_threshold",
            threshold=0.7,
            categories_json=categories if categories else None,
            severity="medium",
            enabled=True,
        )
        db.add(default_rule)

        # If user selected specific categories, also create a diff-detection rule
        if categories:
            diff_rule = AlertRuleDB(
                user_id=user.id,
                organization_id=org.id,
                name="Page change alert",
                condition_type="diff_detected",
                threshold=0.0,
                categories_json=categories,
                severity="medium",
                enabled=True,
            )
            db.add(diff_rule)

        db.commit()

        token = create_token(user.id, org.id, plan, user.role)

        return jsonify({
            "success": True,
            "token": token,
            "user": {
                "id": user.id,
                "email": user.email,
                "name": user.name,
                "role": user.role,
            },
            "organization": {
                "id": org.id,
                "name": org.name,
                "slug": org.slug,
                "plan": org.plan,
            },
            "preferences": {
                "persona_shortcut": prefs.persona_shortcut,
                "interest_categories": prefs.interest_categories,
                "dashboard_config": prefs.dashboard_config,
                "onboarding_completed": prefs.onboarding_completed,
            },
        }), 201

    except Exception as e:
        db.rollback()
        logger.exception("Auth endpoint error: %s", e)
        return jsonify({"success": False, "error": "An internal error occurred"}), 500
    finally:
        db.close()


@auth_bp.route('/login', methods=['POST'])
def login():
    """Authenticate user with email and password, return JWT token."""
    db = _get_db()
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "Request body is required"}), 400

        email = data.get('email', '').strip().lower()
        password = data.get('password', '')

        if not email or not password:
            return jsonify({"success": False, "error": "email and password are required"}), 400

        user = db.query(User).filter(User.email == email).first()
        if not user or not verify_password(password, user.password_hash):
            return jsonify({"success": False, "error": "Invalid email or password"}), 401

        if not user.is_active:
            return jsonify({"success": False, "error": "Account is deactivated"}), 403

        # Update last_login
        user.last_login = datetime.now(timezone.utc)
        db.commit()

        org = user.organization
        plan = org.plan if org else 'free'

        token = create_token(user.id, org.id if org else None, plan, user.role)

        return jsonify({
            "success": True,
            "token": token,
            "user": {
                "id": user.id,
                "email": user.email,
                "name": user.name,
                "role": user.role,
            },
            "organization": {
                "id": org.id,
                "name": org.name,
                "slug": org.slug,
                "plan": org.plan,
            } if org else None,
        }), 200

    except Exception as e:
        db.rollback()
        logger.exception("Auth endpoint error: %s", e)
        return jsonify({"success": False, "error": "An internal error occurred"}), 500
    finally:
        db.close()


@auth_bp.route('/me', methods=['GET'])
@require_auth
def me():
    """Return current user, organization, and subscription info."""
    db = _get_db()
    try:
        from flask import g
        user = db.query(User).filter(User.id == g.user_id).first()
        if not user:
            return jsonify({"success": False, "error": "User not found"}), 404

        org = user.organization
        subscription = None
        if org:
            sub = db.query(Subscription).filter(
                Subscription.organization_id == org.id,
                Subscription.status == 'active',
            ).first()
            if sub:
                subscription = {
                    "id": sub.id,
                    "plan": sub.plan,
                    "status": sub.status,
                    "current_period_start": sub.current_period_start.isoformat() if sub.current_period_start else None,
                    "current_period_end": sub.current_period_end.isoformat() if sub.current_period_end else None,
                    "monthly_price": sub.monthly_price,
                }

        prefs = db.query(UserPreferences).filter(UserPreferences.user_id == user.id).first()
        preferences = None
        if prefs:
            preferences = {
                "persona_shortcut": prefs.persona_shortcut,
                "interest_categories": prefs.interest_categories,
                "dashboard_config": prefs.dashboard_config,
                "onboarding_completed": prefs.onboarding_completed,
            }

        return jsonify({
            "success": True,
            "user": {
                "id": user.id,
                "email": user.email,
                "name": user.name,
                "role": user.role,
                "is_active": user.is_active,
                "email_verified": user.email_verified,
                "created_at": user.created_at.isoformat() if user.created_at else None,
                "last_login": user.last_login.isoformat() if user.last_login else None,
            },
            "organization": {
                "id": org.id,
                "name": org.name,
                "slug": org.slug,
                "plan": org.plan,
                "max_users": org.max_users,
                "max_sites": org.max_sites,
                "max_simulations_per_month": org.max_simulations_per_month,
            } if org else None,
            "subscription": subscription,
            "preferences": preferences,
        }), 200

    except Exception as e:
        logger.exception("Auth endpoint error: %s", e)
        return jsonify({"success": False, "error": "An internal error occurred"}), 500
    finally:
        db.close()


@auth_bp.route('/preferences', methods=['GET'])
@require_auth
def get_preferences():
    """Return current user's preferences."""
    db = _get_db()
    try:
        from flask import g
        prefs = db.query(UserPreferences).filter(UserPreferences.user_id == g.user_id).first()
        if not prefs:
            return jsonify({"success": True, "preferences": None}), 200

        return jsonify({
            "success": True,
            "preferences": {
                "persona_shortcut": prefs.persona_shortcut,
                "interest_categories": prefs.interest_categories,
                "dashboard_config": prefs.dashboard_config,
                "onboarding_completed": prefs.onboarding_completed,
                "created_at": prefs.created_at.isoformat() if prefs.created_at else None,
                "updated_at": prefs.updated_at.isoformat() if prefs.updated_at else None,
            },
        }), 200

    except Exception as e:
        logger.exception("Auth endpoint error: %s", e)
        return jsonify({"success": False, "error": "An internal error occurred"}), 500
    finally:
        db.close()


@auth_bp.route('/preferences', methods=['PUT'])
@require_auth
def update_preferences():
    """Update current user's preferences."""
    db = _get_db()
    try:
        from flask import g
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "Request body is required"}), 400

        prefs = db.query(UserPreferences).filter(UserPreferences.user_id == g.user_id).first()
        if not prefs:
            prefs = UserPreferences(user_id=g.user_id)
            db.add(prefs)

        if 'persona_shortcut' in data:
            persona = data['persona_shortcut']
            if persona and persona not in PERSONA_DEFAULTS:
                return jsonify({"success": False, "error": f"Invalid persona: {persona}"}), 400
            prefs.persona_shortcut = persona
            # If switching persona, apply defaults unless categories/config explicitly provided
            if persona and persona in PERSONA_DEFAULTS:
                if 'interest_categories' not in data:
                    prefs.interest_categories = PERSONA_DEFAULTS[persona]['categories']
                if 'dashboard_config' not in data:
                    prefs.dashboard_config = {'panel_order': PERSONA_DEFAULTS[persona]['panels'], 'removed_panels': []}

        if 'interest_categories' in data:
            categories = data['interest_categories']
            plan_limits = PLAN_LIMITS.get(g.plan, PLAN_LIMITS['free'])
            max_cats = plan_limits.get('max_categories', 3)
            if len(categories) > max_cats:
                return jsonify({
                    "success": False,
                    "error": f"Your plan allows {max_cats} categories. Upgrade for more.",
                    "upgrade": True,
                    "limit": max_cats
                }), 403
            prefs.interest_categories = categories

        if 'dashboard_config' in data:
            prefs.dashboard_config = data['dashboard_config']

        if 'onboarding_completed' in data:
            prefs.onboarding_completed = data['onboarding_completed']

        db.commit()

        return jsonify({
            "success": True,
            "preferences": {
                "persona_shortcut": prefs.persona_shortcut,
                "interest_categories": prefs.interest_categories,
                "dashboard_config": prefs.dashboard_config,
                "onboarding_completed": prefs.onboarding_completed,
                "created_at": prefs.created_at.isoformat() if prefs.created_at else None,
                "updated_at": prefs.updated_at.isoformat() if prefs.updated_at else None,
            },
        }), 200

    except Exception as e:
        db.rollback()
        logger.exception("Auth endpoint error: %s", e)
        return jsonify({"success": False, "error": "An internal error occurred"}), 500
    finally:
        db.close()


@auth_bp.route('/plan-config', methods=['GET'])
@require_auth
def plan_config():
    """Return current plan limits and usage for panel/category gating."""
    db = _get_db()
    try:
        from flask import g
        from sqlalchemy import select, func
        from app.oracleflow.models.site import MonitoredSite

        user = db.query(User).filter(User.id == g.user_id).first()
        if not user:
            return jsonify({"success": False, "error": "User not found"}), 404

        org = user.organization
        plan = org.plan if org else 'free'
        limits = PLAN_LIMITS.get(plan, PLAN_LIMITS['free'])

        # Current usage
        sites_count = 0
        panels_visible = 0
        categories_selected = []
        if org:
            sites_count = db.execute(
                select(func.count()).select_from(MonitoredSite).where(
                    MonitoredSite.organization_id == org.id
                )
            ).scalar() or 0

        prefs = db.query(UserPreferences).filter(UserPreferences.user_id == user.id).first()
        if prefs:
            categories_selected = prefs.interest_categories or []
            config = prefs.dashboard_config or {}
            removed = config.get('removed_panels', [])
            panel_order = config.get('panel_order', [])
            # If panel_order is set, visible = len(panel_order) minus removed
            if panel_order:
                panels_visible = len([p for p in panel_order if p not in removed])
            else:
                # No custom order means all panels visible (minus removed)
                panels_visible = 26 - len(removed)  # 26 grid panels total

        return jsonify({
            "success": True,
            "plan": plan,
            "limits": {
                "max_panels": limits['max_panels'],
                "max_categories": limits['max_categories'],
                "max_sites": limits['max_sites'],
                "max_simulations": limits['max_simulations'],
            },
            "usage": {
                "panels_visible": panels_visible,
                "categories_selected": len(categories_selected),
                "sites_count": sites_count,
            },
        }), 200

    except Exception as e:
        logger.exception("Auth endpoint error: %s", e)
        return jsonify({"success": False, "error": "An internal error occurred"}), 500
    finally:
        db.close()


@auth_bp.route('/profile', methods=['PUT'])
@require_auth
def update_profile():
    """Update current user's name and/or password."""
    db = _get_db()
    try:
        from flask import g
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "Request body is required"}), 400

        user = db.query(User).filter(User.id == g.user_id).first()
        if not user:
            return jsonify({"success": False, "error": "User not found"}), 404

        if 'name' in data:
            name = data['name'].strip()
            if not name:
                return jsonify({"success": False, "error": "Name cannot be empty"}), 400
            user.name = name

        if 'password' in data:
            password = data['password']
            current_password = data.get('current_password', '')
            if not current_password or not verify_password(current_password, user.password_hash):
                return jsonify({"success": False, "error": "Current password is incorrect"}), 400
            if len(password) < 8:
                return jsonify({"success": False, "error": "Password must be at least 8 characters"}), 400
            user.password_hash = hash_password(password)

        db.commit()

        return jsonify({
            "success": True,
            "user": {
                "id": user.id,
                "email": user.email,
                "name": user.name,
                "role": user.role,
            },
        }), 200

    except Exception as e:
        db.rollback()
        logger.exception("Auth endpoint error: %s", e)
        return jsonify({"success": False, "error": "An internal error occurred"}), 500
    finally:
        db.close()
