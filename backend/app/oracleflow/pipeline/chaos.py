"""ChaosIndexCalculator -- compute the Global Chaos Index."""

from __future__ import annotations

import logging
import math
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.oracleflow.constants import SignalCategory
from app.oracleflow.models.signal import ChaosIndex, Signal

from .schemas import ChaosIndexSnapshot

logger = logging.getLogger(__name__)

# Category weights for global score (must sum to 1.0)
_CATEGORY_WEIGHTS: dict[str, float] = {
    SignalCategory.FINANCE.value: 0.18,
    SignalCategory.GEOPOLITICAL.value: 0.20,
    SignalCategory.SUPPLY_CHAIN.value: 0.13,
    SignalCategory.CYBER.value: 0.12,
    SignalCategory.CLIMATE.value: 0.10,
    SignalCategory.POLITICS.value: 0.15,
    SignalCategory.CRIME.value: 0.07,
    SignalCategory.ECONOMY.value: 0.05,
}

# Half-life for recency weighting (hours)
_RECENCY_HALF_LIFE_HOURS = 12.0

# Normalisation cap: raw score at or above this maps to 100.
_RAW_SCORE_CAP = 50.0


def _recency_weight(signal_ts: datetime) -> float:
    """Exponential decay weight (0, 1] based on signal age."""
    now = datetime.now(timezone.utc)
    age_hours = max((now - signal_ts).total_seconds() / 3600.0, 0.0)
    return math.exp(-math.log(2) * age_hours / _RECENCY_HALF_LIFE_HOURS)


def _normalize(raw: float, cap: float = _RAW_SCORE_CAP) -> float:
    """Map a raw score to the 0-100 range."""
    return round(min(raw / cap * 100.0, 100.0), 2)


class ChaosIndexCalculator:
    """Compute and persist the Global Chaos Index."""

    @staticmethod
    def compute(db: Session) -> ChaosIndexSnapshot:
        """Build a chaos index snapshot from the last 24 hours of signals.

        Steps:
        1. Query all signals from the last 24 hours.
        2. Group by ``SignalCategory`` (finance, geopolitical, supply_chain,
           cyber, climate).  Signals in other categories are ignored for the
           global index.
        3. Per-category raw score = sum(importance * anomaly_score * recency).
        4. Normalise each category to 0-100.
        5. Global score = weighted average of the five core categories.
        6. Persist a ``ChaosIndex`` row and return a snapshot.
        """
        cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
        stmt = select(Signal).where(Signal.timestamp >= cutoff)
        result = db.execute(stmt)
        signals: list[Signal] = list(result.scalars().all())

        # Bucket signals into the five core categories
        category_signals: dict[str, list[Signal]] = {cat: [] for cat in _CATEGORY_WEIGHTS}
        for sig in signals:
            if sig.category in category_signals:
                category_signals[sig.category].append(sig)

        # Compute per-category scores
        category_scores: dict[str, float] = {}
        for cat, sigs in category_signals.items():
            raw = sum(
                sig.importance * sig.anomaly_score * _recency_weight(sig.timestamp)
                for sig in sigs
            )
            category_scores[cat] = _normalize(raw)

        # Global weighted average
        global_score = round(
            sum(
                _CATEGORY_WEIGHTS[cat] * category_scores.get(cat, 0.0)
                for cat in _CATEGORY_WEIGHTS
            ),
            2,
        )

        now = datetime.now(timezone.utc)

        # Persist to DB
        signal_ids = [s.id for s in signals]
        record = ChaosIndex(
            timestamp=now,
            global_score=global_score,
            category_scores_json=category_scores,
            contributing_signal_ids_json=signal_ids,
        )
        db.add(record)
        db.flush()

        snapshot = ChaosIndexSnapshot(
            global_score=global_score,
            categories=category_scores,
            timestamp=now,
            contributing_signals=len(signals),
        )

        logger.info(
            "Chaos index computed: global=%.2f, signals=%d",
            global_score,
            len(signals),
        )
        return snapshot
