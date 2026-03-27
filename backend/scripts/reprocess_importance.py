#!/usr/bin/env python3
"""Reprocess importance scores on all existing signals.

Reads source_name from raw_data_json and applies the SOURCE_TIERS mapping
to replace the old hardcoded 0.5 default. Also recalculates anomaly_score
using the updated wider-spread algorithm.

Connects directly to PostgreSQL (same pattern as reprocess_signals.py).
"""

import json
import re
import sys
from sqlalchemy import create_engine, text

DB_URL = "postgresql://oracleflow:oracleflow@localhost:5433/oracleflow"
BATCH_SIZE = 100

# ---------------------------------------------------------------------------
# Source-tier importance mapping (mirrors rss.py SOURCE_TIERS)
# ---------------------------------------------------------------------------

SOURCE_TIERS = {
    # Wire services -- 0.9
    "Reuters World": 0.9, "Reuters Business": 0.9,
    "AP": 0.9, "AFP": 0.9, "UPI": 0.9,
    # Major global outlets -- 0.8
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
    # Specialized domain sources -- 0.75
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
    # Regional outlets -- 0.6
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

DEFAULT_IMPORTANCE = 0.5


def content_importance(title):
    """Score content importance based on title keywords. Returns adjustment in [-0.05, 0.15]."""
    t = title.lower()
    adjustment = 0.0

    high_keywords = ['breaking', 'urgent', 'exclusive']
    medium_keywords = ['analysis', 'report', 'investigation']
    low_keywords = ['opinion', 'editorial', 'commentary']

    if any(kw in t for kw in high_keywords):
        adjustment += 0.15
    if any(kw in t for kw in medium_keywords):
        adjustment += 0.10
    if any(kw in t for kw in low_keywords):
        adjustment -= 0.05

    return adjustment


def importance_for_source(source_name, title=''):
    """Compute importance from source tier + content keywords, clamped to [0.1, 1.0]."""
    base = SOURCE_TIERS.get(source_name, DEFAULT_IMPORTANCE)
    adjustment = content_importance(title) if title else 0.0
    return round(max(0.1, min(1.0, base + adjustment)), 2)


# ---------------------------------------------------------------------------
# Anomaly recalculation (mirrors rss.py _estimate_anomaly)
# ---------------------------------------------------------------------------

def estimate_anomaly(text, source_name=""):
    t = text.lower()
    high_urgency = [
        "breaking", "urgent", "crisis", "emergency", "war", "attack",
        "killed", "explosion", "crash", "collapse", "invaded", "coup",
        "assassination", "martial law", "catastroph",
    ]
    medium_urgency = [
        "warns", "threat", "concern", "fears", "spike", "surge", "plunge",
        "record", "sanctions", "escalat", "tensions", "protest", "riot",
        "shutdown", "default", "breach", "ransomware", "hack",
    ]

    high_hits = sum(1 for w in high_urgency if w in t)
    medium_hits = sum(1 for w in medium_urgency if w in t)

    if high_hits >= 2:
        score = min(1.0, 0.85 + (high_hits - 2) * 0.05)
    elif high_hits == 1:
        score = min(0.80, 0.65 + medium_hits * 0.05)
    elif medium_hits >= 2:
        score = min(0.65, 0.55 + (medium_hits - 2) * 0.03)
    elif medium_hits == 1:
        score = 0.45
    else:
        text_len_factor = min(0.1, len(t) / 5000)
        score = 0.2 + text_len_factor

    source_importance = SOURCE_TIERS.get(source_name, DEFAULT_IMPORTANCE)
    if source_importance >= 0.9:
        score = min(1.0, score + 0.05)

    return round(score, 2)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print(f"Connecting to {DB_URL} ...")
    engine = create_engine(DB_URL)

    with engine.connect() as conn:
        total = conn.execute(text("SELECT COUNT(*) FROM signals")).scalar()
        print(f"Total signals to reprocess: {total}")

        if total == 0:
            print("No signals found. Exiting.")
            return

        rows = conn.execute(text(
            "SELECT id, title, summary, raw_data_json, importance, anomaly_score FROM signals ORDER BY id"
        )).fetchall()

        importance_updated = 0
        anomaly_updated = 0

        for i, row in enumerate(rows):
            sig_id = row[0]
            title = row[1] or ""
            summary = row[2] or ""
            raw_data = row[3]
            old_importance = row[4]
            old_anomaly = row[5]

            # Parse raw_data_json to get source_name
            if raw_data is None:
                raw_data = {}
            elif isinstance(raw_data, str):
                try:
                    raw_data = json.loads(raw_data)
                except (json.JSONDecodeError, TypeError):
                    raw_data = {}

            source_name = raw_data.get("source_name", "")

            # Compute new importance from source tier + content keywords
            new_importance = importance_for_source(source_name, title)

            # Recalculate anomaly score with wider spread
            combined_text = title + " " + summary
            new_anomaly = estimate_anomaly(combined_text, source_name)

            # Only update if values actually changed
            if new_importance != old_importance or new_anomaly != old_anomaly:
                conn.execute(
                    text(
                        "UPDATE signals SET importance = :imp, anomaly_score = :anom WHERE id = :sid"
                    ),
                    {"imp": new_importance, "anom": new_anomaly, "sid": sig_id},
                )

                if new_importance != old_importance:
                    importance_updated += 1
                if new_anomaly != old_anomaly:
                    anomaly_updated += 1

            if (i + 1) % BATCH_SIZE == 0:
                conn.commit()
                print(f"  Progress: {i + 1}/{total} checked "
                      f"({importance_updated} importance, {anomaly_updated} anomaly updated)")

        conn.commit()
        print(f"\nDone! Checked {total} signals.")
        print(f"  Importance updated: {importance_updated}")
        print(f"  Anomaly score updated: {anomaly_updated}")


if __name__ == "__main__":
    main()
