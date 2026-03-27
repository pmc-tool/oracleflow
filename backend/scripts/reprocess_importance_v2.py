#!/usr/bin/env python3
"""Reprocess importance scores for all existing signals using the new multi-factor formula.

Factors in: source tier, content keywords, anomaly score, entity count, and signal age.
Connects directly to PostgreSQL.
"""

import json
import re
import sys
from datetime import datetime, timezone
from sqlalchemy import create_engine, text

DB_URL = "postgresql://oracleflow:oracleflow@localhost:5433/oracleflow"
BATCH_SIZE = 100

# ---------------------------------------------------------------------------
# Source tier mapping (same as rss.py)
# ---------------------------------------------------------------------------
SOURCE_TIERS = {
    "Reuters World": 0.9, "Reuters Business": 0.9,
    "AP": 0.9, "AFP": 0.9, "UPI": 0.9,
    "BBC World": 0.8, "BBC Business": 0.8, "BBC Politics": 0.8,
    "BBC Health": 0.8, "BBC Tech": 0.8,
    "CNN World": 0.8, "CNN Money": 0.8,
    "NPR World": 0.8, "Al Jazeera": 0.8,
    "Guardian World": 0.8, "Guardian Politics": 0.8, "Guardian Climate": 0.8,
    "CNBC": 0.8, "MarketWatch": 0.8, "Yahoo Finance": 0.8,
    "Financial Times": 0.8, "The Economist": 0.8, "WSJ via Dow Jones": 0.8,
    "Foreign Policy": 0.8, "Foreign Affairs": 0.8,
    "ABC News Intl": 0.8, "NBC News World": 0.8, "CBS News World": 0.8,
    "PBS NewsHour World": 0.8,
    "Nikkei Asia": 0.8, "South China Morning Post": 0.8,
    "Deutsche Welle": 0.8, "France 24": 0.8, "NHK World": 0.8,
    "ABC Australia": 0.8, "CBC World": 0.8, "Le Monde": 0.8,
    "El Pais": 0.8, "Der Spiegel Intl": 0.8, "Euronews": 0.8,
    "CoinDesk": 0.75, "Cointelegraph": 0.75, "Blockworks": 0.75,
    "Decrypt": 0.75, "Bitcoin Magazine": 0.75,
    "Krebs on Security": 0.75, "CISA Advisories": 0.75, "CISA": 0.75,
    "Dark Reading": 0.75, "Schneier": 0.75,
    "BleepingComputer": 0.75, "The Record": 0.75, "SecurityWeek": 0.75,
    "The Hacker News": 0.75, "Cisco Talos": 0.75, "Palo Alto Unit42": 0.75,
    "US-CERT Alerts": 0.75, "NVD CVEs": 0.75,
    "Google Project Zero": 0.75, "Microsoft Security Response": 0.75,
    "GitHub Security Advisories": 0.75,
    "Defense News": 0.75, "Military Times": 0.75, "USNI News": 0.75,
    "Breaking Defense": 0.75, "Janes": 0.75, "Defense One": 0.75,
    "RAND Corporation": 0.75, "Carnegie Endowment": 0.75,
    "Chatham House": 0.75, "Crisis Group": 0.75, "IISS": 0.75,
    "Brookings": 0.75, "Atlantic Council": 0.75, "CSIS": 0.75, "CFR": 0.75,
    "Kitco Gold": 0.75, "OilPrice": 0.75,
    "NASA Climate": 0.75, "CDC": 0.75, "WHO Alerts": 0.75,
    "IMF News": 0.75, "Federal Reserve": 0.75, "ECB Press": 0.75,
    "UN News": 0.75, "IAEA": 0.75, "FAO News": 0.75,
    "State Dept": 0.75, "Pentagon": 0.75, "White House": 0.75,
    "OPEC News": 0.75, "IEA": 0.75, "EIA": 0.75, "EIA Main": 0.75,
    "USDA": 0.75, "CFTC": 0.75,
    "ReliefWeb": 0.75, "UNHCR News": 0.75, "ICRC": 0.75,
    "FEMA": 0.75, "GDACS": 0.75,
    "FreightWaves": 0.75, "Supply Chain Dive": 0.75,
    "Lloyd's List": 0.75, "Journal of Commerce": 0.75,
    "Jamaica Observer": 0.6, "Jamaica Gleaner": 0.6, "Loop Jamaica": 0.6,
    "Trinidad Newsday": 0.6, "Trinidad Guardian": 0.6, "Barbados Today": 0.6,
    "Jamaica Gleaner Alt": 0.6, "Trinidad Express": 0.6,
    "Times of India": 0.6, "The Hindu": 0.6, "Indian Express": 0.6,
    "Bangkok Post": 0.6, "VnExpress": 0.6, "Channel NewsAsia": 0.6,
    "Japan Today": 0.6, "Kyiv Independent": 0.6, "Moscow Times": 0.6,
    "Times of Israel": 0.6, "Haaretz": 0.6, "Al Arabiya": 0.6,
    "Miami Herald Americas": 0.6, "MercoPress": 0.6,
    "Buenos Aires Times": 0.6, "Mexico News Daily": 0.6,
    "Africanews": 0.6, "News24 South Africa": 0.6, "AllAfrica": 0.6,
    "Premium Times Nigeria": 0.6, "Vanguard Nigeria": 0.6,
    "Good News Network": 0.6, "Positive News": 0.6,
}
_DEFAULT_IMPORTANCE = 0.5


def _content_importance(title):
    t = title.lower()
    adjustment = 0.0
    if any(kw in t for kw in ['breaking', 'urgent', 'exclusive']):
        adjustment += 0.15
    if any(kw in t for kw in ['analysis', 'report', 'investigation']):
        adjustment += 0.10
    if any(kw in t for kw in ['opinion', 'editorial', 'commentary']):
        adjustment -= 0.05
    return adjustment


def compute_importance(source_name, title, anomaly_score, entity_count, signal_age_hours):
    """Multi-factor importance matching the updated rss.py formula."""
    source_base = SOURCE_TIERS.get(source_name, _DEFAULT_IMPORTANCE)

    content_adj = _content_importance(title) if title else 0.0
    content_component = max(0.0, min(1.0, (content_adj + 0.05) / 0.2))

    anomaly_component = max(0.0, min(1.0, anomaly_score))

    entity_component = min(1.0, entity_count / 5.0)

    if signal_age_hours <= 0:
        freshness_component = 1.0
    elif signal_age_hours >= 24:
        freshness_component = 0.2
    else:
        freshness_component = 1.0 - (0.8 * signal_age_hours / 24.0)

    importance = (
        0.40 * source_base +
        0.15 * content_component +
        0.20 * anomaly_component +
        0.10 * entity_component +
        0.15 * freshness_component
    )

    return round(max(0.1, min(1.0, importance)), 2)


def main():
    print(f"Connecting to {DB_URL} ...")
    engine = create_engine(DB_URL)
    now = datetime.now(timezone.utc)

    with engine.connect() as conn:
        rows = conn.execute(text(
            "SELECT id, title, raw_data_json, anomaly_score, importance, timestamp "
            "FROM signals ORDER BY id"
        )).fetchall()

        print(f"Reprocessing importance for {len(rows)} signals...")

        updated = 0
        old_distribution = {}
        new_distribution = {}

        for row in rows:
            sig_id = row[0]
            title = row[1] or ''
            raw_data = row[2]
            anomaly_score = float(row[3] or 0)
            old_importance = float(row[4] or 0)
            timestamp = row[5]

            # Parse raw_data_json
            if raw_data is None:
                raw_data = {}
            elif isinstance(raw_data, str):
                try:
                    raw_data = json.loads(raw_data)
                except Exception:
                    raw_data = {}

            # Get source name
            source_name = raw_data.get('source_name', '')

            # Count entities
            entities = raw_data.get('entities', {})
            entity_count = 0
            for v in entities.values():
                if isinstance(v, list):
                    entity_count += len(v)

            # Compute signal age
            if timestamp:
                if isinstance(timestamp, str):
                    try:
                        ts = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    except Exception:
                        ts = now
                else:
                    ts = timestamp
                    if ts.tzinfo is None:
                        ts = ts.replace(tzinfo=timezone.utc)
                age_hours = (now - ts).total_seconds() / 3600.0
            else:
                age_hours = 24.0

            new_importance = compute_importance(
                source_name, title, anomaly_score, entity_count, age_hours
            )

            # Track distributions
            old_bucket = round(old_importance, 1)
            new_bucket = round(new_importance, 1)
            old_distribution[old_bucket] = old_distribution.get(old_bucket, 0) + 1
            new_distribution[new_bucket] = new_distribution.get(new_bucket, 0) + 1

            if abs(new_importance - old_importance) > 0.001:
                conn.execute(text(
                    "UPDATE signals SET importance = :imp WHERE id = :sid"
                ), {"imp": new_importance, "sid": sig_id})
                updated += 1

            if (updated + 1) % BATCH_SIZE == 0:
                conn.commit()

        conn.commit()

        print(f"\nUpdated {updated}/{len(rows)} signal importance scores")
        print("\nOLD importance distribution:")
        for bucket in sorted(old_distribution.keys()):
            count = old_distribution[bucket]
            bar = '#' * min(50, count)
            print(f"  {bucket:.1f}: {count:4d} {bar}")

        print("\nNEW importance distribution:")
        for bucket in sorted(new_distribution.keys()):
            count = new_distribution[bucket]
            bar = '#' * min(50, count)
            print(f"  {bucket:.1f}: {count:4d} {bar}")


if __name__ == "__main__":
    main()
