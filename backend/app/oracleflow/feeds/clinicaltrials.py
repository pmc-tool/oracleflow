"""Fetch recently updated clinical trials from ClinicalTrials.gov (free, no API key)."""

import logging
import requests
from datetime import datetime, timezone, timedelta

from app.oracleflow.models.signal import Signal
from app.oracleflow.entities.signal_extractor import extract_entities

logger = logging.getLogger(__name__)


def fetch_clinical_trials(db, days=3):
    """Fetch recently updated clinical trials from ClinicalTrials.gov (free, no key).

    Uses the v2 API to pull studies updated within the last *days* days,
    sorted by most recently updated first.  Deduplicates by NCT ID.
    """
    end = datetime.now(timezone.utc)
    start = end - timedelta(days=days)
    start_str = start.strftime('%Y-%m-%d')
    end_str = end.strftime('%Y-%m-%d')

    url = (
        f"https://clinicaltrials.gov/api/v2/studies"
        f"?query.term=AREA[LastUpdatePostDate]RANGE[{start_str},{end_str}]"
        f"&pageSize=20&sort=LastUpdatePostDate:desc&format=json"
    )

    try:
        resp = requests.get(url, timeout=30)
        if resp.status_code != 200:
            logger.warning("ClinicalTrials.gov returned %s", resp.status_code)
            return 0

        data = resp.json()
        count = 0
        for study in data.get('studies', []):
            protocol = study.get('protocolSection', {})
            id_module = protocol.get('identificationModule', {})
            status_module = protocol.get('statusModule', {})
            desc_module = protocol.get('descriptionModule', {})

            nct_id = id_module.get('nctId', '')
            title = id_module.get('briefTitle', id_module.get('officialTitle', ''))
            status = status_module.get('overallStatus', '')
            phase = ', '.join(protocol.get('designModule', {}).get('phases', []))
            brief_summary = desc_module.get('briefSummary', '')

            if not title or not nct_id:
                continue

            # Dedup by NCT ID
            existing = db.query(Signal).filter(Signal.title.ilike(f'%{nct_id}%')).first()
            if existing:
                continue

            # Importance by phase
            phase_importance = {
                'PHASE3': 0.85, 'PHASE2': 0.7, 'PHASE1': 0.6, 'PHASE4': 0.8,
            }
            importance = 0.5
            for p, imp in phase_importance.items():
                if p in (phase or '').upper().replace(' ', ''):
                    importance = imp
                    break

            entities = extract_entities(title, brief_summary[:200] if brief_summary else '')

            signal = Signal(
                source='clinicaltrials_gov',
                signal_type='clinical_trial',
                category='healthcare',
                title=f"[{nct_id}] {title} ({phase or 'N/A'} - {status})",
                summary=brief_summary[:500] if brief_summary else f"Clinical trial {nct_id} status: {status}",
                raw_data_json={
                    'nct_id': nct_id,
                    'phase': phase,
                    'status': status,
                    'link': f"https://clinicaltrials.gov/study/{nct_id}",
                    'source_name': 'ClinicalTrials.gov',
                    'entities': entities,
                },
                sentiment_score=0.3 if status in ('RECRUITING', 'ACTIVE_NOT_RECRUITING') else 0.0,
                anomaly_score=round(importance * 0.6, 4),
                importance=round(importance, 4),
                timestamp=datetime.now(timezone.utc),
            )
            db.add(signal)
            count += 1

        db.commit()
        logger.info("ClinicalTrials.gov: fetched %d new trials", count)
        return count

    except Exception as e:
        db.rollback()
        logger.error("ClinicalTrials.gov fetch failed: %s", e)
        return 0
