"""Fetch threat intelligence pulses from AlienVault OTX (free, no API key)."""

import logging
import requests
from datetime import datetime, timezone

from app.oracleflow.models.signal import Signal
from app.oracleflow.entities.signal_extractor import extract_entities

logger = logging.getLogger(__name__)


def fetch_otx_pulses(db):
    """Fetch public threat pulses from AlienVault OTX (free).

    Uses the public activity endpoint which does not require authentication.
    Each pulse contains indicators of compromise (IOCs) and tags describing
    the threat.  Higher IOC counts produce higher anomaly scores.
    """
    url = "https://otx.alienvault.com/otxapi/pulses/?limit=20&sort=-created&page=1"

    try:
        resp = requests.get(url, timeout=30, headers={'User-Agent': 'OracleFlow/1.0'})
        if resp.status_code != 200:
            logger.warning("AlienVault OTX returned %s", resp.status_code)
            return 0

        data = resp.json()
        count = 0
        for pulse in data.get('results', []):
            title = pulse.get('name', '')
            desc = pulse.get('description', '')[:500]
            tags = pulse.get('tags', [])
            ioc_count = len(pulse.get('indicators', []))

            if not title:
                continue

            # Dedup by exact title
            if db.query(Signal).filter(Signal.title == title).first():
                continue

            # Extract IOC types
            ioc_types = set()
            for ind in pulse.get('indicators', [])[:10]:
                ioc_types.add(ind.get('type', ''))

            entities = extract_entities(title, desc)
            entities['iocs'] = {'types': list(ioc_types), 'count': ioc_count}
            if tags:
                entities['tags'] = tags[:10]

            anomaly = min(1.0, 0.4 + ioc_count * 0.02)  # More IOCs = higher anomaly

            signal = Signal(
                source='otx',
                signal_type='threat_pulse',
                category='cyber',
                title=title,
                summary=desc or f"Threat pulse with {ioc_count} indicators. Tags: {', '.join(tags[:5])}",
                raw_data_json={
                    'pulse_id': pulse.get('id'),
                    'link': f"https://otx.alienvault.com/pulse/{pulse.get('id')}",
                    'source_name': 'AlienVault OTX',
                    'tags': tags,
                    'ioc_count': ioc_count,
                    'ioc_types': list(ioc_types),
                    'entities': entities,
                },
                sentiment_score=-0.5,
                anomaly_score=round(anomaly, 4),
                importance=round(min(1.0, 0.6 + ioc_count * 0.01), 4),
                timestamp=datetime.now(timezone.utc),
            )
            db.add(signal)
            count += 1

        db.commit()
        logger.info("AlienVault OTX: fetched %d new pulses", count)
        return count

    except Exception as e:
        db.rollback()
        logger.error("AlienVault OTX fetch failed: %s", e)
        return 0
