import requests
import logging
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.oracleflow.models.signal import Signal
from app.oracleflow.constants import SignalCategory

logger = logging.getLogger(__name__)
USGS_URL = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/4.5_day.geojson"


def fetch_earthquakes(db: Session) -> list[Signal]:
    """Fetch significant earthquakes (M4.5+) from last 24h."""
    try:
        resp = requests.get(USGS_URL, timeout=15)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        logger.error(f"USGS fetch failed: {e}")
        return []

    signals = []
    for feature in data.get("features", [])[:20]:
        props = feature.get("properties", {})
        title = props.get("title", "Unknown earthquake")[:200]

        # Dedup
        existing = db.execute(
            select(Signal).where(Signal.title == title)
        ).scalar_one_or_none()
        if existing:
            continue

        magnitude = props.get("mag", 0) or 0
        _summary = f"Magnitude {magnitude} earthquake. {props.get('place', '')}"

        # Extract entities from title + summary
        from app.oracleflow.entities.signal_extractor import extract_entities
        _entities = extract_entities(title, _summary)

        _raw_data = {
            "magnitude": magnitude,
            "place": props.get("place"),
            "url": props.get("url"),
        }
        if _entities:
            _raw_data["entities"] = _entities

        signal = Signal(
            source="usgs",
            signal_type="earthquake",
            category=SignalCategory.CLIMATE.value,
            country_code="",  # USGS doesn't always give country
            title=title,
            summary=_summary,
            raw_data_json=_raw_data,
            sentiment_score=-0.5,
            anomaly_score=min(magnitude / 9.0, 1.0),  # Normalize to 0-1
            importance=min(magnitude / 8.0, 1.0),
            timestamp=datetime.now(timezone.utc),
        )
        db.add(signal)
        signals.append(signal)

    db.flush()
    return signals
