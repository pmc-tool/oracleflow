"""Fetch drug safety / adverse event reports from OpenFDA (free, no API key).

The openFDA Drug Adverse Events endpoint provides public access to FDA
Adverse Event Reporting System (FAERS) data.  This feed pulls the most
recent serious adverse event reports and converts them to signals.
"""

import logging
import requests
from datetime import datetime, timezone, timedelta

from app.oracleflow.models.signal import Signal
from app.oracleflow.entities.signal_extractor import extract_entities

logger = logging.getLogger(__name__)


def fetch_open_fda(db):
    """Fetch recent drug adverse event reports from openFDA (free, no key).

    Queries the Drug Adverse Events API for serious reports received in the
    last 30 days, limited to 20 results.
    """
    end = datetime.now(timezone.utc)
    start = end - timedelta(days=30)
    start_str = start.strftime('%Y%m%d')
    end_str = end.strftime('%Y%m%d')

    url = (
        f"https://api.fda.gov/drug/event.json"
        f"?search=serious:1"
        f"&limit=20&sort=receivedate:desc"
    )

    try:
        resp = requests.get(url, timeout=30)
        if resp.status_code != 200:
            logger.warning("openFDA returned %s", resp.status_code)
            return 0

        data = resp.json()
        results = data.get('results', [])
        count = 0

        for event in results:
            safety_report_id = event.get('safetyreportid', '')
            receive_date = event.get('receivedate', '')
            serious = event.get('serious', 0)

            # Get drug names
            drugs = event.get('patient', {}).get('drug', [])
            drug_names = []
            for d in drugs[:5]:
                name = d.get('medicinalproduct', '')
                if name:
                    drug_names.append(name)

            # Get reactions
            reactions = event.get('patient', {}).get('reaction', [])
            reaction_names = []
            for r in reactions[:5]:
                name = r.get('reactionmeddrapt', '')
                if name:
                    reaction_names.append(name)

            if not drug_names or not safety_report_id:
                continue

            title = f"FDA AE #{safety_report_id}: {', '.join(drug_names[:3])} — {', '.join(reaction_names[:3])}"

            # Dedup
            if db.query(Signal).filter(Signal.title.ilike(f'%{safety_report_id}%')).first():
                continue

            summary = (
                f"Serious adverse event report for {', '.join(drug_names[:3])}. "
                f"Reactions: {', '.join(reaction_names[:5])}. "
                f"Report date: {receive_date}."
            )

            entities = extract_entities(title, summary)
            entities['drugs'] = drug_names[:5]
            entities['reactions'] = reaction_names[:5]

            # Seriousness flags
            seriousness_flags = []
            if event.get('seriousnessdeath'):
                seriousness_flags.append('death')
            if event.get('seriousnesshospitalization'):
                seriousness_flags.append('hospitalization')
            if event.get('seriousnesslifethreatening'):
                seriousness_flags.append('life-threatening')
            if event.get('seriousnessdisabling'):
                seriousness_flags.append('disabling')

            # Higher anomaly for death/life-threatening
            if 'death' in seriousness_flags:
                anomaly = 0.85
                importance = 0.9
            elif 'life-threatening' in seriousness_flags:
                anomaly = 0.75
                importance = 0.8
            else:
                anomaly = 0.55
                importance = 0.65

            signal = Signal(
                source='open_fda',
                signal_type='adverse_event',
                category='healthcare',
                title=title[:1024],
                summary=summary[:500],
                raw_data_json={
                    'safety_report_id': safety_report_id,
                    'drugs': drug_names,
                    'reactions': reaction_names,
                    'seriousness': seriousness_flags,
                    'receive_date': receive_date,
                    'link': 'https://open.fda.gov/apis/drug/event/',
                    'source_name': 'OpenFDA',
                    'entities': entities,
                },
                sentiment_score=-0.6,
                anomaly_score=round(anomaly, 4),
                importance=round(importance, 4),
                timestamp=datetime.now(timezone.utc),
            )
            db.add(signal)
            count += 1

        db.commit()
        logger.info("openFDA: fetched %d new adverse event signals", count)
        return count

    except Exception as e:
        db.rollback()
        logger.error("openFDA fetch failed: %s", e)
        return 0
