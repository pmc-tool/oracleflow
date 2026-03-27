#!/usr/bin/env python3
"""Manually fetch NVD CVEs and GDACS alerts to populate cyber/climate signals.

Connects directly to PostgreSQL and calls the feed fetchers within a Flask-free
context using raw SQLAlchemy sessions.
"""

import json
import re
import sys
import requests
import feedparser
from datetime import datetime, timezone, timedelta
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

DB_URL = "postgresql://oracleflow:oracleflow@localhost:5433/oracleflow"

# ---------------------------------------------------------------------------
# Inline entity extraction (same as signal_extractor.py)
# ---------------------------------------------------------------------------
STOP_WORDS = {
    "a", "an", "the", "on", "in", "at", "it", "is", "to", "as", "or", "so",
    "no", "go", "do", "up", "by", "we", "he", "if", "my",
}

TICKER_ALIASES = {
    'APPLE': 'AAPL', 'MICROSOFT': 'MSFT', 'GOOGLE': 'GOOGL', 'ALPHABET': 'GOOGL',
    'AMAZON': 'AMZN', 'NVIDIA': 'NVDA', 'META': 'META', 'FACEBOOK': 'META',
    'TESLA': 'TSLA', 'NETFLIX': 'NFLX', 'BITCOIN': 'BTC', 'ETHEREUM': 'ETH',
    'OPEC': 'OPEC', 'NATO': 'NATO',
    'JPMORGAN': 'JPM', 'GOLDMAN SACHS': 'GS', 'MORGAN STANLEY': 'MS',
    'BOEING': 'BA', 'LOCKHEED': 'LMT', 'RAYTHEON': 'RTX',
    'EXXON': 'XOM', 'CHEVRON': 'CVX', 'SHELL': 'SHEL',
}

TICKERS = {
    'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA', 'JPM',
    'BTC', 'ETH', 'XRP', 'SOL', 'WTI', 'BRENT', 'GOLD', 'SILVER',
    'SPX', 'SPY', 'NDX', 'QQQ', 'VIX',
}

CVE_PATTERN = re.compile(r'CVE-\d{4}-\d{4,}')

ORGANIZATIONS = [
    'NATO', 'EU', 'UN', 'WHO', 'IMF', 'OPEC', 'FBI', 'CIA', 'NSA', 'CISA',
    'SEC', 'Fed', 'ECB', 'Microsoft', 'Google', 'Amazon', 'Meta', 'NVIDIA',
    'IAEA', 'BRICS', 'Pentagon', 'Kremlin',
]

MITRE_KEYWORDS = {
    'phishing': 'T1566', 'ransomware': 'T1486', 'zero-day': 'T1190',
    'supply chain': 'T1195', 'DDoS': 'T1498', 'brute force': 'T1110',
    'backdoor': 'T1059', 'wiper': 'T1485', 'botnet': 'T1583.005',
}

COUNTRY_MAP = {
    'United States': 'US', 'United Kingdom': 'GB', 'China': 'CN', 'Russia': 'RU',
    'Ukraine': 'UA', 'India': 'IN', 'Japan': 'JP', 'Germany': 'DE', 'France': 'FR',
    'Iran': 'IR', 'Israel': 'IL', 'North Korea': 'KP',
}


def extract_entities(title, summary=''):
    combined = (title or '') + ' ' + (summary or '')
    text_upper = combined.upper()
    entities = {}

    # Tickers
    matched_tickers = set()
    for ticker in TICKERS:
        if ticker.lower() in STOP_WORDS:
            continue
        if re.search(r'\b' + re.escape(ticker) + r'\b', text_upper):
            matched_tickers.add(ticker)
    for alias, ticker in TICKER_ALIASES.items():
        if re.search(r'\b' + re.escape(alias) + r'\b', text_upper):
            matched_tickers.add(ticker)
    if matched_tickers:
        entities['tickers'] = sorted(matched_tickers)

    # CVEs
    cves = [m.group() for m in CVE_PATTERN.finditer(combined)]
    if cves:
        entities['cves'] = cves

    # Organizations
    orgs = []
    for org in ORGANIZATIONS:
        if len(org) <= 4:
            if re.search(r'\b' + re.escape(org) + r'\b', combined):
                orgs.append(org)
        else:
            if org.upper() in text_upper or org in combined:
                orgs.append(org)
    if orgs:
        entities['organizations'] = orgs

    # Countries
    countries = []
    for name, code in COUNTRY_MAP.items():
        if name.upper() in text_upper:
            countries.append(code)
    if countries:
        entities['countries'] = countries

    # MITRE
    text_lower = combined.lower()
    mitre = []
    for kw, tid in MITRE_KEYWORDS.items():
        if kw.lower() in text_lower:
            mitre.append(tid)
    if mitre:
        entities['mitre_attack'] = mitre

    return entities


# ---------------------------------------------------------------------------
# NVD CVE Fetcher (expanded time range for more results)
# ---------------------------------------------------------------------------
def fetch_nvd_cves(conn, hours=120):
    """Fetch CVEs from NVD for the last `hours` hours (default 5 days for more coverage)."""
    now = datetime.now(timezone.utc)
    start = (now - timedelta(hours=hours)).strftime('%Y-%m-%dT%H:%M:%S.000')
    end = now.strftime('%Y-%m-%dT%H:%M:%S.000')

    print(f"\n--- NVD CVE Fetch (last {hours} hours) ---")
    url = (
        f"https://services.nvd.nist.gov/rest/json/cves/2.0"
        f"?resultsPerPage=40&pubStartDate={start}&pubEndDate={end}"
    )
    print(f"Fetching: {url}")

    try:
        resp = requests.get(url, timeout=30)
        print(f"Response status: {resp.status_code}")
        if resp.status_code != 200:
            print(f"NVD API returned {resp.status_code}")
            return 0

        data = resp.json()
        vulns = data.get('vulnerabilities', [])
        print(f"NVD returned {len(vulns)} vulnerabilities")

        count = 0
        for vuln in vulns:
            cve = vuln.get('cve', {})
            cve_id = cve.get('id', '')
            if not cve_id:
                continue

            # Check duplicate
            existing = conn.execute(text(
                "SELECT 1 FROM signals WHERE title ILIKE :pattern LIMIT 1"
            ), {"pattern": f"%{cve_id}%"}).scalar()
            if existing:
                continue

            descriptions = cve.get('descriptions', [])
            desc = next((d['value'] for d in descriptions if d.get('lang') == 'en'), '')

            # CVSS score
            metrics = cve.get('metrics', {})
            cvss_score = 0.0
            severity = 'LOW'
            for key in ['cvssMetricV31', 'cvssMetricV30', 'cvssMetricV2']:
                if key in metrics:
                    cvss_data = metrics[key][0].get('cvssData', {})
                    cvss_score = cvss_data.get('baseScore', 0.0)
                    severity = cvss_data.get('baseSeverity', 'LOW')
                    break

            anomaly = min(1.0, cvss_score / 10.0)
            entities = extract_entities(f"{cve_id} {desc}", '')
            entities['cves'] = [cve_id]
            if cvss_score > 0:
                entities['cvss'] = {'score': cvss_score, 'severity': severity}

            raw_data = json.dumps({
                'cve_id': cve_id,
                'cvss_score': cvss_score,
                'severity': severity,
                'link': f"https://nvd.nist.gov/vuln/detail/{cve_id}",
                'entities': entities,
                'source_name': 'NVD CVEs',
            })

            conn.execute(text(
                "INSERT INTO signals (source, signal_type, category, title, summary, "
                "raw_data_json, sentiment_score, anomaly_score, importance, timestamp) "
                "VALUES (:source, :stype, :cat, :title, :summary, "
                ":raw, :sent, :anomaly, :importance, :ts)"
            ), {
                "source": "nvd",
                "stype": "cve",
                "cat": "cyber",
                "title": f"{cve_id} ({severity}, CVSS {cvss_score})",
                "summary": desc[:500],
                "raw": raw_data,
                "sent": -0.5 if cvss_score > 7 else -0.2,
                "anomaly": round(anomaly, 4),
                "importance": round(min(1.0, 0.5 + cvss_score / 20), 4),
                "ts": now.isoformat(),
            })
            count += 1

        conn.commit()
        print(f"Inserted {count} new CVE signals")
        return count

    except Exception as e:
        print(f"NVD fetch error: {e}")
        try:
            conn.rollback()
        except Exception:
            pass
        return 0


# ---------------------------------------------------------------------------
# GDACS Disaster Alert Fetcher
# ---------------------------------------------------------------------------
def fetch_gdacs_alerts(conn):
    """Fetch disaster alerts from GDACS RSS feed."""
    print("\n--- GDACS Disaster Alert Fetch ---")
    try:
        feed = feedparser.parse('https://www.gdacs.org/xml/rss.xml')
        entries = feed.entries[:20]
        print(f"GDACS feed returned {len(entries)} entries")

        count = 0
        now = datetime.now(timezone.utc)

        for entry in entries:
            title = entry.get('title', '')
            if not title:
                continue

            # Dedup
            existing = conn.execute(text(
                "SELECT 1 FROM signals WHERE title = :title LIMIT 1"
            ), {"title": title}).scalar()
            if existing:
                continue

            summary = entry.get('summary', entry.get('description', ''))
            link = entry.get('link', '')

            anomaly = 0.3
            if 'Red' in title or 'red' in title:
                anomaly = 0.9
            elif 'Orange' in title or 'orange' in title:
                anomaly = 0.7
            elif 'Green' in title or 'green' in title:
                anomaly = 0.4

            entities = extract_entities(title, summary)

            raw_data = json.dumps({
                'link': link,
                'source_name': 'GDACS',
                'entities': entities,
            })

            conn.execute(text(
                "INSERT INTO signals (source, signal_type, category, title, summary, "
                "raw_data_json, sentiment_score, anomaly_score, importance, timestamp) "
                "VALUES (:source, :stype, :cat, :title, :summary, "
                ":raw, :sent, :anomaly, :importance, :ts)"
            ), {
                "source": "gdacs",
                "stype": "disaster_alert",
                "cat": "climate",
                "title": title,
                "summary": (summary or "")[:500],
                "raw": raw_data,
                "sent": -0.7,
                "anomaly": round(anomaly, 4),
                "importance": round(max(0.6, anomaly), 4),
                "ts": now.isoformat(),
            })
            count += 1

        conn.commit()
        print(f"Inserted {count} new GDACS signals")
        return count

    except Exception as e:
        print(f"GDACS fetch error: {e}")
        try:
            conn.rollback()
        except Exception:
            pass
        return 0


# ---------------------------------------------------------------------------
# OPEC Debug
# ---------------------------------------------------------------------------
def debug_opec(conn):
    """Debug OPEC entity extraction issue."""
    print("\n--- OPEC Entity Debug ---")

    # Check signals mentioning OPEC in title
    rows = conn.execute(text(
        "SELECT id, title, raw_data_json FROM signals WHERE title ILIKE '%opec%' ORDER BY id"
    )).fetchall()
    print(f"Signals with 'OPEC' in title: {len(rows)}")

    opec_with_entity = 0
    opec_without_entity = 0

    for row in rows:
        sig_id, title, raw_data = row[0], row[1], row[2]
        if isinstance(raw_data, str):
            try:
                raw_data = json.loads(raw_data)
            except Exception:
                raw_data = {}
        elif raw_data is None:
            raw_data = {}

        entities = raw_data.get("entities", {})
        orgs = entities.get("organizations", [])
        tickers = entities.get("tickers", [])

        has_opec = "OPEC" in orgs or "OPEC" in tickers
        if has_opec:
            opec_with_entity += 1
        else:
            opec_without_entity += 1
            print(f"  MISSING OPEC entity on signal {sig_id}: {title[:80]}")
            print(f"    orgs={orgs}, tickers={tickers}")

            # Fix: re-extract entities and update
            new_entities = extract_entities(title, raw_data.get("summary", ""))
            raw_data["entities"] = new_entities
            conn.execute(text(
                "UPDATE signals SET raw_data_json = :raw WHERE id = :sid"
            ), {"raw": json.dumps(raw_data), "sid": sig_id})

    if opec_without_entity > 0:
        conn.commit()
        print(f"Fixed {opec_without_entity} OPEC signals with missing entity extraction")

    print(f"OPEC signals: {opec_with_entity} with entity, {opec_without_entity} were missing (now fixed)")

    # Also check entity filter: signals where raw_data_json entities contain OPEC
    entity_count = conn.execute(text(
        "SELECT COUNT(*) FROM signals WHERE "
        "raw_data_json::text ILIKE '%\"OPEC\"%'"
    )).scalar()
    print(f"Signals with OPEC in entities JSON: {entity_count}")


def main():
    print(f"Connecting to {DB_URL} ...")
    engine = create_engine(DB_URL)

    with engine.connect() as conn:
        # Fetch NVD CVEs (5-day window for more coverage)
        nvd_count = fetch_nvd_cves(conn, hours=120)

        # Fetch GDACS alerts
        gdacs_count = fetch_gdacs_alerts(conn)

        # Debug OPEC
        debug_opec(conn)

        # Summary
        print("\n=== Summary ===")
        print(f"NVD CVEs added: {nvd_count}")
        print(f"GDACS alerts added: {gdacs_count}")

        # Show total cyber signals
        cyber_count = conn.execute(text(
            "SELECT COUNT(*) FROM signals WHERE category = 'cyber'"
        )).scalar()
        print(f"Total cyber signals now: {cyber_count}")

        climate_count = conn.execute(text(
            "SELECT COUNT(*) FROM signals WHERE category = 'climate'"
        )).scalar()
        print(f"Total climate signals now: {climate_count}")


if __name__ == "__main__":
    main()
