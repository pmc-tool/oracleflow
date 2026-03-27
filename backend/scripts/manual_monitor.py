"""Manual page monitor check — run from backend/ directory."""
import sys, os, hashlib, re, requests
from datetime import datetime, timezone
from difflib import SequenceMatcher
from urllib.parse import urlparse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

DB_URL = os.environ.get('DATABASE_URL', 'postgresql://oracleflow:oracleflow@localhost:5433/oracleflow')
engine = create_engine(DB_URL)
db = Session(engine)

SITE_ID = int(sys.argv[1]) if len(sys.argv) > 1 else 11
LIMIT = int(sys.argv[2]) if len(sys.argv) > 2 else 3
ORG_ID = 3

rows = db.execute(text(
    "SELECT id, url, path, importance_score FROM site_pages "
    "WHERE site_id=:sid AND is_active=true "
    "ORDER BY last_crawled ASC NULLS FIRST LIMIT :lim"
), {"sid": SITE_ID, "lim": LIMIT}).fetchall()

print(f"Checking {len(rows)} pages from site {SITE_ID}...")

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"

for pid, url, path, imp in rows:
    print(f"\n--- {path or url} ---")
    try:
        r = requests.get(url, timeout=15, headers={"User-Agent": UA})
        html = r.text

        t = re.sub(r"<script[\s\S]*?</script>", " ", html, flags=re.IGNORECASE)
        t = re.sub(r"<style[\s\S]*?</style>", " ", t, flags=re.IGNORECASE)
        t = re.sub(r"<[^>]+>", " ", t)
        t = re.sub(r"&\w+;", " ", t)
        t = re.sub(r"\s+", " ", t).strip()

        h = hashlib.sha256(t.encode()).hexdigest()[:40]
        print(f"  Fetched: {len(t)} chars, hash: {h[:16]}")

        prev = db.execute(text(
            "SELECT id, content_hash, content_text FROM page_snapshots "
            "WHERE page_id=:p ORDER BY captured_at DESC LIMIT 1"
        ), {"p": pid}).fetchone()

        db.execute(text(
            "INSERT INTO page_snapshots (page_id, content_text, content_html, content_hash, captured_at) "
            "VALUES (:p, :t, :h, :hash, :now)"
        ), {"p": pid, "t": t[:80000], "h": html[:150000], "hash": h, "now": datetime.now(timezone.utc)})

        nsid = db.execute(text("SELECT lastval()")).scalar()

        if prev and prev[1] != h:
            ratio = SequenceMatcher(None, (prev[2] or "")[:5000], t[:5000]).ratio()
            pct = round((1 - ratio) * 100, 1)
            sig = min(1.0, pct / 100)

            db.execute(text(
                "INSERT INTO page_diffs (page_id, old_snapshot_id, new_snapshot_id, diff_type, diff_summary, detected_at) "
                "VALUES (:p, :o, :n, :dt, :ds, :now)"
            ), {"p": pid, "o": prev[0], "n": nsid, "dt": "content_changed",
                "ds": f"{pct}% changed", "now": datetime.now(timezone.utc)})

            did = db.execute(text("SELECT lastval()")).scalar()
            parsed = urlparse(url)
            pname = (path or "/").strip("/").split("/")[-1] or "homepage"
            pname = pname.replace("-", " ").replace("_", " ").title()

            db.execute(text(
                "INSERT INTO signals (source, signal_type, category, organization_id, title, summary, "
                "sentiment_score, anomaly_score, importance, timestamp) "
                "VALUES (:s, :st, :c, :o, :t, :su, :se, :a, :i, :ts)"
            ), {
                "s": "site_monitor", "st": "page_change", "c": "geopolitical", "o": ORG_ID,
                "t": f"{parsed.netloc}: {pname} page changed",
                "su": f"{pct}% content changed on {pname} page",
                "se": 0, "a": round(sig, 4),
                "i": round(min(1, (imp or 0.5) * 0.6 + sig * 0.4), 4),
                "ts": datetime.now(timezone.utc),
            })
            # Create notification if anomaly is high enough
            signal_id = db.execute(text("SELECT lastval()")).scalar()
            title = f"{parsed.netloc}: {pname} page changed"
            if sig >= 0.7:
                severity = "critical" if sig > 0.8 else "high"
                # Find users in this org
                users = db.execute(text("SELECT id FROM users WHERE organization_id=:o AND is_active=true"), {"o": ORG_ID}).fetchall()
                for u in users:
                    db.execute(text(
                        "INSERT INTO notifications (user_id, organization_id, signal_id, title, message, severity, is_read, created_at) "
                        "VALUES (:uid, :oid, :sid, :t, :m, :sev, 0, :now)"
                    ), {"uid": u[0], "oid": ORG_ID, "sid": signal_id, "t": title,
                        "m": f"{pct}% content changed on {pname} page", "sev": severity,
                        "now": datetime.now(timezone.utc)})
                print(f"  *** CHANGE DETECTED: {pct}% → signal + notification created!")
            else:
                print(f"  *** CHANGE DETECTED: {pct}% → signal created (below alert threshold)")
        elif prev:
            print(f"  No change (hash matches)")
        else:
            print(f"  First snapshot taken")

        db.execute(text("UPDATE site_pages SET last_crawled=:n WHERE id=:p"),
                   {"n": datetime.now(timezone.utc), "p": pid})

    except Exception as e:
        print(f"  ERROR: {e}")

db.commit()
count = db.execute(text(
    "SELECT count(*) FROM signals WHERE source='site_monitor' AND organization_id=:o"
), {"o": ORG_ID}).scalar()
print(f"\nDone! Total site_monitor signals: {count}")
db.close()
