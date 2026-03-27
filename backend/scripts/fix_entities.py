#!/usr/bin/env python3
"""Fix entity table data quality issues:
1. Delete entities where name starts with 'CVE-' (vulnerabilities, not orgs)
2. Fix WTI entity_type from 'business' to 'commodity'
3. Fix OPEC: keep only 'organization', delete 'business' duplicate
"""

from sqlalchemy import create_engine, text

DB_URL = "postgresql://oracleflow:oracleflow@localhost:5433/oracleflow"


def main():
    print(f"Connecting to {DB_URL} ...")
    engine = create_engine(DB_URL)

    with engine.connect() as conn:
        # --- 1. Delete CVE entities ---
        cve_count = conn.execute(text(
            "SELECT COUNT(*) FROM entities WHERE name LIKE 'CVE-%'"
        )).scalar()
        print(f"\n1. CVE entities found: {cve_count}")

        if cve_count > 0:
            # First delete related entity_sources and entity_relationships
            conn.execute(text(
                "DELETE FROM entity_sources WHERE entity_id IN "
                "(SELECT id FROM entities WHERE name LIKE 'CVE-%')"
            ))
            conn.execute(text(
                "DELETE FROM entity_relationships WHERE from_entity_id IN "
                "(SELECT id FROM entities WHERE name LIKE 'CVE-%') "
                "OR to_entity_id IN "
                "(SELECT id FROM entities WHERE name LIKE 'CVE-%')"
            ))
            deleted = conn.execute(text(
                "DELETE FROM entities WHERE name LIKE 'CVE-%'"
            )).rowcount
            print(f"   Deleted {deleted} CVE entities")

        # --- 2. Fix WTI entity_type ---
        wti = conn.execute(text(
            "SELECT id, name, entity_type FROM entities WHERE name = 'WTI'"
        )).fetchall()
        print(f"\n2. WTI entities: {wti}")

        if wti:
            conn.execute(text(
                "UPDATE entities SET entity_type = 'commodity' WHERE name = 'WTI'"
            ))
            print("   Updated WTI entity_type to 'commodity'")

        # --- 3. Fix OPEC: keep organization, delete business duplicate ---
        opec = conn.execute(text(
            "SELECT id, name, entity_type FROM entities WHERE name = 'OPEC' ORDER BY id"
        )).fetchall()
        print(f"\n3. OPEC entities: {opec}")

        if len(opec) > 1:
            # Keep the 'organization' one, delete the 'business' one
            org_ids = [r[0] for r in opec if r[2] == 'organization']
            biz_ids = [r[0] for r in opec if r[2] == 'business']

            if not org_ids:
                # If there's no 'organization' one, update the first to be 'organization'
                first_id = opec[0][0]
                conn.execute(text(
                    "UPDATE entities SET entity_type = 'organization' WHERE id = :eid"
                ), {"eid": first_id})
                biz_ids = [r[0] for r in opec if r[0] != first_id]
                print(f"   Updated entity {first_id} to 'organization'")

            for bid in biz_ids:
                # Move any sources/relationships to the kept entity
                keep_id = org_ids[0] if org_ids else opec[0][0]
                conn.execute(text(
                    "UPDATE entity_sources SET entity_id = :keep WHERE entity_id = :del"
                ), {"keep": keep_id, "del": bid})
                conn.execute(text(
                    "UPDATE entity_relationships SET from_entity_id = :keep WHERE from_entity_id = :del"
                ), {"keep": keep_id, "del": bid})
                conn.execute(text(
                    "UPDATE entity_relationships SET to_entity_id = :keep WHERE to_entity_id = :del"
                ), {"keep": keep_id, "del": bid})
                conn.execute(text(
                    "DELETE FROM entities WHERE id = :del"
                ), {"del": bid})
                print(f"   Deleted OPEC duplicate (id={bid}, type='business')")
        elif len(opec) == 1 and opec[0][2] == 'business':
            conn.execute(text(
                "UPDATE entities SET entity_type = 'organization' WHERE name = 'OPEC'"
            ))
            print("   Updated OPEC entity_type to 'organization'")

        conn.commit()

        # Verify
        print("\n--- Verification ---")
        remaining_cve = conn.execute(text(
            "SELECT COUNT(*) FROM entities WHERE name LIKE 'CVE-%'"
        )).scalar()
        print(f"CVE entities remaining: {remaining_cve}")

        wti_check = conn.execute(text(
            "SELECT id, name, entity_type FROM entities WHERE name = 'WTI'"
        )).fetchall()
        print(f"WTI: {wti_check}")

        opec_check = conn.execute(text(
            "SELECT id, name, entity_type FROM entities WHERE name = 'OPEC'"
        )).fetchall()
        print(f"OPEC: {opec_check}")

        total = conn.execute(text("SELECT COUNT(*) FROM entities")).scalar()
        print(f"Total entities remaining: {total}")


if __name__ == "__main__":
    main()
