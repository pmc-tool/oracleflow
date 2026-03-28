"""Watchlist API endpoints — personalized monitoring for organizations, people, topics."""

import logging
from datetime import datetime, timezone
from urllib.parse import quote_plus

from flask import g, jsonify, request
from sqlalchemy import and_, func, or_, select, cast, Date

from . import watchlist_bp
from app.oracleflow.auth.middleware import require_auth
from app.oracleflow.database import get_session
from app.oracleflow.models.signal import Signal, AlertRuleDB
from app.oracleflow.models.watchlist import WatchlistItem

logger = logging.getLogger(__name__)

# Country code -> country name for Google News RSS URL generation
_COUNTRY_NAMES = {
    "BD": "Bangladesh", "PK": "Pakistan", "IN": "India", "US": "United States",
    "GB": "United Kingdom", "DE": "Germany", "FR": "France", "CN": "China",
    "RU": "Russia", "JP": "Japan", "KR": "South Korea", "AU": "Australia",
    "CA": "Canada", "BR": "Brazil", "MX": "Mexico", "AR": "Argentina",
    "CL": "Chile", "CO": "Colombia", "ZA": "South Africa", "NG": "Nigeria",
    "KE": "Kenya", "EG": "Egypt", "SA": "Saudi Arabia", "AE": "UAE",
    "IL": "Israel", "IR": "Iran", "IQ": "Iraq", "SY": "Syria",
    "TR": "Turkey", "UA": "Ukraine", "PL": "Poland", "AF": "Afghanistan",
    "MM": "Myanmar", "TH": "Thailand", "VN": "Vietnam", "ID": "Indonesia",
    "PH": "Philippines", "MY": "Malaysia", "SG": "Singapore", "TW": "Taiwan",
    "NZ": "New Zealand", "SE": "Sweden", "NO": "Norway", "CH": "Switzerland",
    "IT": "Italy", "ES": "Spain", "NL": "Netherlands", "JM": "Jamaica",
    "TT": "Trinidad and Tobago", "BB": "Barbados",
}

VALID_ITEM_TYPES = {"organization", "person", "topic", "competitor", "location"}


def _get_db():
    return get_session()


def _generate_google_news_rss(name: str, country_code: str | None = None) -> str:
    """Build a Google News RSS search URL for the watchlist item."""
    query = f'"{name}"'
    if country_code and country_code in _COUNTRY_NAMES:
        query += f" {_COUNTRY_NAMES[country_code]}"
    return f"https://news.google.com/rss/search?q={quote_plus(query)}&hl=en"


def _build_keyword_filter(keywords: list[str]):
    """Build an OR filter matching any keyword in Signal title or summary."""
    conditions = []
    for kw in keywords:
        pattern = f"%{kw}%"
        conditions.append(Signal.title.ilike(pattern))
        conditions.append(Signal.summary.ilike(pattern))
    return or_(*conditions) if conditions else None


def _serialize_item(item: WatchlistItem, signal_count: int = 0) -> dict:
    """Serialize a WatchlistItem to a JSON-safe dict."""
    return {
        "id": item.id,
        "user_id": item.user_id,
        "organization_id": item.organization_id,
        "name": item.name,
        "item_type": item.item_type,
        "country_code": item.country_code,
        "keywords": item.keywords or [],
        "google_news_rss": item.google_news_rss,
        "websites": item.websites or [],
        "social_links": item.social_links or {},
        "is_active": item.is_active,
        "signal_count": signal_count,
        "created_at": item.created_at.isoformat() if item.created_at else None,
        "updated_at": item.updated_at.isoformat() if item.updated_at else None,
    }


def _serialize_signal(s: Signal) -> dict:
    """Serialize a Signal to a JSON-safe dict with source URL and entities."""
    raw = s.raw_data_json or {}
    source_url = raw.get("link") or raw.get("url") or raw.get("source_url") or ""
    return {
        "id": s.id,
        "source": s.source,
        "signal_type": s.signal_type,
        "category": s.category,
        "country_code": s.country_code,
        "title": s.title,
        "summary": s.summary,
        "source_url": source_url,
        "entities": raw.get("entities", {}),
        "sentiment_score": s.sentiment_score,
        "anomaly_score": s.anomaly_score,
        "importance": s.importance,
        "timestamp": s.timestamp.isoformat() if s.timestamp else None,
    }


# ---------------------------------------------------------------------------
# POST /api/watchlist/ — Create a watchlist item
# ---------------------------------------------------------------------------
@watchlist_bp.route("/", methods=["POST"])
@require_auth
def create_watchlist_item():
    """Create a new watchlist item with auto-generated keywords and RSS URL."""
    db = _get_db()
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "Request body required"}), 400

        name = (data.get("name") or "").strip()
        item_type = (data.get("item_type") or "").strip()

        if not name:
            return jsonify({"success": False, "error": "name is required"}), 400
        if item_type not in VALID_ITEM_TYPES:
            return jsonify({
                "success": False,
                "error": f"item_type must be one of: {', '.join(sorted(VALID_ITEM_TYPES))}",
            }), 400

        country_code = (data.get("country_code") or "").strip().upper() or None
        keywords = data.get("keywords") or [name, name.lower()]
        # Deduplicate keywords while preserving order
        seen = set()
        unique_keywords = []
        for kw in keywords:
            kw_lower = kw.lower()
            if kw_lower not in seen:
                seen.add(kw_lower)
                unique_keywords.append(kw)
        keywords = unique_keywords

        google_news_rss = _generate_google_news_rss(name, country_code)
        websites = data.get("websites") or []
        social_links = data.get("social_links") or {}

        item = WatchlistItem(
            user_id=g.user_id,
            organization_id=g.org_id,
            name=name,
            item_type=item_type,
            country_code=country_code,
            keywords=keywords,
            google_news_rss=google_news_rss,
            websites=websites,
            social_links=social_links,
        )
        db.add(item)
        db.flush()

        # Auto-create a keyword alert rule for this watchlist item
        alert_rule = AlertRuleDB(
            user_id=g.user_id,
            organization_id=g.org_id,
            name=f"Watchlist: {name}",
            condition_type="keyword_match",
            threshold=0.0,
            keywords_json=keywords,
            country_codes_json=[country_code] if country_code else [],
            severity="medium",
            channels_json=["in_app"],
            enabled=True,
        )
        db.add(alert_rule)
        db.commit()

        return jsonify({"success": True, "data": _serialize_item(item)}), 201

    except Exception as e:
        db.rollback()
        logger.exception("Watchlist create error: %s", e)
        return jsonify({"success": False, "error": "An internal error occurred"}), 500
    finally:
        db.close()


# ---------------------------------------------------------------------------
# GET /api/watchlist/ — List user's watchlist items with signal counts
# ---------------------------------------------------------------------------
@watchlist_bp.route("/", methods=["GET"])
@require_auth
def list_watchlist_items():
    """Return the authenticated user's active watchlist items sorted by signal count."""
    db = _get_db()
    try:
        stmt = (
            select(WatchlistItem)
            .where(
                WatchlistItem.user_id == g.user_id,
                WatchlistItem.is_active == 1,
            )
        )
        items = list(db.execute(stmt).scalars().all())

        results = []
        for item in items:
            kw_filter = _build_keyword_filter(item.keywords or [])
            if kw_filter is not None:
                count = db.execute(
                    select(func.count()).select_from(Signal).where(kw_filter)
                ).scalar() or 0
            else:
                count = 0
            results.append((item, count))

        # Sort by signal count descending
        results.sort(key=lambda x: x[1], reverse=True)

        data = [_serialize_item(item, count) for item, count in results]
        return jsonify({"success": True, "data": data, "total": len(data)})

    except Exception as e:
        db.rollback()
        logger.exception("Watchlist list error: %s", e)
        return jsonify({"success": False, "error": "An internal error occurred"}), 500
    finally:
        db.close()


# ---------------------------------------------------------------------------
# GET /api/watchlist/<id> — Get single item with recent matching signals
# ---------------------------------------------------------------------------
@watchlist_bp.route("/<int:item_id>", methods=["GET"])
@require_auth
def get_watchlist_item(item_id):
    """Return a single watchlist item with the 20 most recent matching signals."""
    db = _get_db()
    try:
        item = db.execute(
            select(WatchlistItem).where(
                WatchlistItem.id == item_id,
                WatchlistItem.user_id == g.user_id,
            )
        ).scalar_one_or_none()

        if not item:
            return jsonify({"success": False, "error": "Watchlist item not found"}), 404

        # Fetch recent matching signals
        kw_filter = _build_keyword_filter(item.keywords or [])
        signals = []
        signal_count = 0
        if kw_filter is not None:
            signal_count = db.execute(
                select(func.count()).select_from(Signal).where(kw_filter)
            ).scalar() or 0

            sig_stmt = (
                select(Signal)
                .where(kw_filter)
                .order_by(Signal.timestamp.desc().nullslast())
                .limit(20)
            )
            signals = list(db.execute(sig_stmt).scalars().all())

        data = _serialize_item(item, signal_count)
        data["signals"] = [_serialize_signal(s) for s in signals]

        return jsonify({"success": True, "data": data})

    except Exception as e:
        db.rollback()
        logger.exception("Watchlist get error: %s", e)
        return jsonify({"success": False, "error": "An internal error occurred"}), 500
    finally:
        db.close()


# ---------------------------------------------------------------------------
# PUT /api/watchlist/<id> — Update a watchlist item
# ---------------------------------------------------------------------------
@watchlist_bp.route("/<int:item_id>", methods=["PUT"])
@require_auth
def update_watchlist_item(item_id):
    """Update fields of an existing watchlist item."""
    db = _get_db()
    try:
        item = db.execute(
            select(WatchlistItem).where(
                WatchlistItem.id == item_id,
                WatchlistItem.user_id == g.user_id,
            )
        ).scalar_one_or_none()

        if not item:
            return jsonify({"success": False, "error": "Watchlist item not found"}), 404

        data = request.get_json() or {}

        if "name" in data:
            item.name = data["name"].strip()
        if "item_type" in data:
            if data["item_type"] not in VALID_ITEM_TYPES:
                return jsonify({
                    "success": False,
                    "error": f"item_type must be one of: {', '.join(sorted(VALID_ITEM_TYPES))}",
                }), 400
            item.item_type = data["item_type"]
        if "country_code" in data:
            item.country_code = (data["country_code"] or "").strip().upper() or None
        if "keywords" in data:
            item.keywords = data["keywords"]
        if "websites" in data:
            item.websites = data["websites"]
        if "social_links" in data:
            item.social_links = data["social_links"]

        # Regenerate Google News RSS if name or country_code changed
        if "name" in data or "country_code" in data:
            item.google_news_rss = _generate_google_news_rss(
                item.name, item.country_code
            )

        item.updated_at = datetime.now(timezone.utc)
        db.commit()

        return jsonify({"success": True, "data": _serialize_item(item)})

    except Exception as e:
        db.rollback()
        logger.exception("Watchlist update error: %s", e)
        return jsonify({"success": False, "error": "An internal error occurred"}), 500
    finally:
        db.close()


# ---------------------------------------------------------------------------
# DELETE /api/watchlist/<id> — Soft delete (set is_active=0)
# ---------------------------------------------------------------------------
@watchlist_bp.route("/<int:item_id>", methods=["DELETE"])
@require_auth
def delete_watchlist_item(item_id):
    """Soft-delete a watchlist item by setting is_active=0."""
    db = _get_db()
    try:
        item = db.execute(
            select(WatchlistItem).where(
                WatchlistItem.id == item_id,
                WatchlistItem.user_id == g.user_id,
            )
        ).scalar_one_or_none()

        if not item:
            return jsonify({"success": False, "error": "Watchlist item not found"}), 404

        item.is_active = 0
        item.updated_at = datetime.now(timezone.utc)
        db.commit()

        return jsonify({"success": True, "message": "Watchlist item deleted"})

    except Exception as e:
        db.rollback()
        logger.exception("Watchlist delete error: %s", e)
        return jsonify({"success": False, "error": "An internal error occurred"}), 500
    finally:
        db.close()


# ---------------------------------------------------------------------------
# GET /api/watchlist/<id>/signals — Signals matching this watchlist item
# ---------------------------------------------------------------------------
@watchlist_bp.route("/<int:item_id>/signals", methods=["GET"])
@require_auth
def get_watchlist_signals(item_id):
    """Return paginated signals matching a watchlist item's keywords."""
    db = _get_db()
    try:
        item = db.execute(
            select(WatchlistItem).where(
                WatchlistItem.id == item_id,
                WatchlistItem.user_id == g.user_id,
            )
        ).scalar_one_or_none()

        if not item:
            return jsonify({"success": False, "error": "Watchlist item not found"}), 404

        limit = min(request.args.get("limit", 50, type=int), 200)
        offset = request.args.get("offset", 0, type=int)
        sort = request.args.get("sort", "timestamp")

        kw_filter = _build_keyword_filter(item.keywords or [])
        if kw_filter is None:
            return jsonify({"success": True, "data": [], "total": 0})

        count_stmt = select(func.count()).select_from(Signal).where(kw_filter)
        total = db.execute(count_stmt).scalar() or 0

        stmt = select(Signal).where(kw_filter)

        if sort == "anomaly":
            stmt = stmt.order_by(Signal.anomaly_score.desc().nullslast())
        elif sort == "importance":
            stmt = stmt.order_by(Signal.importance.desc().nullslast())
        elif sort == "sentiment":
            stmt = stmt.order_by(Signal.sentiment_score.desc().nullslast())
        else:
            stmt = stmt.order_by(Signal.timestamp.desc().nullslast())

        stmt = stmt.limit(limit).offset(offset)
        signals = list(db.execute(stmt).scalars().all())

        data = [_serialize_signal(s) for s in signals]
        return jsonify({"success": True, "data": data, "total": total})

    except Exception as e:
        db.rollback()
        logger.exception("Watchlist signals error: %s", e)
        return jsonify({"success": False, "error": "An internal error occurred"}), 500
    finally:
        db.close()


# ---------------------------------------------------------------------------
# GET /api/watchlist/<id>/sentiment — Sentiment over time
# ---------------------------------------------------------------------------
@watchlist_bp.route("/<int:item_id>/sentiment", methods=["GET"])
@require_auth
def get_watchlist_sentiment(item_id):
    """Return daily sentiment averages and signal counts for a watchlist item."""
    db = _get_db()
    try:
        item = db.execute(
            select(WatchlistItem).where(
                WatchlistItem.id == item_id,
                WatchlistItem.user_id == g.user_id,
            )
        ).scalar_one_or_none()

        if not item:
            return jsonify({"success": False, "error": "Watchlist item not found"}), 404

        kw_filter = _build_keyword_filter(item.keywords or [])
        if kw_filter is None:
            return jsonify({"success": True, "data": []})

        stmt = (
            select(
                cast(Signal.timestamp, Date).label("date"),
                func.avg(Signal.sentiment_score).label("avg_sentiment"),
                func.count(Signal.id).label("signal_count"),
            )
            .where(kw_filter)
            .group_by(cast(Signal.timestamp, Date))
            .order_by(cast(Signal.timestamp, Date).asc())
        )
        rows = db.execute(stmt).all()

        data = [
            {
                "date": row.date.isoformat() if row.date else None,
                "avg_sentiment": round(float(row.avg_sentiment or 0), 3),
                "signal_count": row.signal_count,
            }
            for row in rows
        ]
        return jsonify({"success": True, "data": data})

    except Exception as e:
        db.rollback()
        logger.exception("Watchlist sentiment error: %s", e)
        return jsonify({"success": False, "error": "An internal error occurred"}), 500
    finally:
        db.close()


# ---------------------------------------------------------------------------
# GET /api/watchlist/compare — Compare signal counts across watchlist items
# ---------------------------------------------------------------------------
@watchlist_bp.route("/compare", methods=["GET"])
@require_auth
def compare_watchlist_items():
    """Return signal counts and average sentiment for all active watchlist items."""
    db = _get_db()
    try:
        stmt = (
            select(WatchlistItem)
            .where(
                WatchlistItem.user_id == g.user_id,
                WatchlistItem.is_active == 1,
            )
        )
        items = list(db.execute(stmt).scalars().all())

        data = []
        for item in items:
            kw_filter = _build_keyword_filter(item.keywords or [])
            if kw_filter is None:
                data.append({
                    "id": item.id,
                    "name": item.name,
                    "item_type": item.item_type,
                    "signal_count": 0,
                    "avg_sentiment": 0.0,
                    "trend": "stable",
                })
                continue

            stats = db.execute(
                select(
                    func.count(Signal.id).label("signal_count"),
                    func.avg(Signal.sentiment_score).label("avg_sentiment"),
                ).where(kw_filter)
            ).one()

            signal_count = stats.signal_count or 0
            avg_sentiment = round(float(stats.avg_sentiment or 0), 3)

            # Determine trend: compare last 7 days vs previous 7 days
            from datetime import timedelta

            now = datetime.now(timezone.utc)
            recent_cutoff = now - timedelta(days=7)
            older_cutoff = now - timedelta(days=14)

            recent_count = db.execute(
                select(func.count()).select_from(Signal).where(
                    kw_filter,
                    Signal.timestamp >= recent_cutoff,
                )
            ).scalar() or 0

            older_count = db.execute(
                select(func.count()).select_from(Signal).where(
                    kw_filter,
                    Signal.timestamp >= older_cutoff,
                    Signal.timestamp < recent_cutoff,
                )
            ).scalar() or 0

            if older_count == 0:
                trend = "rising" if recent_count > 0 else "stable"
            elif recent_count > older_count * 1.2:
                trend = "rising"
            elif recent_count < older_count * 0.8:
                trend = "declining"
            else:
                trend = "stable"

            data.append({
                "id": item.id,
                "name": item.name,
                "item_type": item.item_type,
                "signal_count": signal_count,
                "avg_sentiment": avg_sentiment,
                "trend": trend,
            })

        return jsonify({"success": True, "data": data})

    except Exception as e:
        db.rollback()
        logger.exception("Watchlist compare error: %s", e)
        return jsonify({"success": False, "error": "An internal error occurred"}), 500
    finally:
        db.close()
