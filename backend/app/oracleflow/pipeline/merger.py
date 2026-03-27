"""SignalMerger -- query, deduplicate, and cluster recent signals."""

from __future__ import annotations

import logging
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from difflib import SequenceMatcher

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.oracleflow.models.signal import Signal

from .schemas import SignalCluster

logger = logging.getLogger(__name__)

_SIMILARITY_THRESHOLD = 0.80


def _titles_match(a: str, b: str) -> bool:
    """Return True when two titles are near-duplicates.

    Checks containment first (fast path) then falls back to
    SequenceMatcher ratio with an 80 % threshold.
    """
    la = a.lower().strip()
    lb = b.lower().strip()
    if la in lb or lb in la:
        return True
    return SequenceMatcher(None, la, lb).ratio() >= _SIMILARITY_THRESHOLD


class SignalMerger:
    """Merge and cluster recent signals."""

    @staticmethod
    def merge_recent(
        db: Session,
        hours: int = 24,
    ) -> list[SignalCluster]:
        """Query signals from the last *hours*, deduplicate, and cluster.

        Signals are grouped by ``(country_code, category)``.  Within each
        group, near-duplicate titles are collapsed so that only the
        highest-importance representative survives.

        Returns a list of :class:`SignalCluster` objects.
        """
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
        stmt = select(Signal).where(Signal.timestamp >= cutoff).order_by(Signal.timestamp.desc())
        result = db.execute(stmt)
        signals: list[Signal] = list(result.scalars().all())

        if not signals:
            return []

        # Group by (country_code, category)
        groups: dict[tuple[str, str], list[Signal]] = defaultdict(list)
        for sig in signals:
            key = (sig.country_code or "", sig.category or "")
            groups[key].append(sig)

        clusters: list[SignalCluster] = []
        for (country, category), group in groups.items():
            # Deduplicate within the group
            unique: list[Signal] = []
            for sig in group:
                is_dup = False
                for existing in unique:
                    if _titles_match(sig.title, existing.title):
                        is_dup = True
                        # Keep the one with higher importance
                        if sig.importance > existing.importance:
                            unique[unique.index(existing)] = sig
                        break
                if not is_dup:
                    unique.append(sig)

            if not unique:
                continue

            avg_sent = sum(s.sentiment_score for s in unique) / len(unique)
            combined_imp = sum(s.importance for s in unique)

            clusters.append(
                SignalCluster(
                    signals=[s.id for s in unique],
                    topic=category,
                    country_code=country,
                    avg_sentiment=round(avg_sent, 4),
                    combined_importance=round(combined_imp, 4),
                )
            )

        logger.info(
            "Merged %d signals into %d clusters (last %dh)",
            len(signals),
            len(clusters),
            hours,
        )
        return clusters
