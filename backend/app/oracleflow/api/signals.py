"""Signal query API endpoints."""

import logging
from datetime import datetime, timedelta, timezone
from functools import wraps

import requests as http_requests
from flask import g, jsonify, request

logger = logging.getLogger(__name__)
from sqlalchemy import cast, func, select, or_, String, text

from . import signals_bp
from app.oracleflow.auth.utils import decode_token
from app.oracleflow.database import get_session
from app.oracleflow.models.signal import Signal


def optional_auth(f):
    """Extract auth token if present but don't fail on missing token."""
    @wraps(f)
    def decorated(*args, **kwargs):
        g.user_id = None
        g.org_id = None
        g.plan = None
        g.role = None

        auth_header = request.headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            token = auth_header[7:]
            payload = decode_token(token)
            if payload:
                g.user_id = payload['user_id']
                g.org_id = payload['org_id']
                g.plan = payload['plan']
                g.role = payload['role']

        return f(*args, **kwargs)
    return decorated


def _get_db():
    return get_session()


@signals_bp.route('/', methods=['GET'])
@optional_auth
def list_signals():
    """List signals with filtering and pagination.

    If authenticated: show global signals (org_id IS NULL) plus
    org-specific signals (org_id == caller's org).
    If unauthenticated: show only global signals (org_id IS NULL).
    """
    db = _get_db()
    try:
        source = request.args.get('source')
        country_code = request.args.get('country_code')
        category = request.args.get('category')
        categories = request.args.get('categories')
        search = request.args.get('search', '').strip()
        min_anomaly_score = request.args.get('min_anomaly_score', type=float)
        since = request.args.get('since')  # ISO datetime or shorthand: 24h, 7d, 30d
        limit = request.args.get('limit', 50, type=int)
        limit = min(limit, 200)
        offset = request.args.get('offset', 0, type=int)

        # Org-scoping: unauthenticated sees only global; authenticated
        # sees global + own org signals.
        if g.org_id is not None:
            visibility = or_(
                Signal.organization_id.is_(None),
                Signal.organization_id == g.org_id,
            )
        else:
            visibility = Signal.organization_id.is_(None)

        stmt = select(Signal).where(visibility)
        count_stmt = select(func.count()).select_from(Signal).where(visibility)

        if source:
            stmt = stmt.where(Signal.source == source)
            count_stmt = count_stmt.where(Signal.source == source)
        if country_code:
            stmt = stmt.where(Signal.country_code == country_code)
            count_stmt = count_stmt.where(Signal.country_code == country_code)
        if categories:
            cat_list = [c.strip() for c in categories.split(',') if c.strip()]
            cat_filter = Signal.category.in_(cat_list)
            stmt = stmt.where(cat_filter)
            count_stmt = count_stmt.where(cat_filter)
        elif category:
            stmt = stmt.where(Signal.category == category)
            count_stmt = count_stmt.where(Signal.category == category)

        # Full-text keyword search on title and summary
        # For short terms (< 5 chars), use word-boundary matching to avoid
        # substring false positives (e.g. "APT" matching "capture").
        if search:
            if len(search) < 5:
                keyword = f"% {search} %"
                # Also match at start/end of string
                kw_start = f"{search} %"
                kw_end = f"% {search}"
                search_filter = or_(
                    Signal.title.ilike(keyword),
                    Signal.title.ilike(kw_start),
                    Signal.title.ilike(kw_end),
                    Signal.summary.ilike(keyword),
                    Signal.summary.ilike(kw_start),
                    Signal.summary.ilike(kw_end),
                )
            else:
                keyword = f"%{search}%"
                search_filter = or_(
                    Signal.title.ilike(keyword),
                    Signal.summary.ilike(keyword),
                )
            stmt = stmt.where(search_filter)
            count_stmt = count_stmt.where(search_filter)

        # Minimum anomaly score filter
        if min_anomaly_score is not None:
            stmt = stmt.where(Signal.anomaly_score >= min_anomaly_score)
            count_stmt = count_stmt.where(Signal.anomaly_score >= min_anomaly_score)

        # Entity filter: search within raw_data_json for matching entity values.
        # Works on SQLite (cast JSON to text + ILIKE) and PostgreSQL alike.
        entity = request.args.get('entity', '').strip()
        if entity:
            # Search only within the "entities" key of raw_data_json to avoid
            # false positives (e.g. "ETH" matching "Netherlands" in other fields).
            entity_pattern = f"%{entity}%"
            entity_filter = text(
                "cast(raw_data_json->'entities' as text) ILIKE :ep"
            ).bindparams(ep=entity_pattern)
            stmt = stmt.where(entity_filter)
            count_stmt = count_stmt.where(entity_filter)

        # Date range filter (accepts shorthand: "24h", "7d", "30d" or ISO datetime)
        if since:
            since_dt = None
            now = datetime.now(timezone.utc)
            if since == '24h':
                since_dt = now - timedelta(hours=24)
            elif since == '7d':
                since_dt = now - timedelta(days=7)
            elif since == '30d':
                since_dt = now - timedelta(days=30)
            else:
                try:
                    since_dt = datetime.fromisoformat(since)
                except (ValueError, TypeError):
                    pass
            if since_dt:
                stmt = stmt.where(Signal.timestamp >= since_dt)
                count_stmt = count_stmt.where(Signal.timestamp >= since_dt)

        total = db.execute(count_stmt).scalar() or 0

        # Sort parameter support
        sort = request.args.get('sort', 'timestamp')
        if sort == 'anomaly':
            stmt = stmt.order_by(Signal.anomaly_score.desc().nullslast())
        elif sort == 'importance':
            stmt = stmt.order_by(Signal.importance.desc().nullslast())
        else:
            stmt = stmt.order_by(Signal.timestamp.desc().nullslast())
        stmt = stmt.limit(limit).offset(offset)
        result = db.execute(stmt)
        signals = list(result.scalars().all())

        data = []
        for s in signals:
            # Extract source URL from raw_data_json if available
            raw = s.raw_data_json or {}
            source_url = raw.get('link') or raw.get('url') or raw.get('source_url') or ''

            data.append({
                "id": s.id,
                "source": s.source,
                "signal_type": s.signal_type,
                "category": s.category,
                "country_code": s.country_code,
                "title": s.title,
                "summary": s.summary,
                "source_url": source_url,
                "entities": raw.get('entities', {}),
                "sentiment_score": s.sentiment_score,
                "anomaly_score": s.anomaly_score,
                "importance": s.importance,
                "timestamp": s.timestamp.isoformat() if s.timestamp else None,
            })

        return jsonify({"success": True, "data": data, "total": total})
    except Exception as e:
        db.rollback()
        logger.exception("Signals API error: %s", e)
        return jsonify({"success": False, "error": "An internal error occurred"}), 500
    finally:
        db.close()


@signals_bp.route('/<int:signal_id>', methods=['GET'])
@optional_auth
def get_signal(signal_id):
    """Get a single signal by ID."""
    db = _get_db()
    try:
        stmt = select(Signal).where(Signal.id == signal_id)
        result = db.execute(stmt)
        signal = result.scalar_one_or_none()

        if not signal:
            return jsonify({"success": False, "error": f"Signal {signal_id} not found"}), 404

        # If signal belongs to an org, only allow access from that org
        if signal.organization_id is not None and signal.organization_id != g.org_id:
            return jsonify({"success": False, "error": f"Signal {signal_id} not found"}), 404

        data = {
            "id": signal.id,
            "source": signal.source,
            "signal_type": signal.signal_type,
            "category": signal.category,
            "country_code": signal.country_code,
            "title": signal.title,
            "summary": signal.summary,
            "raw_data_json": signal.raw_data_json,
            "sentiment_score": signal.sentiment_score,
            "anomaly_score": signal.anomaly_score,
            "importance": signal.importance,
            "timestamp": signal.timestamp.isoformat() if signal.timestamp else None,
        }

        return jsonify({"success": True, "data": data})
    except Exception as e:
        db.rollback()
        logger.exception("Signals API error: %s", e)
        return jsonify({"success": False, "error": "An internal error occurred"}), 500
    finally:
        db.close()


@signals_bp.route('/displacement', methods=['GET'])
def get_displacement():
    try:
        from app.oracleflow.feeds.displacement import get_displacement_data
        return jsonify({"success": True, "data": get_displacement_data()})
    except Exception as e:
        logger.exception("Signals API error: %s", e)
        return jsonify({"success": False, "error": "An internal error occurred"}), 500


@signals_bp.route('/quotes', methods=['GET'])
def get_quotes():
    try:
        from app.oracleflow.feeds.finnhub_quotes import fetch_stock_quotes, fetch_crypto_quotes
        stocks = fetch_stock_quotes()
        crypto = fetch_crypto_quotes()
        return jsonify({"success": True, "data": {"stocks": stocks, "crypto": crypto}})
    except Exception as e:
        logger.exception("Signals API error: %s", e)
        return jsonify({"success": False, "error": "An internal error occurred"}), 500


@signals_bp.route('/feed-health', methods=['GET'])
def get_feed_health():
    """Return status of data feeds."""
    try:
        from app.oracleflow.feeds.global_feeds import GLOBAL_FEEDS
        db = _get_db()

        # Count signals by source in last 24h
        from datetime import datetime, timezone, timedelta
        since = datetime.now(timezone.utc) - timedelta(hours=24)

        stmt = select(Signal.source, func.count(Signal.id)).where(
            Signal.timestamp >= since
        ).group_by(Signal.source)
        result = db.execute(stmt)
        source_counts = {row[0]: row[1] for row in result}

        total_signals = sum(source_counts.values())

        data = {
            "total_feeds": len(GLOBAL_FEEDS),
            "total_signals_24h": total_signals,
            "by_source": source_counts,
            "feed_categories": {},
        }

        # Count feeds by category
        from collections import Counter
        cat_counts = Counter(cat for _, cat, _ in GLOBAL_FEEDS)
        data["feed_categories"] = dict(cat_counts)

        return jsonify({"success": True, "data": data})
    except Exception as e:
        logger.exception("Signals API error: %s", e)
        return jsonify({"success": False, "error": "An internal error occurred"}), 500


@signals_bp.route('/<int:signal_id>/analyze', methods=['GET', 'POST'])
@optional_auth
def analyze_signal_by_id(signal_id):
    """Convenience route: GET/POST /api/signals/<id>/analyze."""
    return _do_analyze(signal_id)


@signals_bp.route('/analyze', methods=['POST'])
@optional_auth
def analyze_signal():
    """Generate AI impact analysis for a signal (POST with JSON body)."""
    data = request.get_json()
    if not data or not data.get('signal_id'):
        return jsonify({"success": False, "error": "signal_id is required"}), 400

    signal_id = data['signal_id']
    return _do_analyze(signal_id)


def _do_analyze(signal_id):
    """Shared analysis logic used by both endpoint variants."""
    db = _get_db()
    try:
        stmt = select(Signal).where(Signal.id == signal_id)
        result = db.execute(stmt)
        signal = result.scalar_one_or_none()

        if not signal:
            return jsonify({"success": False, "error": "Signal not found"}), 404

        # If signal belongs to an org, only allow access from that org
        if signal.organization_id is not None and signal.organization_id != g.org_id:
            return jsonify({"success": False, "error": "Signal not found"}), 404

        # Build context from related signals (same category, last 24h)
        cutoff_24h = datetime.now(timezone.utc) - timedelta(hours=24)
        related_stmt = (
            select(Signal)
            .where(
                Signal.category == signal.category,
                Signal.timestamp >= cutoff_24h,
            )
            .order_by(Signal.anomaly_score.desc())
            .limit(10)
        )
        related_result = db.execute(related_stmt)
        related = list(related_result.scalars().all())

        related_text = "\n".join(
            f"- {s.title} (anomaly: {s.anomaly_score:.0%})" for s in related
        )

        prompt = f"""You are an intelligence analyst. Analyze this signal and predict its impact:

Signal: {signal.title}
Category: {signal.category}
Anomaly Score: {signal.anomaly_score:.0%}
Summary: {signal.summary or 'N/A'}

Related signals in the same category (last 24h):
{related_text}

Provide your analysis in EXACTLY this format (keep each section concise):

1. IMPACT ASSESSMENT: What is the likely impact? (1 paragraph)
2. PROBABILITY: How likely is escalation? (give a percentage, e.g. 65%)
3. TIMELINE: When will effects be felt? (hours/days/weeks)
4. AFFECTED SECTORS: Which sectors/markets/regions are affected? (comma-separated list)
5. RECOMMENDED ACTIONS: What should an analyst do? (numbered list, 3-5 items)
"""

        from app.config import Config
        api_key = Config.LLM_API_KEY
        base_url = Config.LLM_BASE_URL
        model = Config.LLM_MODEL_NAME

        resp = http_requests.post(
            f"{base_url}/chat/completions",
            json={
                "model": model,
                "messages": [
                    {"role": "system", "content": "You are a senior intelligence analyst producing classified impact assessments."},
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.3,
            },
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=30,
        )
        resp.raise_for_status()
        analysis_text = resp.json()["choices"][0]["message"]["content"]

        return jsonify({
            "success": True,
            "data": {
                "signal_id": signal.id,
                "signal_title": signal.title,
                "analysis": analysis_text,
                "related_count": len(related),
            }
        })
    except http_requests.exceptions.RequestException as e:
        logger.error("LLM request failed for signal %s: %s", signal_id, e)
        return jsonify({"success": False, "error": "Analysis service unavailable"}), 503
    except Exception as e:
        db.rollback()
        logger.exception("Signals API error: %s", e)
        return jsonify({"success": False, "error": "An internal error occurred"}), 500
    finally:
        db.close()
