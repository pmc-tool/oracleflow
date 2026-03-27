"""Chaos Index API endpoints."""

import logging
from datetime import datetime, timedelta, timezone

from flask import jsonify, request

logger = logging.getLogger(__name__)
from sqlalchemy import select

from . import chaos_bp
from app.oracleflow.database import get_session
from app.oracleflow.models.signal import ChaosIndex


def _get_db():
    return get_session()


@chaos_bp.route('/', methods=['GET'])
def get_latest_chaos():
    """Return the latest ChaosIndex record."""
    db = _get_db()
    try:
        stmt = select(ChaosIndex).order_by(ChaosIndex.timestamp.desc()).limit(1)
        result = db.execute(stmt)
        record = result.scalar_one_or_none()

        if not record:
            return jsonify({
                "success": True,
                "data": {
                    "global_score": 0.0,
                    "category_scores": {},
                    "timestamp": None,
                }
            })

        data = {
            "global_score": record.global_score,
            "category_scores": record.category_scores_json or {},
            "timestamp": record.timestamp.isoformat() if record.timestamp else None,
        }

        return jsonify({"success": True, "data": data})
    except Exception as e:
        db.rollback()
        logger.exception("Chaos API error: %s", e)
        return jsonify({"success": False, "error": "An internal error occurred"}), 500
    finally:
        db.close()


@chaos_bp.route('/history', methods=['GET'])
def get_chaos_history():
    """Return ChaosIndex records for the last N days."""
    db = _get_db()
    try:
        days = request.args.get('days', 7, type=int)
        days = min(days, 200)
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)

        stmt = (
            select(ChaosIndex)
            .where(ChaosIndex.timestamp >= cutoff)
            .order_by(ChaosIndex.timestamp.desc())
        )
        result = db.execute(stmt)
        records = list(result.scalars().all())

        data = []
        for r in records:
            data.append({
                "id": r.id,
                "global_score": r.global_score,
                "category_scores": r.category_scores_json or {},
                "contributing_signal_ids": r.contributing_signal_ids_json or [],
                "timestamp": r.timestamp.isoformat() if r.timestamp else None,
            })

        return jsonify({"success": True, "data": data, "total": len(data)})
    except Exception as e:
        db.rollback()
        logger.exception("Chaos API error: %s", e)
        return jsonify({"success": False, "error": "An internal error occurred"}), 500
    finally:
        db.close()
