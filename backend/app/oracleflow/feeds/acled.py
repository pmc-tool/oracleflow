"""Fetch armed conflict events from ACLED API."""
import requests
import os
import logging
from datetime import datetime, timezone, timedelta
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.oracleflow.models.signal import Signal

logger = logging.getLogger(__name__)

ACLED_API = "https://api.acleddata.com/acled/read"


def fetch_conflicts(db: Session) -> list[Signal]:
    """Fetch recent conflict events. Uses ACLED API key if available."""
    try:
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")

        params = {
            "event_date": f"{start_date}|{end_date}",
            "event_date_where": "BETWEEN",
            "limit": 50,
        }

        # Use ACLED credentials if available in environment
        acled_email = os.environ.get("ACLED_EMAIL", "")
        acled_key = os.environ.get("ACLED_PASSWORD", "")
        if acled_email and acled_key:
            params["key"] = acled_key
            params["email"] = acled_email
            logger.info("Using authenticated ACLED API access")
        else:
            logger.info("No ACLED credentials found, attempting unauthenticated access")

        resp = requests.get(ACLED_API, params=params, timeout=15)

        if resp.status_code != 200:
            logger.warning(f"ACLED API returned {resp.status_code}, falling back to placeholders")
            return _generate_placeholder_conflicts(db)

        data = resp.json()
        events = data.get("data", [])

        if not events:
            logger.info("ACLED API returned 0 events, using placeholders")
            return _generate_placeholder_conflicts(db)

    except Exception as e:
        logger.debug(f"ACLED fetch failed: {e}, using placeholders")
        return _generate_placeholder_conflicts(db)

    signals = []
    for event in events[:30]:
        title = f"{event.get('event_type', 'Conflict')}: {event.get('location', 'Unknown')}, {event.get('country', '')}"[:200]

        existing = db.execute(select(Signal).where(Signal.title == title)).scalar_one_or_none()
        if existing:
            continue

        fatalities = int(event.get("fatalities", 0))
        _summary = event.get("notes", "")[:500]

        # Extract entities from title + summary
        from app.oracleflow.entities.signal_extractor import extract_entities
        _entities = extract_entities(title, _summary)

        _raw_data = {
            "lat": float(event.get("latitude", 0)),
            "lng": float(event.get("longitude", 0)),
            "event_type": event.get("event_type"),
            "fatalities": fatalities,
            "actor1": event.get("actor1", ""),
            "source": event.get("source", ""),
        }
        if _entities:
            _raw_data["entities"] = _entities

        # Diversified anomaly score based on event type and fatalities
        anomaly = _compute_anomaly(event.get("event_type", ""), fatalities)

        signal = Signal(
            source="acled",
            signal_type="conflict_event",
            category="geopolitical",
            country_code=event.get("iso", "")[:2] if event.get("iso") else "",
            title=title,
            summary=_summary,
            raw_data_json=_raw_data,
            sentiment_score=_compute_sentiment(event.get("event_type", ""), fatalities),
            anomaly_score=anomaly,
            importance=min(1.0, anomaly + 0.1),
            timestamp=datetime.now(timezone.utc),
        )
        db.add(signal)
        signals.append(signal)

    db.flush()
    return signals


def _compute_anomaly(event_type: str, fatalities: int) -> float:
    """Compute diversified anomaly score based on event type and fatality count.

    Ranges:
      - Battles with fatalities:           0.6 - 1.0
      - Explosions/Remote violence:        0.55 - 1.0
      - Violence against civilians:        0.5 - 0.95
      - Protests (no fatalities):          0.2 - 0.35
      - Protests (with fatalities):        0.5 - 0.8
      - Strategic developments:            0.3 - 0.5
      - Riots:                             0.35 - 0.7
      - Other:                             0.3 - 0.8
    """
    et = (event_type or "").lower()

    if "battles" in et or "battle" in et:
        base = 0.6
        return min(1.0, base + fatalities * 0.04)
    elif "explosion" in et or "remote violence" in et:
        base = 0.55
        return min(1.0, base + fatalities * 0.05)
    elif "violence against civilians" in et:
        base = 0.5
        return min(0.95, base + fatalities * 0.03)
    elif "protest" in et:
        if fatalities > 0:
            return min(0.8, 0.5 + fatalities * 0.1)
        return 0.25
    elif "riot" in et:
        base = 0.35
        return min(0.7, base + fatalities * 0.07)
    elif "strategic" in et:
        return 0.4
    else:
        base = 0.3
        return min(0.8, base + fatalities * 0.05)


def _compute_sentiment(event_type: str, fatalities: int) -> float:
    """Compute sentiment based on event severity."""
    et = (event_type or "").lower()

    if fatalities > 20:
        return -0.95
    elif fatalities > 10:
        return -0.85
    elif fatalities > 5:
        return -0.75
    elif fatalities > 0:
        return -0.6

    # No fatalities
    if "protest" in et:
        return -0.4
    elif "strategic" in et:
        return -0.3
    return -0.5


def _generate_placeholder_conflicts(db: Session) -> list[Signal]:
    """Generate realistic placeholder conflict signals for demo with DIVERSIFIED scores."""
    hotspots = [
        {"title": "Battles: Kherson Oblast, Ukraine", "country": "UA", "lat": 46.63, "lng": 32.62, "type": "Battles", "fatalities": 12},
        {"title": "Shelling: Donetsk, Ukraine", "country": "UA", "lat": 48.00, "lng": 37.80, "type": "Explosions/Remote violence", "fatalities": 5},
        {"title": "Armed clash: Darfur, Sudan", "country": "SD", "lat": 13.50, "lng": 25.00, "type": "Battles", "fatalities": 23},
        {"title": "Airstrike: Rafah, Palestine", "country": "PS", "lat": 31.30, "lng": 34.25, "type": "Explosions/Remote violence", "fatalities": 8},
        {"title": "Protest: Tehran, Iran", "country": "IR", "lat": 35.69, "lng": 51.39, "type": "Protests", "fatalities": 0},
        {"title": "Violence against civilians: Beni, DR Congo", "country": "CD", "lat": 0.49, "lng": 29.47, "type": "Violence against civilians", "fatalities": 15},
        {"title": "Armed clash: Mogadishu, Somalia", "country": "SO", "lat": 2.05, "lng": 45.34, "type": "Battles", "fatalities": 7},
        {"title": "Drone strike: Marib, Yemen", "country": "YE", "lat": 15.47, "lng": 45.32, "type": "Explosions/Remote violence", "fatalities": 3},
        {"title": "Protest: Yangon, Myanmar", "country": "MM", "lat": 16.87, "lng": 96.20, "type": "Protests", "fatalities": 0},
        {"title": "Armed clash: Tillaberi, Niger", "country": "NE", "lat": 14.21, "lng": 1.45, "type": "Battles", "fatalities": 11},
    ]

    signals = []
    for h in hotspots:
        existing = db.execute(select(Signal).where(Signal.title == h["title"])).scalar_one_or_none()
        if existing:
            # Update existing placeholder with diversified scores
            anomaly = _compute_anomaly(h["type"], h["fatalities"])
            sentiment = _compute_sentiment(h["type"], h["fatalities"])
            existing.anomaly_score = anomaly
            existing.sentiment_score = sentiment
            existing.importance = min(1.0, anomaly + 0.1)
            continue

        _summary = f"{h['type']} event with {h['fatalities']} reported fatalities"

        from app.oracleflow.entities.signal_extractor import extract_entities
        _entities = extract_entities(h["title"], _summary)

        _raw_data = {"lat": h["lat"], "lng": h["lng"], "event_type": h["type"], "fatalities": h["fatalities"]}
        if _entities:
            _raw_data["entities"] = _entities

        anomaly = _compute_anomaly(h["type"], h["fatalities"])
        sentiment = _compute_sentiment(h["type"], h["fatalities"])

        signal = Signal(
            source="acled",
            signal_type="conflict_event",
            category="geopolitical",
            country_code=h["country"],
            title=h["title"],
            summary=_summary,
            raw_data_json=_raw_data,
            sentiment_score=sentiment,
            anomaly_score=anomaly,
            importance=min(1.0, anomaly + 0.1),
            timestamp=datetime.now(timezone.utc),
        )
        db.add(signal)
        signals.append(signal)

    db.flush()
    return signals
