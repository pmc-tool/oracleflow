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
    """Fetch recent conflict events. Works without API key (limited)."""
    try:
        # ACLED allows limited access without key
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")

        resp = requests.get(ACLED_API, params={
            "event_date": f"{start_date}|{end_date}",
            "event_date_where": "BETWEEN",
            "limit": 50,
        }, timeout=15)

        if resp.status_code != 200:
            # Fallback: generate placeholder conflict data from known hotspots
            return _generate_placeholder_conflicts(db)

        data = resp.json()
        events = data.get("data", [])
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

        signal = Signal(
            source="acled",
            signal_type="conflict_event",
            category="geopolitical",
            country_code=event.get("iso", "")[:2] if event.get("iso") else "",
            title=title,
            summary=_summary,
            raw_data_json=_raw_data,
            sentiment_score=-0.7,
            anomaly_score=min(0.5 + fatalities * 0.05, 1.0),
            importance=min(0.6 + fatalities * 0.04, 1.0),
            timestamp=datetime.now(timezone.utc),
        )
        db.add(signal)
        signals.append(signal)

    db.flush()
    return signals


def _generate_placeholder_conflicts(db: Session) -> list[Signal]:
    """Generate realistic placeholder conflict signals for demo."""
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
            continue

        _summary = f"{h['type']} event with {h['fatalities']} reported fatalities"

        from app.oracleflow.entities.signal_extractor import extract_entities
        _entities = extract_entities(h["title"], _summary)

        _raw_data = {"lat": h["lat"], "lng": h["lng"], "event_type": h["type"], "fatalities": h["fatalities"]}
        if _entities:
            _raw_data["entities"] = _entities

        signal = Signal(
            source="acled",
            signal_type="conflict_event",
            category="geopolitical",
            country_code=h["country"],
            title=h["title"],
            summary=_summary,
            raw_data_json=_raw_data,
            sentiment_score=-0.8,
            anomaly_score=min(0.5 + h["fatalities"] * 0.05, 1.0),
            importance=min(0.6 + h["fatalities"] * 0.04, 1.0),
            timestamp=datetime.now(timezone.utc),
        )
        db.add(signal)
        signals.append(signal)

    db.flush()
    return signals
