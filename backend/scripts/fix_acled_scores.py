#!/usr/bin/env python3
"""Fix ACLED signals: diversify anomaly scores based on event type and fatalities.

The 10 existing ACLED signals all have identical anomaly_score (0.0188).
This script updates them with diversified scores based on their content.
"""

import json
from sqlalchemy import create_engine, text

DB_URL = "postgresql://oracleflow:oracleflow@localhost:5433/oracleflow"


def compute_anomaly(event_type: str, fatalities: int) -> float:
    et = (event_type or "").lower()
    if "battles" in et or "battle" in et or "armed clash" in et:
        return min(1.0, 0.6 + fatalities * 0.04)
    elif "explosion" in et or "remote violence" in et or "shelling" in et or "airstrike" in et or "drone strike" in et:
        return min(1.0, 0.55 + fatalities * 0.05)
    elif "violence against civilians" in et:
        return min(0.95, 0.5 + fatalities * 0.03)
    elif "protest" in et:
        if fatalities > 0:
            return min(0.8, 0.5 + fatalities * 0.1)
        return 0.25
    elif "riot" in et:
        return min(0.7, 0.35 + fatalities * 0.07)
    else:
        return min(0.8, 0.3 + fatalities * 0.05)


def compute_sentiment(event_type: str, fatalities: int) -> float:
    if fatalities > 20:
        return -0.95
    elif fatalities > 10:
        return -0.85
    elif fatalities > 5:
        return -0.75
    elif fatalities > 0:
        return -0.6
    et = (event_type or "").lower()
    if "protest" in et:
        return -0.4
    return -0.5


def main():
    print(f"Connecting to {DB_URL} ...")
    engine = create_engine(DB_URL)

    with engine.connect() as conn:
        rows = conn.execute(text(
            "SELECT id, title, raw_data_json, anomaly_score FROM signals WHERE source = 'acled' ORDER BY id"
        )).fetchall()

        print(f"ACLED signals found: {len(rows)}")

        for row in rows:
            sig_id = row[0]
            title = row[1]
            raw_data = row[2]
            old_score = row[3]

            if isinstance(raw_data, str):
                try:
                    raw_data = json.loads(raw_data)
                except Exception:
                    raw_data = {}
            elif raw_data is None:
                raw_data = {}

            event_type = raw_data.get("event_type", "")
            fatalities = int(raw_data.get("fatalities", 0))

            # Also infer event type from title if not in raw_data
            if not event_type:
                t = title.lower()
                if "battle" in t or "armed clash" in t:
                    event_type = "Battles"
                elif "shelling" in t or "airstrike" in t or "drone strike" in t:
                    event_type = "Explosions/Remote violence"
                elif "protest" in t:
                    event_type = "Protests"
                elif "violence against" in t:
                    event_type = "Violence against civilians"

            new_anomaly = round(compute_anomaly(event_type, fatalities), 4)
            new_sentiment = round(compute_sentiment(event_type, fatalities), 4)
            new_importance = round(min(1.0, new_anomaly + 0.1), 4)

            conn.execute(text(
                "UPDATE signals SET anomaly_score = :a, sentiment_score = :s, importance = :i "
                "WHERE id = :sid"
            ), {"a": new_anomaly, "s": new_sentiment, "i": new_importance, "sid": sig_id})

            print(f"  Signal {sig_id}: '{title[:60]}' | fatalities={fatalities} | "
                  f"anomaly: {old_score} -> {new_anomaly} | sentiment: {new_sentiment}")

        conn.commit()

        # Verify diversity
        scores = conn.execute(text(
            "SELECT anomaly_score, COUNT(*) FROM signals WHERE source = 'acled' "
            "GROUP BY anomaly_score ORDER BY anomaly_score"
        )).fetchall()
        print(f"\nNew anomaly score distribution:")
        for s in scores:
            print(f"  {s[0]}: {s[1]} signals")


if __name__ == "__main__":
    main()
