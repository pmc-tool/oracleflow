"""OracleFlow background scheduler -- periodic chaos index and signal pipeline jobs."""

import difflib
import hashlib
import logging
import re
from datetime import datetime, timedelta, timezone
from urllib.parse import urlparse

import requests
from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy import select

from app.oracleflow.database import get_session
from app.oracleflow.pipeline.chaos import ChaosIndexCalculator

logger = logging.getLogger(__name__)

_scheduler = None


def start_scheduler(app):
    """Start the APScheduler BackgroundScheduler with OracleFlow jobs."""
    global _scheduler

    if _scheduler is not None:
        logger.warning("Scheduler already running, skipping duplicate start")
        return

    _scheduler = BackgroundScheduler()

    # Chaos index computation every 5 minutes
    _scheduler.add_job(
        _compute_chaos,
        'interval',
        seconds=300,
        args=[app],
        id='oracleflow_chaos_index',
        replace_existing=True,
        max_instances=1,
        coalesce=True,
        misfire_grace_time=300,
    )

    # Signal pipeline (merge + score + alert evaluation) every 5 minutes
    _scheduler.add_job(
        _run_pipeline,
        'interval',
        seconds=300,
        args=[app],
        id='oracleflow_signal_pipeline',
        replace_existing=True,
        max_instances=1,
        coalesce=True,
        misfire_grace_time=300,
    )

    # Global RSS feed ingest every 15 minutes
    _scheduler.add_job(
        _fetch_feeds,
        'interval',
        seconds=900,
        args=[app],
        id='oracleflow_feed_ingest',
        replace_existing=True,
        max_instances=1,
        coalesce=True,
        misfire_grace_time=300,
    )

    # Page monitoring every 30 minutes
    _scheduler.add_job(
        _monitor_pages,
        'interval',
        seconds=1800,
        args=[app],
        id='oracleflow_page_monitor',
        replace_existing=True,
        max_instances=1,
        coalesce=True,
        misfire_grace_time=300,
    )

    # Run feeds once immediately on startup
    _scheduler.add_job(
        _fetch_feeds,
        args=[app],
        id='oracleflow_feed_startup',
        replace_existing=True,
        max_instances=1,
        coalesce=True,
        misfire_grace_time=300,
    )

    _scheduler.start()
    logger.info(
        "OracleFlow scheduler started "
        "(feeds every 15min, chaos+pipeline every 5min, page monitor every 30min)"
    )


def _compute_chaos(app):
    """Compute and persist the global chaos index."""
    with app.app_context():
        db = get_session()
        try:
            snapshot = ChaosIndexCalculator.compute(db)
            db.commit()
            logger.debug("Chaos index computation completed")

            # Broadcast new chaos score via real-time layer
            try:
                from app.oracleflow.realtime import broadcast_chaos_update
                broadcast_chaos_update({
                    'global_score': snapshot.global_score,
                    'categories': snapshot.categories,
                    'timestamp': snapshot.timestamp.isoformat() if snapshot.timestamp else None,
                })
            except Exception as rt_err:
                logger.debug("Chaos real-time broadcast failed: %s", rt_err)

        except Exception as e:
            db.rollback()
            logger.error("Chaos index computation failed: %s", e)
        finally:
            db.close()


def _fetch_feeds(app):
    """Fetch signals from all global RSS feeds + USGS + NVD + GDACS."""
    with app.app_context():
        db = get_session()
        try:
            from app.oracleflow.feeds.rss import fetch_global_feeds
            from app.oracleflow.feeds.usgs import fetch_earthquakes
            from app.oracleflow.feeds.acled import fetch_conflicts
            from app.oracleflow.feeds.nasa import fetch_wildfires
            from app.oracleflow.feeds.nvd import fetch_cves
            from app.oracleflow.feeds.gdacs import fetch_gdacs_alerts
            from app.oracleflow.feeds.clinicaltrials import fetch_clinical_trials
            from app.oracleflow.feeds.otx import fetch_otx_pulses
            from app.oracleflow.feeds.usda_fas import fetch_usda_fas
            from app.oracleflow.feeds.open_fda import fetch_open_fda

            rss_signals = fetch_global_feeds(db)
            quake_signals = fetch_earthquakes(db)
            conflict_signals = fetch_conflicts(db)
            fire_signals = fetch_wildfires(db)
            cve_count = fetch_cves(db)
            gdacs_count = fetch_gdacs_alerts(db)
            clinical_count = fetch_clinical_trials(db)
            otx_count = fetch_otx_pulses(db)
            usda_count = fetch_usda_fas(db)
            fda_count = fetch_open_fda(db)
            db.commit()
            total = (len(rss_signals) + len(quake_signals) + len(conflict_signals)
                     + len(fire_signals) + cve_count + gdacs_count
                     + clinical_count + otx_count + usda_count + fda_count)
            if total > 0:
                logger.info(
                    f"Feed ingest: {len(rss_signals)} RSS + {len(quake_signals)} earthquakes"
                    f" + {len(conflict_signals)} conflicts + {len(fire_signals)} fires"
                    f" + {cve_count} CVEs + {gdacs_count} GDACS alerts"
                    f" + {clinical_count} clinical trials + {otx_count} OTX pulses"
                    f" + {usda_count} World Bank + {fda_count} FDA adverse events"
                    f" = {total} new signals"
                )
        except Exception as e:
            db.rollback()
            logger.error("Feed ingest failed: %s", e)
        finally:
            db.close()


def _run_pipeline(app):
    """Run signal merge, anomaly scoring, and alert evaluation pipeline."""
    with app.app_context():
        db = get_session()
        try:
            from app.oracleflow.pipeline.merger import SignalMerger
            from app.oracleflow.pipeline.scorer import AnomalyScorer
            from app.oracleflow.models.signal import Signal, Alert, AlertRuleDB
            from app.oracleflow.alerts.rules import RuleEvaluator
            from app.oracleflow.constants import AlertSeverity

            # Merge recent signals into clusters
            clusters = SignalMerger.merge_recent(db)

            # Collect all signal IDs from clusters for scoring
            signal_ids = []
            for cluster in clusters:
                signal_ids.extend(cluster.signals)

            if signal_ids:
                # Load signals and score them
                stmt = select(Signal).where(Signal.id.in_(signal_ids))
                result = db.execute(stmt)
                signals = list(result.scalars().all())

                anomaly_results = AnomalyScorer.score(db, signals)

                # Update anomaly scores on signal records
                score_map = {ar.signal_id: ar.anomaly_score for ar in anomaly_results}
                for sig in signals:
                    if sig.id in score_map:
                        sig.anomaly_score = score_map[sig.id]

                db.commit()
                logger.debug(
                    "Signal pipeline completed: %d clusters, %d signals scored",
                    len(clusters),
                    len(anomaly_results),
                )

                # --- Broadcast top 5 highest-anomaly signals via real-time layer ---
                try:
                    from app.oracleflow.realtime import broadcast_signal
                    top_signals = sorted(signals, key=lambda s: s.anomaly_score or 0, reverse=True)[:5]
                    for sig in top_signals:
                        broadcast_signal({
                            'id': sig.id,
                            'title': sig.title,
                            'category': sig.category,
                            'anomaly_score': sig.anomaly_score,
                            'sentiment_score': sig.sentiment_score,
                            'timestamp': sig.timestamp.isoformat() if sig.timestamp else None,
                        }, org_id=sig.organization_id)
                except Exception as rt_err:
                    logger.debug("Real-time broadcast failed: %s", rt_err)

                # --- Alert evaluation ---
                _evaluate_alerts(db, signals)
            else:
                logger.debug("Signal pipeline: no signals to process")
        except Exception as e:
            db.rollback()
            logger.error("Signal pipeline failed: %s", e)
        finally:
            db.close()


def _evaluate_alerts(db, scored_signals=None):
    """Evaluate recently scored signals against alert rules and create Alert records.

    If *scored_signals* is provided, evaluate those directly. Otherwise, query
    signals from the last 5 minutes with anomaly_score >= 0.7.
    """
    from app.oracleflow.models.signal import Signal, Alert, AlertRuleDB
    from app.oracleflow.alerts.rules import RuleEvaluator
    from app.oracleflow.constants import AlertSeverity

    try:
        # Determine which signals to evaluate
        if scored_signals is not None:
            high_signals = [s for s in scored_signals if s.anomaly_score >= 0.7]
        else:
            cutoff = datetime.now(timezone.utc) - timedelta(minutes=5)
            stmt = (
                select(Signal)
                .where(Signal.timestamp >= cutoff)
                .where(Signal.anomaly_score >= 0.7)
            )
            result = db.execute(stmt)
            high_signals = list(result.scalars().all())

        if not high_signals:
            return

        # Load all enabled alert rules from DB
        rule_stmt = select(AlertRuleDB).where(AlertRuleDB.enabled == True)  # noqa: E712
        rule_result = db.execute(rule_stmt)
        db_rules = list(rule_result.scalars().all())

        if not db_rules:
            # Fallback: create alerts for signals with anomaly >= 0.8 even without rules
            _create_fallback_alerts(db, high_signals)
            return

        # Convert DB rules to Pydantic rules for the evaluator
        pydantic_rules = [r.to_pydantic() for r in db_rules]

        alerts_created = 0
        for signal in high_signals:
            matched_rules = RuleEvaluator.evaluate(signal, pydantic_rules)
            for rule in matched_rules:
                # Determine severity from rule or signal anomaly score
                if signal.anomaly_score >= 0.9:
                    severity = AlertSeverity.CRITICAL.value
                elif signal.anomaly_score >= 0.8:
                    severity = AlertSeverity.HIGH.value
                else:
                    severity = rule.severity if isinstance(rule.severity, str) else rule.severity.value

                alert = Alert(
                    signal_id=signal.id,
                    alert_type=rule.condition_type,
                    severity=severity,
                    message=f"[{rule.name}] {signal.title} (anomaly={signal.anomaly_score:.2f})",
                )
                db.add(alert)
                alerts_created += 1

                # Create notifications for matching users
                _create_notifications_for_signal(db, signal, severity,
                    f"[{rule.name}] {signal.title}",
                    f"Anomaly score: {signal.anomaly_score:.2f} — {signal.summary or signal.title}")

        db.commit()
        if alerts_created:
            logger.info("Alert evaluation: created %d alerts from %d high-anomaly signals",
                        alerts_created, len(high_signals))

    except Exception as e:
        db.rollback()
        logger.error("Alert evaluation failed: %s", e)


def _create_fallback_alerts(db, signals):
    """Create alerts for very high anomaly signals when no rules are configured."""
    from app.oracleflow.models.signal import Alert
    from app.oracleflow.constants import AlertSeverity

    alerts_created = 0
    for signal in signals:
        if signal.anomaly_score < 0.8:
            continue

        if signal.anomaly_score >= 0.9:
            severity = AlertSeverity.CRITICAL.value
        else:
            severity = AlertSeverity.HIGH.value

        alert = Alert(
            signal_id=signal.id,
            alert_type="anomaly_threshold",
            severity=severity,
            message=f"High anomaly detected: {signal.title} (anomaly={signal.anomaly_score:.2f})",
        )
        db.add(alert)
        alerts_created += 1

        # Create notifications for matching users
        _create_notifications_for_signal(db, signal, severity,
            f"High anomaly: {signal.title}",
            f"Anomaly score: {signal.anomaly_score:.2f} — {signal.summary or signal.title}")

    if alerts_created:
        db.commit()
        logger.info("Fallback alerts: created %d alerts for high-anomaly signals", alerts_created)


def _create_notifications_for_signal(db, signal, severity, title, message):
    """Create Notification records for users whose interest_categories match the signal.

    Queries UserPreferences to find users in the signal's organization (or all
    users if the signal has no org) whose interest_categories overlap with the
    signal's category, then creates one Notification per matching user.
    """
    from app.oracleflow.models.signal import Notification
    from app.oracleflow.auth.models import UserPreferences, User

    try:
        from app.oracleflow.alerts.delivery import send_alert_email

        # Build base query for users
        if signal.organization_id:
            # Org-specific signal — only notify users in THAT org
            user_stmt = (
                select(User.id, User.organization_id)
                .where(User.organization_id == signal.organization_id)
                .where(User.is_active == True)  # noqa: E712
            )
        else:
            # Global signal — use category-specific thresholds.
            # Finance/crypto signals are meaningful at lower anomaly scores.
            _category = (signal.category or "").lower()
            _CATEGORY_THRESHOLDS = {
                "finance": 0.6,
                "economy": 0.65,
                "crypto": 0.6,
                "cyber": 0.65,
            }
            _threshold = _CATEGORY_THRESHOLDS.get(_category, 0.75)

            if signal.anomaly_score is None or signal.anomaly_score < _threshold:
                return
            user_stmt = (
                select(User.id, User.organization_id)
                .where(User.is_active == True)  # noqa: E712
            )

        users = list(db.execute(user_stmt).all())
        if not users:
            return

        # Load preferences for these users
        user_ids = [u.id for u in users]
        pref_stmt = (
            select(UserPreferences)
            .where(UserPreferences.user_id.in_(user_ids))
        )
        prefs = {p.user_id: p for p in db.execute(pref_stmt).scalars().all()}

        signal_category = (signal.category or "").lower()
        notified = 0

        for user_row in users:
            uid = user_row.id
            org_id = user_row.organization_id

            # Check if user's interest categories match signal category
            user_pref = prefs.get(uid)
            if user_pref and user_pref.interest_categories:
                categories = [c.lower() for c in user_pref.interest_categories]
                if signal_category and signal_category not in categories:
                    continue
            # If user has no preferences, send notification anyway (default: all)

            notification = Notification(
                user_id=uid,
                organization_id=org_id,
                signal_id=signal.id,
                title=title[:512],
                message=(message or "")[:2000],
                severity=severity,
            )
            db.add(notification)
            notified += 1

            # Send email alert for this user
            try:
                user_obj = db.execute(
                    select(User).where(User.id == uid)
                ).scalar_one_or_none()
                if user_obj and user_obj.email:
                    raw = signal.raw_data_json or {}
                    signal_url = raw.get('url') or raw.get('link') or None
                    send_alert_email(
                        user_email=user_obj.email,
                        user_name=user_obj.name or user_obj.email,
                        signal_title=signal.title,
                        signal_summary=signal.summary,
                        severity=severity,
                        anomaly_score=signal.anomaly_score or 0.0,
                        category=signal.category or 'other',
                        signal_url=signal_url,
                    )
            except Exception as email_err:
                logger.warning("Email delivery failed for user %s: %s", uid, email_err)

        if notified:
            logger.debug("Created %d notifications for signal %d", notified, signal.id)

    except Exception as e:
        logger.warning("Failed to create notifications for signal %s: %s", signal.id, e)


def _monitor_pages(app):
    """Re-fetch monitored pages, take snapshots, compute diffs, and emit signals.

    Processes up to 50 active pages per run, prioritizing never-checked pages
    and those least recently crawled.  Skips pages checked within the last
    15 minutes.  Uses the full diff engine (PageComparator + DiffSignalEmitter)
    when possible, falling back to a simplified content-hash comparison if the
    diff engine components fail.
    """
    with app.app_context():
        db = get_session()
        try:
            from app.oracleflow.models.site import MonitoredSite, SitePage, PageDiff
            from app.oracleflow.discovery.snapshot import SnapshotManager
            from sqlalchemy import or_

            # Skip pages that were checked within the last 15 minutes
            recent_cutoff = datetime.now(timezone.utc) - timedelta(minutes=15)

            # Query active pages, prioritize never-checked (NULL last_crawled)
            # then least recently crawled, batch of 50
            stmt = (
                select(SitePage)
                .join(MonitoredSite, SitePage.site_id == MonitoredSite.id)
                .where(MonitoredSite.status == "active")
                .where(SitePage.is_active == True)  # noqa: E712
                .where(
                    or_(
                        SitePage.last_crawled.is_(None),
                        SitePage.last_crawled < recent_cutoff,
                    )
                )
                .order_by(SitePage.last_crawled.asc().nulls_first())
                .limit(50)
            )
            result = db.execute(stmt)
            pages = list(result.scalars().all())

            if not pages:
                logger.debug("Page monitor: no active pages to check")
                return

            snapshot_mgr = SnapshotManager()
            diffs_created = 0
            signals_created = 0

            for page in pages:
                try:
                    # Get previous snapshot before fetching new content
                    old_snapshot = snapshot_mgr.get_latest(db, page.id)

                    # Fetch page content
                    text, html, metadata = _fetch_page_content(page.url)

                    # Take new snapshot
                    new_snapshot = snapshot_mgr.take_snapshot(
                        db,
                        page_id=page.id,
                        content_text=text,
                        content_html=html,
                        metadata=metadata,
                    )

                    # Update page last_crawled and content_hash
                    page.last_crawled = datetime.now(timezone.utc)
                    page.content_hash = new_snapshot.content_hash

                    # Compare snapshots if we have a previous one
                    if old_snapshot and old_snapshot.content_hash != new_snapshot.content_hash:
                        diff_results = _compare_snapshots(old_snapshot, new_snapshot)

                        for diff_result in diff_results:
                            # Create PageDiff record
                            page_diff = PageDiff(
                                page_id=page.id,
                                old_snapshot_id=old_snapshot.id,
                                new_snapshot_id=new_snapshot.id,
                                diff_type=diff_result.diff_type if isinstance(diff_result.diff_type, str) else diff_result.diff_type.value,
                                diff_summary=diff_result.summary,
                                diff_detail_json=diff_result.detail,
                                detected_at=datetime.now(timezone.utc),
                            )
                            db.add(page_diff)
                            db.flush()
                            diffs_created += 1

                            # Emit signal from diff
                            signal = _emit_signal_from_diff(db, page, page_diff)
                            if signal:
                                signals_created += 1

                except Exception as e:
                    logger.warning("Failed to monitor page %s: %s", page.url, e)
                    continue

            db.commit()
            if diffs_created or signals_created:
                logger.info(
                    "Page monitor: checked %d pages, %d diffs detected, %d signals emitted",
                    len(pages), diffs_created, signals_created,
                )
            else:
                logger.debug("Page monitor: checked %d pages, no changes detected", len(pages))

        except Exception as e:
            db.rollback()
            logger.error("Page monitoring failed: %s", e)
        finally:
            db.close()


def _fetch_page_content(url):
    """Fetch a page and return (text, html, metadata).

    Uses MonitorFetcher which tries Scrapling first and falls back to
    requests internally.
    """
    from app.oracleflow.diffengine.fetcher import MonitorFetcher
    fetcher = MonitorFetcher()
    return fetcher.fetch_page(url, anti_bot_level="low")


def _compare_snapshots(old_snapshot, new_snapshot):
    """Compare two snapshots using PageComparator, with simplified fallback.

    Returns a list of DiffResult objects.  Each result carries ``detail``
    with ``change_percentage`` and ``significance_score`` (0-1).
    """
    try:
        from app.oracleflow.diffengine.comparator import PageComparator
        comparator = PageComparator()
        results = comparator.compare(old_snapshot, new_snapshot)
        if results:
            # Ensure every result has significance_score in its detail
            for r in results:
                if "significance_score" not in r.detail:
                    pct = r.detail.get("change_percentage", 50.0)
                    r.detail["significance_score"] = round(min(1.0, pct / 100.0), 4)
                if "change_percentage" not in r.detail:
                    r.detail["change_percentage"] = round(
                        r.detail.get("significance_score", 0.5) * 100, 2
                    )
            return results
    except Exception as e:
        logger.debug("PageComparator failed, using inline diff: %s", e)

    # ---- Inline fallback using difflib ----
    from app.oracleflow.diffengine.schemas import DiffResult
    from app.oracleflow.constants import DiffType

    old_text = old_snapshot.content_text or ""
    new_text = new_snapshot.content_text or ""

    matcher = difflib.SequenceMatcher(None, old_text, new_text)
    ratio = matcher.ratio()
    change_pct = round((1 - ratio) * 100, 2)

    # Collect a sample of changed phrases (up to 5)
    changed_phrases: list[str] = []
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag in ("replace", "insert"):
            phrase = new_text[j1:j2].strip()
            if phrase and len(phrase) < 200:
                changed_phrases.append(phrase)
            if len(changed_phrases) >= 5:
                break

    # Significance: small edits < 5% are low, > 30% are high
    if change_pct < 5:
        significance = round(change_pct / 10, 4)
    elif change_pct < 30:
        significance = round(0.3 + (change_pct - 5) / 50, 4)
    else:
        significance = round(min(1.0, 0.8 + (change_pct - 30) / 100), 4)

    summary = f"{change_pct}% content changed"
    if changed_phrases:
        summary += f"; samples: {', '.join(p[:60] for p in changed_phrases[:3])}"

    # Produce unified diff for detail
    old_lines = old_text.splitlines(keepends=True)
    new_lines = new_text.splitlines(keepends=True)
    unified = list(difflib.unified_diff(old_lines, new_lines, n=2))
    # Truncate diff to avoid huge JSON blobs
    diff_text = "".join(unified[:200])

    return [
        DiffResult(
            diff_type=DiffType.CONTENT_CHANGED,
            summary=summary,
            detail={
                "old_hash": old_snapshot.content_hash,
                "new_hash": new_snapshot.content_hash,
                "change_percentage": change_pct,
                "similarity_ratio": round(ratio, 4),
                "significance_score": significance,
                "changed_phrases": changed_phrases,
                "unified_diff": diff_text[:10000],
            },
            old_hash=old_snapshot.content_hash,
            new_hash=new_snapshot.content_hash,
        )
    ]


def _emit_signal_from_diff(db, page, page_diff):
    """Create a Signal from a PageDiff using DiffSignalEmitter, with fallback.

    Returns the Signal or None on failure.
    """
    try:
        from app.oracleflow.diffengine.signals import DiffSignalEmitter
        emitter = DiffSignalEmitter()
        signal = emitter.emit(db, page, page_diff)
        # Patch raw_data_json to always include the full page_url
        if signal and signal.raw_data_json:
            signal.raw_data_json = {**signal.raw_data_json, "page_url": page.url}
        return signal
    except Exception as e:
        logger.debug("DiffSignalEmitter failed, using inline signal creation: %s", e)

    # ---- Inline fallback ----
    from app.oracleflow.models.signal import Signal
    from app.oracleflow.constants import SignalSource, SignalCategory

    parsed = urlparse(page.url)
    domain = parsed.netloc or parsed.path.split("/")[0]
    page_path = parsed.path or "/"

    # Clean page path into readable name: /contact-us/ → "Contact Us"
    page_name = page_path.strip("/").split("/")[-1] if page_path.strip("/") else "homepage"
    page_name = page_name.replace("-", " ").replace("_", " ").title()

    # Map page type to category
    page_type = getattr(page, 'page_type', '') or ''
    category_map = {
        'policy_page': 'politics', 'pricing': 'economy', 'news': 'geopolitical',
        'blog': 'technology', 'product': 'economy', 'legal': 'politics',
        'homepage': 'economy', 'team_page': 'economy',
    }
    category = category_map.get(page_type, 'other')

    # Extract significance from diff detail if available
    detail = page_diff.diff_detail_json or {}
    significance = detail.get("significance_score", 0.5)
    change_pct = detail.get("change_percentage", 0)

    # Clean the summary — strip any JS/code fragments
    raw_summary = page_diff.diff_summary or f"Change detected on {page.url}"
    # Remove anything that looks like code
    clean_summary = re.sub(r'function\s*\([^)]*\).*?[;}]', '', raw_summary)
    clean_summary = re.sub(r'var\s+\w+\s*=.*?;', '', clean_summary)
    clean_summary = re.sub(r'\{[^{}]*:[^{}]*\}', '', clean_summary)
    clean_summary = re.sub(r'\s+', ' ', clean_summary).strip()
    if not clean_summary or len(clean_summary) < 10:
        clean_summary = f"{change_pct:.0f}% of content changed on {page_name} page"

    # Look up the MonitoredSite's organization_id for org-scoping
    from app.oracleflow.models.site import MonitoredSite
    site = db.execute(
        select(MonitoredSite).where(MonitoredSite.id == page.site_id)
    ).scalar_one_or_none()
    site_org_id = site.organization_id if site else None

    signal = Signal(
        source='site_monitor',
        signal_type="page_change",
        category=category,
        organization_id=site_org_id,
        title=f"{domain}: {page_name} page changed",
        summary=clean_summary,
        raw_data_json={
            "page_id": page.id,
            "page_url": page.url,
            "diff_id": page_diff.id,
            "diff_type": page_diff.diff_type,
            "significance_score": significance,
            "change_percentage": detail.get("change_percentage"),
        },
        sentiment_score=0.0,
        anomaly_score=round(significance, 4),
        importance=round(
            min(1.0, max(0.0, page.importance_score * 0.6 + significance * 0.4)),
            4,
        ),
        timestamp=datetime.now(timezone.utc),
    )
    db.add(signal)
    db.flush()
    return signal
