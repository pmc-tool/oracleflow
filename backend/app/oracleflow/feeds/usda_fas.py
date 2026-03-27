"""Fetch global economic indicators from World Bank API (free, no key).

The World Bank Indicators API provides macroeconomic data for all countries.
This feed pulls recent values for key indicators (inflation, GDP growth,
trade balance, etc.) and converts notable changes into signals.
"""

import logging
import requests
from datetime import datetime, timezone

from app.oracleflow.models.signal import Signal
from app.oracleflow.entities.signal_extractor import extract_entities

logger = logging.getLogger(__name__)

# Key indicators: (code, human_name, category, higher_is_worse)
INDICATORS = [
    ('FP.CPI.TOTL.ZG', 'Inflation Rate (CPI)', 'economy', True),
    ('NY.GDP.MKTP.KD.ZG', 'GDP Growth Rate', 'economy', False),
    ('SL.UEM.TOTL.ZS', 'Unemployment Rate', 'economy', True),
    ('BN.CAB.XOKA.CD', 'Current Account Balance', 'economy', False),
    ('GC.DOD.TOTL.GD.ZS', 'Government Debt (% GDP)', 'economy', True),
    ('PA.NUS.FCRF', 'Exchange Rate (LCU per USD)', 'finance', False),
]

# Major economies to track
COUNTRIES = 'USA;CHN;DEU;JPN;GBR;IND;BRA;FRA;CAN;KOR'


def fetch_usda_fas(db):
    """Fetch World Bank economic indicators (free, no key).

    Despite the module name (kept for backward compat with scheduler imports),
    this now pulls from the World Bank Indicators API.
    """
    count = 0

    for indicator_code, indicator_name, category, higher_is_worse in INDICATORS:
        try:
            url = (
                f"https://api.worldbank.org/v2/country/{COUNTRIES}"
                f"/indicator/{indicator_code}"
                f"?format=json&per_page=20&date=2022:2025&mrv=1"
            )
            resp = requests.get(url, timeout=20)
            if resp.status_code != 200:
                continue

            data = resp.json()
            # World Bank returns [metadata, results]
            if not isinstance(data, list) or len(data) < 2:
                continue

            results = data[1]
            if not results:
                continue

            # Build consolidated signal from multiple country data points
            entries = []
            for entry in results:
                if entry.get('value') is None:
                    continue
                country = entry.get('country', {}).get('value', 'Unknown')
                value = entry.get('value')
                year = entry.get('date', '')
                entries.append({
                    'country': country,
                    'value': round(value, 2) if isinstance(value, float) else value,
                    'year': year,
                })

            if not entries:
                continue

            title = f"World Bank: {indicator_name} — Latest Data ({entries[0].get('year', '2024')})"

            # Dedup
            if db.query(Signal).filter(Signal.title == title).first():
                continue

            # Build summary
            parts = [f"{e['country']}: {e['value']}" for e in entries[:6]]
            summary_text = f"{indicator_name} across major economies — " + '; '.join(parts)

            entities = extract_entities(title, summary_text)
            entities['indicator'] = indicator_code
            entities['countries'] = [e['country'] for e in entries]

            # Anomaly: flag high inflation or unemployment
            anomaly = 0.35
            if higher_is_worse:
                max_val = max(e['value'] for e in entries if isinstance(e['value'], (int, float)))
                if indicator_code == 'FP.CPI.TOTL.ZG' and max_val > 8:
                    anomaly = 0.7
                elif indicator_code == 'SL.UEM.TOTL.ZS' and max_val > 10:
                    anomaly = 0.65

            signal = Signal(
                source='worldbank',
                signal_type='economic_indicator',
                category=category,
                title=title,
                summary=summary_text[:500],
                raw_data_json={
                    'indicator_code': indicator_code,
                    'indicator_name': indicator_name,
                    'entries': entries[:10],
                    'link': f'https://data.worldbank.org/indicator/{indicator_code}',
                    'source_name': 'World Bank',
                    'entities': entities,
                },
                sentiment_score=-0.2 if higher_is_worse else 0.1,
                anomaly_score=round(anomaly, 4),
                importance=0.7,
                timestamp=datetime.now(timezone.utc),
            )
            db.add(signal)
            count += 1

        except Exception as e:
            logger.debug("World Bank fetch for %s failed: %s", indicator_name, e)
            continue

    if count:
        db.commit()
        logger.info("World Bank: fetched %d new economic indicator signals", count)

    return count
