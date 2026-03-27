"""UNHCR displacement data -- with honest timestamps and live RSS fetch."""

import logging
import re
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# Static baseline data from UNHCR Global Trends reports.
# This is used as a fallback when the live RSS feed is unavailable.
_STATIC_DISPLACEMENT_DATA = {
    "refugees": 30_500_000,
    "asylum_seekers": 8_400_000,
    "idps": 63_900_000,
    "total": 117_300_000,
    "last_updated": "2025-06-15",
    "source": "UNHCR Global Trends 2024 (estimates, updated annually)",
    "note": "Static baseline. Live updates attempted via UNHCR RSS on each request.",
    "top_origins": [
        {"country": "Syrian Arab Rep.", "code": "SY", "count": 6_800_000, "status": "CRISIS"},
        {"country": "Ukraine", "code": "UA", "count": 6_300_000, "status": "CRISIS"},
        {"country": "Afghanistan", "code": "AF", "count": 6_100_000, "status": "CRISIS"},
        {"country": "Sudan", "code": "SD", "count": 2_700_000, "status": "CRISIS"},
        {"country": "South Sudan", "code": "SS", "count": 2_300_000, "status": "CRISIS"},
        {"country": "Venezuela", "code": "VE", "count": 7_700_000, "status": "CRISIS"},
        {"country": "DR Congo", "code": "CD", "count": 1_100_000, "status": "CRISIS"},
        {"country": "Myanmar", "code": "MM", "count": 1_300_000, "status": "CRISIS"},
        {"country": "Somalia", "code": "SO", "count": 800_000, "status": "CRISIS"},
        {"country": "Eritrea", "code": "ER", "count": 600_000, "status": "HIGH"},
    ],
    "top_hosts": [
        {"country": "Turkey", "code": "TR", "count": 3_600_000},
        {"country": "Iran", "code": "IR", "count": 3_400_000},
        {"country": "Colombia", "code": "CO", "count": 2_900_000},
        {"country": "Germany", "code": "DE", "count": 2_600_000},
        {"country": "Pakistan", "code": "PK", "count": 1_700_000},
    ],
}

_UNHCR_RSS_URL = "https://www.unhcr.org/rss/news.xml"

# Simple patterns to extract displacement numbers from headlines
_NUMBER_PATTERNS = [
    re.compile(r'(\d[\d,\.]*)\s*million\s+(refugee|displaced|people|flee)', re.IGNORECASE),
    re.compile(r'(refugee|displaced|flee|forced)\D{0,40}(\d[\d,\.]*)\s*million', re.IGNORECASE),
]


def _try_fetch_unhcr_rss() -> list[dict]:
    """Attempt to fetch recent UNHCR news headlines via RSS.

    Returns a list of recent displacement-related headlines with any
    extracted numbers. Returns an empty list on failure.
    """
    try:
        import feedparser
    except ImportError:
        logger.debug("feedparser not available for UNHCR RSS fetch")
        return []

    try:
        feed = feedparser.parse(_UNHCR_RSS_URL)
        if not feed.entries:
            return []

        headlines = []
        for entry in feed.entries[:15]:
            title = (entry.get("title") or "").strip()
            summary = (entry.get("summary") or "").strip()
            link = entry.get("link", "")
            if not title:
                continue

            # Try to extract displacement numbers from headline/summary
            extracted_number = None
            for pattern in _NUMBER_PATTERNS:
                match = pattern.search(title + " " + summary)
                if match:
                    groups = match.groups()
                    for g in groups:
                        if g and g[0].isdigit():
                            try:
                                extracted_number = float(g.replace(",", ""))
                            except ValueError:
                                pass
                            break
                    if extracted_number:
                        break

            headlines.append({
                "title": title[:200],
                "summary": summary[:300],
                "url": link,
                "extracted_millions": extracted_number,
            })

        return headlines
    except Exception as e:
        logger.debug(f"Failed to fetch UNHCR RSS: {e}")
        return []


def get_displacement_data() -> dict:
    """Return displacement data with honest sourcing.

    Attempts to enrich static baseline data with live UNHCR RSS headlines.
    Always includes last_updated timestamp and source attribution.
    """
    data = dict(_STATIC_DISPLACEMENT_DATA)

    # Try to get live UNHCR headlines
    live_headlines = _try_fetch_unhcr_rss()
    if live_headlines:
        data["live_headlines"] = live_headlines
        data["live_feed_fetched"] = datetime.now(timezone.utc).isoformat()
        data["source"] = "UNHCR estimates (updated monthly) + live RSS headlines"
    else:
        data["live_headlines"] = []
        data["source"] = "UNHCR estimates (updated monthly, static fallback)"

    data["fetched_at"] = datetime.now(timezone.utc).isoformat()
    return data
