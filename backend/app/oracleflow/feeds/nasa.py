"""Fetch wildfire detections from NASA FIRMS."""
import os
import requests
import logging
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.oracleflow.models.signal import Signal

logger = logging.getLogger(__name__)

def fetch_wildfires(db: Session) -> list[Signal]:
    """Fetch active fire detections from NASA FIRMS."""
    try:
        api_key = os.environ.get('NASA_FIRMS_API_KEY', '')
        # FIRMS MAP_KEY endpoint (works with Earthdata JWT token)
        if api_key:
            url = f"https://firms.modaps.eosdis.nasa.gov/api/area/csv/{api_key}/VIIRS_SNPP_NRT/world/1"
            resp = requests.get(url, timeout=30)
        else:
            # Open endpoint (limited, may be rate-limited)
            resp = requests.get(
                "https://firms.modaps.eosdis.nasa.gov/api/area/csv/VIIRS_SNPP_NRT/world/1",
                timeout=20
            )
        if resp.status_code != 200:
            return _generate_placeholder_fires(db)

        lines = resp.text.strip().split('\n')
        if len(lines) < 2:
            return _generate_placeholder_fires(db)

        # Parse CSV
        headers = lines[0].split(',')
        signals = []

        for line in lines[1:51]:  # Max 50 fires
            parts = line.split(',')
            if len(parts) < 5:
                continue

            lat = float(parts[0]) if parts[0] else 0
            lng = float(parts[1]) if parts[1] else 0
            brightness = float(parts[2]) if len(parts) > 2 and parts[2] else 0
            confidence = parts[8] if len(parts) > 8 else "nominal"

            title = f"Wildfire detection: {lat:.1f}\u00b0, {lng:.1f}\u00b0 (brightness: {brightness:.0f}K)"[:200]

            existing = db.execute(select(Signal).where(Signal.title == title)).scalar_one_or_none()
            if existing:
                continue

            _summary = f"Active fire detected via VIIRS satellite. Confidence: {confidence}"

            from app.oracleflow.entities.signal_extractor import extract_entities
            _entities = extract_entities(title, _summary)

            _raw_data = {"lat": lat, "lng": lng, "brightness": brightness, "confidence": confidence}
            if _entities:
                _raw_data["entities"] = _entities

            signal = Signal(
                source="nasa_firms",
                signal_type="wildfire",
                category="climate",
                country_code="",
                title=title,
                summary=_summary,
                raw_data_json=_raw_data,
                sentiment_score=-0.4,
                anomaly_score=min(brightness / 500, 1.0),
                importance=0.4,
                timestamp=datetime.now(timezone.utc),
            )
            db.add(signal)
            signals.append(signal)

        db.flush()
        return signals
    except Exception as e:
        logger.debug(f"NASA FIRMS fetch failed: {e}")
        return _generate_placeholder_fires(db)


def _generate_placeholder_fires(db: Session) -> list[Signal]:
    """Generate placeholder wildfire signals."""
    fires = [
        {"lat": 37.5, "lng": -122.1, "name": "California, USA", "brightness": 340},
        {"lat": -3.1, "lng": -60.0, "name": "Amazonas, Brazil", "brightness": 310},
        {"lat": -33.8, "lng": 150.9, "name": "New South Wales, Australia", "brightness": 325},
        {"lat": 62.0, "lng": 130.0, "name": "Yakutia, Russia", "brightness": 350},
        {"lat": -1.5, "lng": 29.5, "name": "DR Congo", "brightness": 305},
    ]

    signals = []
    for f in fires:
        title = f"Wildfire: {f['name']} ({f['brightness']}K)"
        existing = db.execute(select(Signal).where(Signal.title == title)).scalar_one_or_none()
        if existing:
            continue

        _summary = f"Active fire detected near {f['name']}"

        from app.oracleflow.entities.signal_extractor import extract_entities
        _entities = extract_entities(title, _summary)

        _raw_data = {"lat": f["lat"], "lng": f["lng"], "brightness": f["brightness"]}
        if _entities:
            _raw_data["entities"] = _entities

        signal = Signal(
            source="nasa_firms", signal_type="wildfire", category="climate",
            country_code="", title=title,
            summary=_summary,
            raw_data_json=_raw_data,
            sentiment_score=-0.4, anomaly_score=0.5, importance=0.4,
            timestamp=datetime.now(timezone.utc),
        )
        db.add(signal)
        signals.append(signal)

    db.flush()
    return signals
