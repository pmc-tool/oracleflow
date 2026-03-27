import feedparser
import requests
from datetime import datetime, timezone
from app.oracleflow.models.signal import Signal
from app.oracleflow.entities.signal_extractor import extract_entities

def fetch_gdacs_alerts(db):
    """Fetch disaster alerts from GDACS (free, no key)."""
    try:
        feed = feedparser.parse('https://www.gdacs.org/xml/rss.xml')
        count = 0
        for entry in feed.entries[:20]:
            title = entry.get('title', '')
            # Dedup
            existing = db.query(Signal).filter(Signal.title == title).first()
            if existing:
                continue

            summary = entry.get('summary', entry.get('description', ''))
            link = entry.get('link', '')

            # Extract alert level from title (Green, Orange, Red)
            anomaly = 0.3
            if 'Red' in title or 'red' in title:
                anomaly = 0.9
            elif 'Orange' in title or 'orange' in title:
                anomaly = 0.7
            elif 'Green' in title or 'green' in title:
                anomaly = 0.4

            entities = extract_entities(title, summary)

            signal = Signal(
                source='gdacs',
                signal_type='disaster_alert',
                category='climate',
                title=title,
                summary=summary[:500],
                raw_data_json={
                    'link': link,
                    'source_name': 'GDACS',
                    'entities': entities,
                },
                sentiment_score=-0.7,
                anomaly_score=round(anomaly, 4),
                importance=round(max(0.6, anomaly), 4),
                timestamp=datetime.now(timezone.utc),
            )
            db.add(signal)
            count += 1

        db.commit()
        return count
    except Exception as e:
        db.rollback()
        return 0
