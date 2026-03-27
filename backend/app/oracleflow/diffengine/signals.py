"""DiffSignalEmitter -- creates Signal records from PageDiff objects."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from urllib.parse import urlparse

from sqlalchemy.orm import Session

from app.oracleflow.constants import DiffType, SignalCategory, SignalSource
from app.oracleflow.models.signal import Signal
from app.oracleflow.models.site import PageDiff, SitePage

logger = logging.getLogger(__name__)

# Map DiffType to a human-readable signal type string
_DIFF_TYPE_TO_SIGNAL_TYPE = {
    DiffType.NEW_PAGE.value: "new_page_detected",
    DiffType.CONTENT_CHANGED.value: "content_change",
    DiffType.PAGE_REMOVED.value: "page_removed",
    DiffType.STRUCTURAL_CHANGE.value: "structural_change",
    DiffType.METADATA_CHANGE.value: "metadata_change",
}

# Severity weights for computing importance
_DIFF_SEVERITY = {
    DiffType.NEW_PAGE.value: 0.6,
    DiffType.CONTENT_CHANGED.value: 0.5,
    DiffType.PAGE_REMOVED.value: 0.8,
    DiffType.STRUCTURAL_CHANGE.value: 0.7,
    DiffType.METADATA_CHANGE.value: 0.3,
}


class DiffSignalEmitter:
    """Create a :class:`Signal` record from a :class:`PageDiff`."""

    def emit(
        self, db: Session, page: SitePage, diff: PageDiff
    ) -> Signal:
        """Persist and return a new Signal derived from *diff*.

        Importance is calculated as:

            ``page.importance_score * 0.6 + diff_severity * 0.4``

        clamped to ``[0.0, 1.0]``.

        The signal title uses ``[domain] page_path changed`` format so
        that the frontend can display the affected page at a glance.
        """
        signal_type = _DIFF_TYPE_TO_SIGNAL_TYPE.get(
            diff.diff_type, "unknown_change"
        )
        severity = _DIFF_SEVERITY.get(diff.diff_type, 0.4)

        # Use significance_score from the diff detail when available
        detail = diff.diff_detail_json or {}
        sig_score = detail.get("significance_score")
        if sig_score is not None:
            severity = max(severity, float(sig_score))

        importance = min(
            1.0, max(0.0, page.importance_score * 0.6 + severity * 0.4)
        )

        parsed = urlparse(page.url)
        domain = parsed.netloc or parsed.path.split("/")[0]
        page_path = parsed.path or "/"

        # Clean page path into readable name
        page_name = page_path.strip("/").split("/")[-1] if page_path.strip("/") else "homepage"
        page_name = page_name.replace("-", " ").replace("_", " ").title()

        title = f"{domain}: {page_name} page changed"

        # Map page type to signal category
        page_type = getattr(page, 'page_type', '') or ''
        category_map = {
            'policy_page': 'politics', 'pricing': 'economy', 'news': 'geopolitical',
            'blog': 'technology', 'product': 'economy', 'legal': 'politics',
            'homepage': 'economy', 'team_page': 'economy',
        }
        category = category_map.get(page_type, SignalCategory.OTHER.value)

        summary = diff.diff_summary or f"Change detected on {page_name} page ({domain})"

        # Look up the MonitoredSite's organization_id for org-scoping
        from app.oracleflow.models.site import MonitoredSite
        from sqlalchemy import select as sa_select
        site = db.execute(
            sa_select(MonitoredSite).where(MonitoredSite.id == page.site_id)
        ).scalar_one_or_none()
        site_org_id = site.organization_id if site else None

        signal = Signal(
            source='site_monitor',
            signal_type=signal_type,
            category=category,
            organization_id=site_org_id,
            title=title,
            summary=summary,
            raw_data_json={
                "page_id": page.id,
                "page_url": page.url,
                "diff_id": diff.id,
                "diff_type": diff.diff_type,
                "significance_score": detail.get("significance_score"),
                "change_percentage": detail.get("change_percentage"),
                "diff_detail": diff.diff_detail_json,
            },
            sentiment_score=0.0,
            anomaly_score=round(severity, 4),
            importance=round(importance, 4),
            timestamp=datetime.now(timezone.utc),
        )
        db.add(signal)
        db.flush()

        logger.info(
            "Emitted signal id=%s type=%s importance=%.2f for page %s",
            signal.id,
            signal_type,
            importance,
            page.url,
        )
        return signal
