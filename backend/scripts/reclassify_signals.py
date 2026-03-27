#!/usr/bin/env python3
"""
Reclassify miscategorized signals in the database.

- Signals in 'climate' with titles containing sperm, coral house, archaeology, dinosaur -> 'other'
- Signals in 'cyber' with titles containing robot, lawnmower, iPad, Apple Watch, Amazon deal -> 'technology'
"""

import sys

import psycopg2

DB_URL = "postgresql://oracleflow:oracleflow@localhost:5433/oracleflow"


def main():
    print("Connecting to database...")
    try:
        conn = psycopg2.connect(DB_URL)
    except Exception as e:
        print(f"ERROR: Could not connect to database: {e}")
        sys.exit(1)

    cur = conn.cursor()
    total_updated = 0

    # --- Climate -> Other for non-climate content ---
    climate_to_other_terms = ["sperm", "coral house", "archaeology", "dinosaur"]
    conditions = " OR ".join(
        [f"LOWER(title) LIKE '%{term}%'" for term in climate_to_other_terms]
    )
    sql = f"""
        UPDATE signals
        SET category = 'other'
        WHERE category = 'climate'
          AND ({conditions})
    """
    cur.execute(sql)
    count = cur.rowcount
    total_updated += count
    print(f"Reclassified {count} signals from 'climate' -> 'other' (non-climate content)")

    # --- Cyber -> Technology for consumer tech content ---
    cyber_to_tech_terms = ["robot", "lawnmower", "ipad", "apple watch", "amazon deal"]
    conditions = " OR ".join(
        [f"LOWER(title) LIKE '%{term}%'" for term in cyber_to_tech_terms]
    )
    sql = f"""
        UPDATE signals
        SET category = 'technology'
        WHERE category = 'cyber'
          AND ({conditions})
    """
    cur.execute(sql)
    count = cur.rowcount
    total_updated += count
    print(f"Reclassified {count} signals from 'cyber' -> 'technology' (consumer tech content)")

    conn.commit()
    print(f"\nTotal signals reclassified: {total_updated}")

    cur.close()
    conn.close()


if __name__ == "__main__":
    main()
