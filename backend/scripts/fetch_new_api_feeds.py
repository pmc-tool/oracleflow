#!/usr/bin/env python3
"""One-shot fetch from the 4 new free API integrations.

Runs ClinicalTrials.gov, AlienVault OTX, USDA FAS, and OpenFDA feeds
directly against the database (no Flask app context needed — uses raw
SQLAlchemy sessions).

Usage:
    cd backend && python scripts/fetch_new_api_feeds.py
"""

import json
import sys
import socket
import logging
import requests
from datetime import datetime, timezone, timedelta
from sqlalchemy import create_engine, text

socket.setdefaulttimeout(15)
logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
logger = logging.getLogger(__name__)

DB_URL = "postgresql://oracleflow:oracleflow@localhost:5433/oracleflow"


# ---------------------------------------------------------------------------
# Inline entity extraction (mirror of signal_extractor.extract_entities)
# ---------------------------------------------------------------------------
import re

_CVE_RE = re.compile(r'CVE-\d{4}-\d{4,}', re.IGNORECASE)
_TICKER_RE = re.compile(r'\b[A-Z]{3,5}\b')


def extract_entities(title, summary):
    combined = f"{title} {summary}"
    entities = {}
    cves = _CVE_RE.findall(combined)
    if cves:
        entities['cves'] = cves
    return entities


# ---------------------------------------------------------------------------
# 1. ClinicalTrials.gov
# ---------------------------------------------------------------------------
def fetch_clinical_trials(conn, days=3):
    end = datetime.now(timezone.utc)
    start = end - timedelta(days=days)
    url = (
        f"https://clinicaltrials.gov/api/v2/studies"
        f"?query.term=AREA[LastUpdatePostDate]RANGE[{start.strftime('%Y-%m-%d')},{end.strftime('%Y-%m-%d')}]"
        f"&pageSize=20&sort=LastUpdatePostDate:desc&format=json"
    )
    resp = requests.get(url, timeout=30)
    if resp.status_code != 200:
        logger.warning("ClinicalTrials.gov returned %s", resp.status_code)
        return 0

    data = resp.json()
    count = 0
    now = datetime.now(timezone.utc)

    for study in data.get('studies', []):
        protocol = study.get('protocolSection', {})
        id_mod = protocol.get('identificationModule', {})
        status_mod = protocol.get('statusModule', {})
        desc_mod = protocol.get('descriptionModule', {})

        nct_id = id_mod.get('nctId', '')
        title = id_mod.get('briefTitle', id_mod.get('officialTitle', ''))
        status = status_mod.get('overallStatus', '')
        phase = ', '.join(protocol.get('designModule', {}).get('phases', []))
        brief = desc_mod.get('briefSummary', '')

        if not title or not nct_id:
            continue

        # Dedup
        exists = conn.execute(text(
            "SELECT 1 FROM signals WHERE title ILIKE :pat LIMIT 1"
        ), {"pat": f"%{nct_id}%"}).scalar()
        if exists:
            continue

        phase_imp = {'PHASE3': 0.85, 'PHASE2': 0.7, 'PHASE1': 0.6, 'PHASE4': 0.8}
        importance = 0.5
        for p, imp in phase_imp.items():
            if p in (phase or '').upper().replace(' ', ''):
                importance = imp
                break

        full_title = f"[{nct_id}] {title} ({phase or 'N/A'} - {status})"
        raw = json.dumps({
            'nct_id': nct_id, 'phase': phase, 'status': status,
            'link': f"https://clinicaltrials.gov/study/{nct_id}",
            'source_name': 'ClinicalTrials.gov',
            'entities': extract_entities(title, brief[:200]),
        })

        conn.execute(text(
            "INSERT INTO signals (source, signal_type, category, title, summary, "
            "raw_data_json, sentiment_score, anomaly_score, importance, timestamp) "
            "VALUES (:src, :st, :cat, :title, :sum, :raw, :sent, :anom, :imp, :ts)"
        ), {
            "src": "clinicaltrials_gov", "st": "clinical_trial", "cat": "healthcare",
            "title": full_title[:1024],
            "sum": (brief[:500] if brief else f"Clinical trial {nct_id} status: {status}"),
            "raw": raw,
            "sent": 0.3 if status in ('RECRUITING', 'ACTIVE_NOT_RECRUITING') else 0.0,
            "anom": round(importance * 0.6, 4), "imp": round(importance, 4),
            "ts": now.isoformat(),
        })
        count += 1

    if count:
        conn.commit()
    return count


# ---------------------------------------------------------------------------
# 2. AlienVault OTX
# ---------------------------------------------------------------------------
def fetch_otx_pulses(conn):
    url = "https://otx.alienvault.com/otxapi/pulses/?limit=20&sort=-created&page=1"
    resp = requests.get(url, timeout=30, headers={'User-Agent': 'OracleFlow/1.0'})
    if resp.status_code != 200:
        logger.warning("OTX returned %s", resp.status_code)
        return 0

    data = resp.json()
    count = 0
    now = datetime.now(timezone.utc)

    for pulse in data.get('results', []):
        title = pulse.get('name', '')
        desc = pulse.get('description', '')[:500]
        tags = pulse.get('tags', [])
        ioc_count = len(pulse.get('indicators', []))

        if not title:
            continue

        exists = conn.execute(text(
            "SELECT 1 FROM signals WHERE title = :t LIMIT 1"
        ), {"t": title}).scalar()
        if exists:
            continue

        ioc_types = list({ind.get('type', '') for ind in pulse.get('indicators', [])[:10]})
        anomaly = min(1.0, 0.4 + ioc_count * 0.02)

        raw = json.dumps({
            'pulse_id': pulse.get('id'),
            'link': f"https://otx.alienvault.com/pulse/{pulse.get('id')}",
            'source_name': 'AlienVault OTX',
            'tags': tags, 'ioc_count': ioc_count, 'ioc_types': ioc_types,
            'entities': extract_entities(title, desc),
        })

        conn.execute(text(
            "INSERT INTO signals (source, signal_type, category, title, summary, "
            "raw_data_json, sentiment_score, anomaly_score, importance, timestamp) "
            "VALUES (:src, :st, :cat, :title, :sum, :raw, :sent, :anom, :imp, :ts)"
        ), {
            "src": "otx", "st": "threat_pulse", "cat": "cyber",
            "title": title[:1024],
            "sum": desc or f"Threat pulse with {ioc_count} indicators. Tags: {', '.join(tags[:5])}",
            "raw": raw,
            "sent": -0.5,
            "anom": round(anomaly, 4),
            "imp": round(min(1.0, 0.6 + ioc_count * 0.01), 4),
            "ts": now.isoformat(),
        })
        count += 1

    if count:
        conn.commit()
    return count


# ---------------------------------------------------------------------------
# 3. World Bank Economic Indicators
# ---------------------------------------------------------------------------
def fetch_usda_fas(conn):
    """Fetch World Bank economic indicators (free, no key)."""
    indicators = [
        ('FP.CPI.TOTL.ZG', 'Inflation Rate (CPI)', 'economy', True),
        ('NY.GDP.MKTP.KD.ZG', 'GDP Growth Rate', 'economy', False),
        ('SL.UEM.TOTL.ZS', 'Unemployment Rate', 'economy', True),
        ('BN.CAB.XOKA.CD', 'Current Account Balance', 'economy', False),
        ('GC.DOD.TOTL.GD.ZS', 'Government Debt (% GDP)', 'economy', True),
        ('PA.NUS.FCRF', 'Exchange Rate (LCU per USD)', 'finance', False),
    ]
    countries = 'USA;CHN;DEU;JPN;GBR;IND;BRA;FRA;CAN;KOR'
    count = 0
    now = datetime.now(timezone.utc)

    for code, name, category, higher_is_worse in indicators:
        try:
            url = (
                f"https://api.worldbank.org/v2/country/{countries}"
                f"/indicator/{code}?format=json&per_page=20&date=2022:2025&mrv=1"
            )
            resp = requests.get(url, timeout=20)
            if resp.status_code != 200:
                continue

            data = resp.json()
            if not isinstance(data, list) or len(data) < 2:
                continue

            results = data[1]
            if not results:
                continue

            entries = []
            for entry in results:
                if entry.get('value') is None:
                    continue
                c = entry.get('country', {}).get('value', 'Unknown')
                v = entry.get('value')
                y = entry.get('date', '')
                entries.append({'country': c, 'value': round(v, 2) if isinstance(v, float) else v, 'year': y})

            if not entries:
                continue

            title = f"World Bank: {name} — Latest Data ({entries[0].get('year', '2024')})"
            exists = conn.execute(text(
                "SELECT 1 FROM signals WHERE title = :t LIMIT 1"
            ), {"t": title}).scalar()
            if exists:
                continue

            parts = [f"{e['country']}: {e['value']}" for e in entries[:6]]
            summary = f"{name} across major economies — " + '; '.join(parts)

            anomaly = 0.35
            if higher_is_worse:
                max_val = max((e['value'] for e in entries if isinstance(e['value'], (int, float))), default=0)
                if code == 'FP.CPI.TOTL.ZG' and max_val > 8:
                    anomaly = 0.7
                elif code == 'SL.UEM.TOTL.ZS' and max_val > 10:
                    anomaly = 0.65

            raw = json.dumps({
                'indicator_code': code, 'indicator_name': name,
                'entries': entries[:10],
                'link': f'https://data.worldbank.org/indicator/{code}',
                'source_name': 'World Bank',
                'entities': extract_entities(title, summary),
            })

            conn.execute(text(
                "INSERT INTO signals (source, signal_type, category, title, summary, "
                "raw_data_json, sentiment_score, anomaly_score, importance, timestamp) "
                "VALUES (:src, :st, :cat, :title, :sum, :raw, :sent, :anom, :imp, :ts)"
            ), {
                "src": "worldbank", "st": "economic_indicator", "cat": category,
                "title": title[:1024], "sum": summary[:500], "raw": raw,
                "sent": -0.2 if higher_is_worse else 0.1,
                "anom": round(anomaly, 4), "imp": 0.7, "ts": now.isoformat(),
            })
            count += 1
        except Exception as e:
            logger.debug("World Bank %s failed: %s", name, e)

    if count:
        conn.commit()
    return count


# ---------------------------------------------------------------------------
# 4. OpenFDA Drug Adverse Events
# ---------------------------------------------------------------------------
def fetch_open_fda(conn):
    end = datetime.now(timezone.utc)
    start = end - timedelta(days=30)
    url = (
        f"https://api.fda.gov/drug/event.json"
        f"?search=serious:1"
        f"&limit=20&sort=receivedate:desc"
    )

    resp = requests.get(url, timeout=30)
    if resp.status_code != 200:
        logger.warning("openFDA returned %s", resp.status_code)
        return 0

    data = resp.json()
    count = 0
    now = datetime.now(timezone.utc)

    for event in data.get('results', []):
        sid = event.get('safetyreportid', '')
        drugs = [d.get('medicinalproduct', '') for d in event.get('patient', {}).get('drug', [])[:5] if d.get('medicinalproduct')]
        reactions = [r.get('reactionmeddrapt', '') for r in event.get('patient', {}).get('reaction', [])[:5] if r.get('reactionmeddrapt')]

        if not drugs or not sid:
            continue

        title = f"FDA AE #{sid}: {', '.join(drugs[:3])} — {', '.join(reactions[:3])}"

        exists = conn.execute(text(
            "SELECT 1 FROM signals WHERE title ILIKE :pat LIMIT 1"
        ), {"pat": f"%{sid}%"}).scalar()
        if exists:
            continue

        seriousness = []
        if event.get('seriousnessdeath'):
            seriousness.append('death')
        if event.get('seriousnesshospitalization'):
            seriousness.append('hospitalization')
        if event.get('seriousnesslifethreatening'):
            seriousness.append('life-threatening')

        if 'death' in seriousness:
            anomaly, importance = 0.85, 0.9
        elif 'life-threatening' in seriousness:
            anomaly, importance = 0.75, 0.8
        else:
            anomaly, importance = 0.55, 0.65

        summary = f"Serious adverse event for {', '.join(drugs[:3])}. Reactions: {', '.join(reactions[:5])}."
        raw = json.dumps({
            'safety_report_id': sid, 'drugs': drugs, 'reactions': reactions,
            'seriousness': seriousness,
            'link': 'https://open.fda.gov/apis/drug/event/',
            'source_name': 'OpenFDA',
            'entities': extract_entities(title, summary),
        })

        conn.execute(text(
            "INSERT INTO signals (source, signal_type, category, title, summary, "
            "raw_data_json, sentiment_score, anomaly_score, importance, timestamp) "
            "VALUES (:src, :st, :cat, :title, :sum, :raw, :sent, :anom, :imp, :ts)"
        ), {
            "src": "open_fda", "st": "adverse_event", "cat": "healthcare",
            "title": title[:1024], "sum": summary[:500], "raw": raw,
            "sent": -0.6, "anom": round(anomaly, 4), "imp": round(importance, 4),
            "ts": now.isoformat(),
        })
        count += 1

    if count:
        conn.commit()
    return count


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    print(f"Connecting to {DB_URL} ...")
    engine = create_engine(DB_URL)

    with engine.connect() as conn:
        # Pre-count
        before = conn.execute(text("SELECT COUNT(*) FROM signals")).scalar()
        print(f"Signals before: {before}")

        print("\n--- 1/4: ClinicalTrials.gov ---")
        try:
            n = fetch_clinical_trials(conn)
            print(f"  -> {n} new clinical trial signals")
        except Exception as e:
            print(f"  -> ERROR: {e}")

        print("\n--- 2/4: AlienVault OTX ---")
        try:
            n = fetch_otx_pulses(conn)
            print(f"  -> {n} new OTX threat pulses")
        except Exception as e:
            print(f"  -> ERROR: {e}")

        print("\n--- 3/4: World Bank Economic Indicators ---")
        try:
            n = fetch_usda_fas(conn)
            print(f"  -> {n} new World Bank indicator signals")
        except Exception as e:
            print(f"  -> ERROR: {e}")

        print("\n--- 4/4: OpenFDA Adverse Events ---")
        try:
            n = fetch_open_fda(conn)
            print(f"  -> {n} new FDA adverse event signals")
        except Exception as e:
            print(f"  -> ERROR: {e}")

        # Post-count
        after = conn.execute(text("SELECT COUNT(*) FROM signals")).scalar()
        print(f"\n=== Summary ===")
        print(f"Signals before: {before}")
        print(f"Signals after:  {after}")
        print(f"New signals:    {after - before}")

        # Breakdown by source
        for src in ['clinicaltrials_gov', 'otx', 'worldbank', 'open_fda']:
            c = conn.execute(text(
                "SELECT COUNT(*) FROM signals WHERE source = :s"
            ), {"s": src}).scalar()
            print(f"  {src}: {c} total")


if __name__ == "__main__":
    main()
