import requests
from datetime import datetime, timezone, timedelta
from app.oracleflow.models.signal import Signal
from app.oracleflow.entities.signal_extractor import extract_entities

def fetch_cves(db, hours=24):
    """Fetch recent CVEs from NVD API (free, no key needed)."""
    now = datetime.now(timezone.utc)
    start = (now - timedelta(hours=hours)).strftime('%Y-%m-%dT%H:%M:%S.000')
    end = now.strftime('%Y-%m-%dT%H:%M:%S.000')

    url = f"https://services.nvd.nist.gov/rest/json/cves/2.0?resultsPerPage=20&pubStartDate={start}&pubEndDate={end}"

    try:
        resp = requests.get(url, timeout=30)
        if resp.status_code != 200:
            return 0
        data = resp.json()
        count = 0
        for vuln in data.get('vulnerabilities', []):
            cve = vuln.get('cve', {})
            cve_id = cve.get('id', '')

            # Check duplicate
            existing = db.query(Signal).filter(Signal.title.ilike(f'%{cve_id}%')).first()
            if existing:
                continue

            # Extract info
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

            # Anomaly from CVSS
            anomaly = min(1.0, cvss_score / 10.0)

            entities = extract_entities(f"{cve_id} {desc}", '')
            entities['cves'] = [cve_id]
            if cvss_score > 0:
                entities['cvss'] = {'score': cvss_score, 'severity': severity}

            signal = Signal(
                source='nvd',
                signal_type='cve',
                category='cyber',
                title=f"{cve_id} ({severity}, CVSS {cvss_score})",
                summary=desc[:500],
                raw_data_json={
                    'cve_id': cve_id,
                    'cvss_score': cvss_score,
                    'severity': severity,
                    'link': f"https://nvd.nist.gov/vuln/detail/{cve_id}",
                    'entities': entities,
                },
                sentiment_score=-0.5 if cvss_score > 7 else -0.2,
                anomaly_score=round(anomaly, 4),
                importance=round(min(1.0, 0.5 + cvss_score / 20), 4),
                timestamp=datetime.now(timezone.utc),
            )
            db.add(signal)
            count += 1

        db.commit()
        return count
    except Exception as e:
        db.rollback()
        return 0
