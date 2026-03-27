import requests
import logging
import os
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.oracleflow.models.signal import Signal
from app.oracleflow.constants import SignalCategory

logger = logging.getLogger(__name__)


def fetch_market_news(db: Session) -> list[Signal]:
    """Fetch general market news from Finnhub."""
    api_key = os.environ.get("FINNHUB_API_KEY", "")
    if not api_key:
        logger.debug("No FINNHUB_API_KEY set, skipping market news")
        return []

    try:
        resp = requests.get(
            "https://finnhub.io/api/v1/news",
            params={"category": "general", "token": api_key},
            timeout=15,
        )
        resp.raise_for_status()
        articles = resp.json()
    except Exception as e:
        logger.error(f"Finnhub fetch failed: {e}")
        return []

    signals = []
    for article in articles[:15]:
        title = article.get("headline", "")[:200]
        if not title:
            continue

        existing = db.execute(
            select(Signal).where(Signal.title == title)
        ).scalar_one_or_none()
        if existing:
            continue

        signal = Signal(
            source="finnhub",
            signal_type="market_news",
            category=SignalCategory.FINANCE.value,
            country_code="US",
            title=title,
            summary=article.get("summary", "")[:500],
            raw_data_json={
                "url": article.get("url"),
                "source": article.get("source"),
            },
            sentiment_score=0.0,
            anomaly_score=0.3,
            importance=0.4,
            timestamp=datetime.now(timezone.utc),
        )
        db.add(signal)
        signals.append(signal)

    db.flush()
    return signals
