"""Country registry, risk, and AI intelligence brief endpoints."""

import logging
import os
import time
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from functools import wraps

import requests as http_requests
from flask import jsonify, request
from sqlalchemy import select

_rate_limits = defaultdict(list)


def rate_limit(max_calls=10, window=60):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            key = request.remote_addr
            now = time.time()
            _rate_limits[key] = [t for t in _rate_limits[key] if now - t < window]
            if len(_rate_limits[key]) >= max_calls:
                return jsonify({"success": False, "error": "Rate limit exceeded"}), 429
            _rate_limits[key].append(now)
            return f(*args, **kwargs)
        return decorated
    return decorator

from sqlalchemy import func as sa_func

from . import countries_bp
from app.oracleflow.database import get_session
from app.oracleflow.models.signal import Signal
from app.oracleflow.registry.loader import RegistryLoader

logger = logging.getLogger(__name__)

# Module-level loader instance (caches configs after first load)
_registry = RegistryLoader()


def _get_db():
    return get_session()


@countries_bp.route('/', methods=['GET'])
def list_countries():
    """List all countries from the registry."""
    try:
        configs = _registry.list_countries()
        data = []
        for c in configs:
            data.append({
                "code": c.code,
                "country": c.country,
                "region": c.region,
                "languages": c.languages,
                "timezone": c.timezone,
            })

        return jsonify({"success": True, "data": data, "total": len(data)})
    except Exception as e:
        logger.exception("Countries API error: %s", e)
        return jsonify({"success": False, "error": "An internal error occurred"}), 500


@countries_bp.route('/<code>', methods=['GET'])
def get_country(code):
    """Get full country config from registry."""
    try:
        config = _registry.get_country(code)
        if not config:
            return jsonify({"success": False, "error": f"Country {code} not found"}), 404

        data = config.model_dump()
        return jsonify({"success": True, "data": data})
    except Exception as e:
        logger.exception("Countries API error: %s", e)
        return jsonify({"success": False, "error": "An internal error occurred"}), 500


@countries_bp.route('/<code>/risk', methods=['GET'])
def get_country_risk(code):
    """Compute country risk from signals -- average anomaly scores by category."""
    db = _get_db()
    try:
        config = _registry.get_country(code)
        if not config:
            return jsonify({"success": False, "error": f"Country {code} not found"}), 404

        country_code = config.code
        stmt = (
            select(Signal)
            .where(Signal.country_code == country_code)
            .order_by(Signal.timestamp.desc())
            .limit(500)
        )
        result = db.execute(stmt)
        signals = list(result.scalars().all())

        if not signals:
            return jsonify({
                "success": True,
                "data": {
                    "country_code": country_code,
                    "overall_risk": 0.0,
                    "category_risk": {},
                    "signal_count": 0,
                }
            })

        # Group by category and compute average anomaly score
        category_scores: dict[str, list[float]] = defaultdict(list)
        for s in signals:
            category_scores[s.category].append(s.anomaly_score)

        category_risk = {}
        for cat, scores in category_scores.items():
            category_risk[cat] = round(sum(scores) / len(scores), 4) if scores else 0.0

        overall_risk = round(
            sum(s.anomaly_score for s in signals) / len(signals), 4
        )

        data = {
            "country_code": country_code,
            "overall_risk": overall_risk,
            "category_risk": category_risk,
            "signal_count": len(signals),
        }

        return jsonify({"success": True, "data": data})
    except Exception as e:
        db.rollback()
        logger.exception("Countries API error: %s", e)
        return jsonify({"success": False, "error": "An internal error occurred"}), 500
    finally:
        db.close()


@countries_bp.route('/<code>/trend', methods=['GET'])
def get_country_trend(code):
    """Return daily risk score trend for a country over the last N days."""
    db = _get_db()
    try:
        config = _registry.get_country(code)
        if not config:
            return jsonify({"success": False, "error": f"Country {code} not found"}), 404

        days = request.args.get('days', 30, type=int)
        days = min(days, 365)
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        country_code = config.code

        # Query signals grouped by date
        date_expr = sa_func.date(Signal.timestamp)
        stmt = (
            select(
                date_expr.label('day'),
                sa_func.avg(Signal.anomaly_score).label('avg_score'),
                sa_func.count(Signal.id).label('signal_count'),
            )
            .where(
                Signal.country_code == country_code,
                Signal.timestamp >= cutoff,
            )
            .group_by(date_expr)
            .order_by(date_expr)
        )

        result = db.execute(stmt)
        rows = result.all()

        data = []
        for row in rows:
            data.append({
                "date": str(row.day),
                "score": round(float(row.avg_score), 4) if row.avg_score else 0.0,
                "count": row.signal_count,
            })

        return jsonify({"success": True, "data": data, "country_code": country_code, "days": days})
    except Exception as e:
        db.rollback()
        logger.exception("Countries API error: %s", e)
        return jsonify({"success": False, "error": "An internal error occurred"}), 500
    finally:
        db.close()


@countries_bp.route('/<code>/brief', methods=['GET'])
@rate_limit(max_calls=10, window=60)
def get_country_brief(code):
    """Generate an AI intelligence brief for a country (or global) from recent signals."""
    db = _get_db()
    try:
        is_global = code.upper() == 'GLOBAL'

        if is_global:
            country_name = "Global"
            # Fetch top 30 signals across ALL countries by anomaly score
            stmt = (
                select(Signal)
                .order_by(Signal.anomaly_score.desc())
                .limit(30)
            )
        else:
            config = _registry.get_country(code)
            country_name = config.country if config else code
            # Get recent signals for this country
            stmt = (
                select(Signal)
                .where(Signal.country_code == code.upper())
                .order_by(Signal.timestamp.desc())
                .limit(20)
            )

        result = db.execute(stmt)
        signals = list(result.scalars().all())

        if not signals:
            return jsonify({
                "success": True,
                "data": {
                    "country_code": code,
                    "country_name": country_name,
                    "brief": f"No intelligence signals available for {country_name}. Add monitoring sites or wait for feed ingestion.",
                    "signal_count": 0,
                }
            })

        # Build signal summary for LLM
        signals_text = ""
        for s in signals:
            signals_text += f"- [{s.category}] {s.title} (anomaly:{s.anomaly_score:.0%}, sentiment:{s.sentiment_score:.0%})\n"
            if s.summary:
                signals_text += f"  {s.summary[:150]}\n"

        if is_global:
            prompt = f"""You are a senior geopolitical intelligence analyst. Write a global intelligence brief covering the world situation based on these signals.

SIGNALS:
{signals_text}

Write a 3-paragraph intelligence brief covering:
1. Current Situation — what is happening across the world right now
2. Key Risks — top global risks, numbered list
3. Outlook — what to watch for next

Format: Professional intelligence briefing style. Be specific. Reference the signals. Keep it under 400 words."""
        else:
            prompt = f"""You are a senior geopolitical intelligence analyst. Write a concise intelligence brief for {country_name} based on these signals from the last 24 hours.

SIGNALS:
{signals_text}

Write a 3-paragraph intelligence brief covering:
1. Current Situation — what is happening right now
2. Key Risks — what could go wrong, numbered list
3. Outlook — what to watch for next

Format: Professional intelligence briefing style. Be specific. Reference the signals. Keep it under 400 words."""

        from app.config import Config
        api_key = Config.LLM_API_KEY
        base_url = Config.LLM_BASE_URL
        model = Config.LLM_MODEL_NAME

        resp = http_requests.post(
            f"{base_url}/chat/completions",
            json={
                "model": model,
                "messages": [
                    {"role": "system", "content": "You are a senior intelligence analyst writing classified briefings."},
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.3,
            },
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=30,
        )
        resp.raise_for_status()
        brief = resp.json()["choices"][0]["message"]["content"]

        return jsonify({
            "success": True,
            "data": {
                "country_code": code,
                "country_name": country_name,
                "brief": brief,
                "signal_count": len(signals),
            }
        })
    except Exception as e:
        logger.error("Brief generation failed for %s: %s", code, e)
        logger.exception("Countries API error: %s", e)
        return jsonify({"success": False, "error": "An internal error occurred"}), 500
    finally:
        db.close()
