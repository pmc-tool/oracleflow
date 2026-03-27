#!/usr/bin/env python3
"""Populate the entities table from signal data.

Scans all signals with entities in raw_data_json and creates Entity + EntitySource
records for each unique entity (ticker, organization, country).
Connects directly to PostgreSQL to avoid Flask context issues.
"""

import json
import sys
from datetime import datetime, timezone
from sqlalchemy import create_engine, text

DB_URL = "postgresql://oracleflow:oracleflow@localhost:5433/oracleflow"
BATCH_SIZE = 50


def main():
    print(f"Connecting to {DB_URL} ...")
    engine = create_engine(DB_URL)

    with engine.connect() as conn:
        # ---------------------------------------------------------------
        # Step 0: Ensure tables exist
        # ---------------------------------------------------------------
        for tbl in ("entities", "entity_sources"):
            check = conn.execute(text(
                "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = :t)"
            ), {"t": tbl}).scalar()
            if not check:
                print(f"Table '{tbl}' does not exist. Run init_db first.")
                sys.exit(1)

        # ---------------------------------------------------------------
        # Step 1: Fetch all signals that have entities in raw_data_json
        # ---------------------------------------------------------------
        rows = conn.execute(text(
            "SELECT id, title, raw_data_json FROM signals "
            "WHERE raw_data_json IS NOT NULL ORDER BY id"
        )).fetchall()

        print(f"Found {len(rows)} signals with raw_data_json")

        # ---------------------------------------------------------------
        # Step 2: Build a map of unique entities -> set of signal ids
        # entity key: (name, entity_type)
        # ---------------------------------------------------------------
        # entity_key -> { "name": ..., "entity_type": ..., "country_code": ..., "signal_ids": set, "source_urls": set }
        entity_map = {}

        for row in rows:
            sig_id = row[0]
            title = row[1] or ""
            raw_data = row[2]

            if raw_data is None:
                continue
            if isinstance(raw_data, str):
                try:
                    raw_data = json.loads(raw_data)
                except (json.JSONDecodeError, TypeError):
                    continue

            entities = raw_data.get("entities")
            if not entities:
                continue

            source_url = raw_data.get("url", raw_data.get("link", ""))

            # Process tickers
            for ticker in entities.get("tickers", []):
                key = (ticker, "business")
                if key not in entity_map:
                    entity_map[key] = {
                        "name": ticker,
                        "entity_type": "business",
                        "country_code": None,
                        "signal_ids": set(),
                        "source_urls": set(),
                    }
                entity_map[key]["signal_ids"].add(sig_id)
                if source_url:
                    entity_map[key]["source_urls"].add(source_url)

            # Process organizations
            for org in entities.get("organizations", []):
                key = (org, "organization")
                if key not in entity_map:
                    entity_map[key] = {
                        "name": org,
                        "entity_type": "organization",
                        "country_code": None,
                        "signal_ids": set(),
                        "source_urls": set(),
                    }
                entity_map[key]["signal_ids"].add(sig_id)
                if source_url:
                    entity_map[key]["source_urls"].add(source_url)

            # Process countries
            for country_code in entities.get("countries", []):
                key = (country_code, "government")
                if key not in entity_map:
                    entity_map[key] = {
                        "name": country_code,
                        "entity_type": "government",
                        "country_code": country_code,
                        "signal_ids": set(),
                        "source_urls": set(),
                    }
                entity_map[key]["signal_ids"].add(sig_id)
                if source_url:
                    entity_map[key]["source_urls"].add(source_url)

            # Process CVEs as entities too
            for cve in entities.get("cves", []):
                key = (cve, "organization")  # treat CVE IDs as org-type entities
                if key not in entity_map:
                    entity_map[key] = {
                        "name": cve,
                        "entity_type": "organization",
                        "country_code": None,
                        "signal_ids": set(),
                        "source_urls": set(),
                    }
                entity_map[key]["signal_ids"].add(sig_id)
                if source_url:
                    entity_map[key]["source_urls"].add(source_url)

        print(f"Found {len(entity_map)} unique entities across signals")

        if not entity_map:
            print("No entities to populate. Exiting.")
            return

        # ---------------------------------------------------------------
        # Step 3: Clear existing entities (fresh populate)
        # ---------------------------------------------------------------
        existing_count = conn.execute(text("SELECT COUNT(*) FROM entities")).scalar()
        if existing_count > 0:
            print(f"Clearing {existing_count} existing entity records...")
            conn.execute(text("DELETE FROM entity_sources"))
            conn.execute(text("DELETE FROM entities"))
            conn.commit()

        # ---------------------------------------------------------------
        # Step 4: Insert entities and entity_sources in batches
        # ---------------------------------------------------------------
        now = datetime.now(timezone.utc).isoformat()
        created = 0
        sources_created = 0

        for (name, etype), info in entity_map.items():
            # Insert entity
            result = conn.execute(text(
                "INSERT INTO entities (name, entity_type, country_code, metadata_json, created_at, updated_at) "
                "VALUES (:name, :etype, :cc, :meta, :now, :now) RETURNING id"
            ), {
                "name": info["name"],
                "etype": info["entity_type"],
                "cc": info["country_code"],
                "meta": json.dumps({
                    "signal_count": len(info["signal_ids"]),
                    "signal_ids": sorted(info["signal_ids"]),
                }),
                "now": now,
            })
            entity_id = result.scalar()
            created += 1

            # Insert entity_sources (one per unique source URL, up to 10)
            urls = sorted(info["source_urls"])[:10]  # cap at 10 sources per entity
            if not urls:
                # Still create at least one source record linked to signal extraction
                conn.execute(text(
                    "INSERT INTO entity_sources (entity_id, source_type, source_url, confidence_score, discovered_at) "
                    "VALUES (:eid, 'signal_extraction', NULL, 0.8, :now)"
                ), {"eid": entity_id, "now": now})
                sources_created += 1
            else:
                for url in urls:
                    conn.execute(text(
                        "INSERT INTO entity_sources (entity_id, source_type, source_url, confidence_score, discovered_at) "
                        "VALUES (:eid, 'signal_extraction', :url, 0.8, :now)"
                    ), {"eid": entity_id, "url": url, "now": now})
                    sources_created += 1

            # Batch commit
            if created % BATCH_SIZE == 0:
                conn.commit()
                print(f"  Progress: {created}/{len(entity_map)} entities created")

        # Final commit
        conn.commit()
        print(f"\nDone! Created {created} entities and {sources_created} entity_source records.")

        # Print breakdown by type
        for etype in ("business", "organization", "government"):
            count = sum(1 for (_, t) in entity_map if t == etype)
            print(f"  {etype}: {count}")


if __name__ == "__main__":
    main()
