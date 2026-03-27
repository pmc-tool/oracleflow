"""Alert rules and notification API endpoints."""

import logging

from flask import g, jsonify, request

logger = logging.getLogger(__name__)
from sqlalchemy import select, func, update

from . import alerts_bp
from app.oracleflow.auth.middleware import require_auth, require_admin
from app.oracleflow.database import get_session
from app.oracleflow.models.signal import AlertRuleDB


@alerts_bp.route('/rules', methods=['GET'])
@require_auth
def list_rules():
    """List alert rules scoped to the authenticated org."""
    db = get_session()
    try:
        stmt = select(AlertRuleDB).where(AlertRuleDB.organization_id == g.org_id)
        result = db.execute(stmt)
        rules = list(result.scalars().all())

        data = []
        for r in rules:
            data.append({
                "id": r.id,
                "user_id": r.user_id,
                "org_id": r.organization_id,
                "name": r.name,
                "condition_type": r.condition_type,
                "threshold": r.threshold,
                "country_codes": r.country_codes_json or [],
                "categories": r.categories_json or [],
                "page_types": r.page_types_json or [],
                "severity": r.severity,
                "channels": r.channels_json or [],
                "webhook_url": r.webhook_url or "",
                "enabled": r.enabled,
            })

        return jsonify({"success": True, "data": data, "total": len(data)})
    except Exception as e:
        logger.exception("Alerts API error: %s", e)
        return jsonify({"success": False, "error": "An internal error occurred"}), 500
    finally:
        db.close()


@alerts_bp.route('/rules', methods=['POST'])
@require_auth
def create_rule():
    """Add an alert rule (org-scoped)."""
    db = get_session()
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "Request body is required"}), 400

        if not data.get('name'):
            return jsonify({"success": False, "error": "name is required"}), 400

        if not data.get('condition_type'):
            return jsonify({"success": False, "error": "condition_type is required"}), 400

        rule = AlertRuleDB(
            user_id=g.user_id,
            organization_id=g.org_id,
            name=data["name"],
            condition_type=data["condition_type"],
            threshold=data.get("threshold", 0.0),
            country_codes_json=data.get("country_codes", []),
            categories_json=data.get("categories", []),
            page_types_json=data.get("page_types", []),
            severity=data.get("severity", "medium"),
            channels_json=data.get("channels", []),
            webhook_url=data.get("webhook_url", ""),
            enabled=data.get("enabled", True),
        )
        db.add(rule)
        db.commit()

        return jsonify({"success": True, "data": {
            "id": rule.id,
            "user_id": rule.user_id,
            "org_id": rule.organization_id,
            "name": rule.name,
            "condition_type": rule.condition_type,
            "threshold": rule.threshold,
            "country_codes": rule.country_codes_json or [],
            "categories": rule.categories_json or [],
            "page_types": rule.page_types_json or [],
            "severity": rule.severity,
            "channels": rule.channels_json or [],
            "webhook_url": rule.webhook_url or "",
            "enabled": rule.enabled,
        }}), 201
    except Exception as e:
        db.rollback()
        logger.exception("Alerts API error: %s", e)
        return jsonify({"success": False, "error": "An internal error occurred"}), 500
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Notification endpoints
# ---------------------------------------------------------------------------

@alerts_bp.route('/notifications', methods=['GET'])
@require_auth
def list_notifications():
    """List the authenticated user's notifications (newest first, paginated)."""
    from app.oracleflow.models.signal import Notification

    db = get_session()
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        per_page = min(per_page, 100)
        offset = (page - 1) * per_page

        # Total count
        count_stmt = (
            select(func.count(Notification.id))
            .where(Notification.user_id == g.user_id)
        )
        total = db.execute(count_stmt).scalar() or 0

        # Unread count
        unread_stmt = (
            select(func.count(Notification.id))
            .where(Notification.user_id == g.user_id)
            .where(Notification.is_read == 0)
        )
        unread = db.execute(unread_stmt).scalar() or 0

        # Paginated list, newest first
        list_stmt = (
            select(Notification)
            .where(Notification.user_id == g.user_id)
            .order_by(Notification.created_at.desc())
            .offset(offset)
            .limit(per_page)
        )
        result = db.execute(list_stmt)
        notifications = list(result.scalars().all())

        data = [
            {
                "id": n.id,
                "signal_id": n.signal_id,
                "organization_id": n.organization_id,
                "title": n.title,
                "message": n.message,
                "severity": n.severity,
                "is_read": n.is_read,
                "created_at": n.created_at.isoformat() if n.created_at else None,
            }
            for n in notifications
        ]

        return jsonify({
            "success": True,
            "data": data,
            "total": total,
            "unread": unread,
            "page": page,
            "per_page": per_page,
        })
    except Exception as e:
        logger.exception("Alerts API error: %s", e)
        return jsonify({"success": False, "error": "An internal error occurred"}), 500
    finally:
        db.close()


@alerts_bp.route('/notifications/count', methods=['GET'])
@require_auth
def notification_unread_count():
    """Return the unread notification count for the authenticated user."""
    from app.oracleflow.models.signal import Notification

    db = get_session()
    try:
        stmt = (
            select(func.count(Notification.id))
            .where(Notification.user_id == g.user_id)
            .where(Notification.is_read == 0)
        )
        unread = db.execute(stmt).scalar() or 0
        return jsonify({"success": True, "unread": unread})
    except Exception as e:
        logger.exception("Alerts API error: %s", e)
        return jsonify({"success": False, "error": "An internal error occurred"}), 500
    finally:
        db.close()


@alerts_bp.route('/notifications/<int:notification_id>/read', methods=['PUT'])
@require_auth
def mark_notification_read(notification_id):
    """Mark a single notification as read."""
    from app.oracleflow.models.signal import Notification

    db = get_session()
    try:
        stmt = (
            select(Notification)
            .where(Notification.id == notification_id)
            .where(Notification.user_id == g.user_id)
        )
        notification = db.execute(stmt).scalar()
        if not notification:
            return jsonify({"success": False, "error": "Notification not found"}), 404

        notification.is_read = 1
        db.commit()
        return jsonify({"success": True})
    except Exception as e:
        db.rollback()
        logger.exception("Alerts API error: %s", e)
        return jsonify({"success": False, "error": "An internal error occurred"}), 500
    finally:
        db.close()


@alerts_bp.route('/notifications/read-all', methods=['PUT'])
@require_auth
def mark_all_notifications_read():
    """Mark all of the authenticated user's notifications as read."""
    from app.oracleflow.models.signal import Notification

    db = get_session()
    try:
        stmt = (
            update(Notification)
            .where(Notification.user_id == g.user_id)
            .where(Notification.is_read == 0)
            .values(is_read=1)
        )
        result = db.execute(stmt)
        db.commit()
        return jsonify({"success": True, "updated": result.rowcount})
    except Exception as e:
        db.rollback()
        logger.exception("Alerts API error: %s", e)
        return jsonify({"success": False, "error": "An internal error occurred"}), 500
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Email outbox (admin only, for verifying email delivery in testing)
# ---------------------------------------------------------------------------

@alerts_bp.route('/email-outbox', methods=['GET'])
@require_admin
def list_email_outbox():
    """List emails in the file-based outbox directory (admin only).

    Query params:
        limit (int): max emails to return, default 50
    """
    from app.oracleflow.alerts.delivery import list_outbox_emails

    try:
        limit = request.args.get('limit', 50, type=int)
        limit = min(limit, 200)
        emails = list_outbox_emails(limit=limit)
        return jsonify({"success": True, "data": emails, "total": len(emails)})
    except Exception as e:
        logger.exception("Email outbox API error: %s", e)
        return jsonify({"success": False, "error": "An internal error occurred"}), 500
