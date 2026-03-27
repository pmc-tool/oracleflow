#!/usr/bin/env python3
"""
Aggressive signal deduplication script.

Strategy:
1. Query all signals ordered by timestamp DESC
2. Normalize titles (lowercase, strip prefixes, remove punctuation)
3. Group signals with identical normalized titles -- keep highest anomaly_score
4. Find signals with >90% word overlap in first 8 words -- merge those too
5. Print how many duplicates were removed
"""

import re
import sys
from collections import defaultdict

import psycopg2

DB_URL = "postgresql://oracleflow:oracleflow@localhost:5433/oracleflow"

STRIP_PREFIXES = [
    "breaking:",
    "breaking -",
    "update:",
    "updated:",
    "exclusive:",
    "just in:",
    "alert:",
    "developing:",
    "watch:",
    "report:",
    "opinion:",
    "analysis:",
]


def normalize_title(title: str) -> str:
    """Lowercase, strip common prefixes, remove punctuation."""
    if not title:
        return ""
    t = title.lower().strip()
    for prefix in STRIP_PREFIXES:
        if t.startswith(prefix):
            t = t[len(prefix):].strip()
    # Remove punctuation
    t = re.sub(r"[^\w\s]", "", t)
    # Collapse whitespace
    t = re.sub(r"\s+", " ", t).strip()
    return t


def word_overlap_ratio(a: str, b: str, max_words: int = 8) -> float:
    """Return the Jaccard overlap ratio of the first max_words words."""
    words_a = set(a.split()[:max_words])
    words_b = set(b.split()[:max_words])
    if not words_a or not words_b:
        return 0.0
    intersection = words_a & words_b
    union = words_a | words_b
    return len(intersection) / len(union)


def main():
    print("Connecting to database...")
    try:
        conn = psycopg2.connect(DB_URL)
    except Exception as e:
        print(f"ERROR: Could not connect to database: {e}")
        sys.exit(1)

    cur = conn.cursor()

    # Fetch all signals
    cur.execute(
        "SELECT id, title, anomaly_score, timestamp FROM signals ORDER BY timestamp DESC"
    )
    rows = cur.fetchall()
    print(f"Total signals in database: {len(rows)}")

    if not rows:
        print("No signals found. Nothing to deduplicate.")
        conn.close()
        return

    # Phase 1: Exact normalized-title deduplication
    groups = defaultdict(list)
    for row in rows:
        sig_id, title, score, timestamp = row
        norm = normalize_title(title or "")
        if norm:
            groups[norm].append((sig_id, score or 0.0, title))

    ids_to_delete = set()
    exact_dupes = 0

    for norm_title, members in groups.items():
        if len(members) <= 1:
            continue
        # Keep the one with highest anomaly_score
        members.sort(key=lambda x: x[1], reverse=True)
        keeper = members[0]
        for dup in members[1:]:
            ids_to_delete.add(dup[0])
            exact_dupes += 1

    print(f"Phase 1 - Exact normalized title duplicates found: {exact_dupes}")

    # Phase 2: Fuzzy dedup -- >90% word overlap in first 8 words
    # Build list of surviving signals (not already marked for deletion)
    surviving = []
    for row in rows:
        sig_id, title, score, timestamp = row
        if sig_id not in ids_to_delete:
            norm = normalize_title(title or "")
            if norm:
                surviving.append((sig_id, norm, score or 0.0))

    # Sort by score descending so we keep highest-scored
    surviving.sort(key=lambda x: x[2], reverse=True)

    fuzzy_dupes = 0
    seen_norms = []  # list of (id, normalized_title)

    for sig_id, norm, score in surviving:
        is_dup = False
        for keeper_id, keeper_norm in seen_norms:
            if word_overlap_ratio(norm, keeper_norm) > 0.90:
                ids_to_delete.add(sig_id)
                fuzzy_dupes += 1
                is_dup = True
                break
        if not is_dup:
            seen_norms.append((sig_id, norm))

    print(f"Phase 2 - Fuzzy overlap (>90%) duplicates found: {fuzzy_dupes}")

    total_to_delete = len(ids_to_delete)
    print(f"Total duplicates to remove: {total_to_delete}")

    if total_to_delete == 0:
        print("No duplicates found. Database is clean.")
        conn.close()
        return

    # Delete duplicates -- handle FK constraints first
    id_list = list(ids_to_delete)
    batch_size = 500
    deleted = 0
    for i in range(0, len(id_list), batch_size):
        batch = id_list[i : i + batch_size]
        placeholders = ",".join(["%s"] * len(batch))
        # Clear FK references: alerts sets NULL on delete, notifications does not
        cur.execute(f"DELETE FROM notifications WHERE signal_id IN ({placeholders})", batch)
        cur.execute(f"UPDATE alerts SET signal_id = NULL WHERE signal_id IN ({placeholders})", batch)
        cur.execute(f"DELETE FROM signals WHERE id IN ({placeholders})", batch)
        deleted += cur.rowcount

    conn.commit()
    print(f"Successfully deleted {deleted} duplicate signals.")

    # Report remaining
    cur.execute("SELECT COUNT(*) FROM signals")
    remaining = cur.fetchone()[0]
    print(f"Signals remaining: {remaining}")

    cur.close()
    conn.close()


if __name__ == "__main__":
    main()
