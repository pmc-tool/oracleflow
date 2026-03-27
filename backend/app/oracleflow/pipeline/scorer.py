"""AnomalyScorer -- compute per-signal anomaly scores."""

from __future__ import annotations

import logging
import math
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.oracleflow.models.signal import Signal

from .schemas import AnomalyResult

logger = logging.getLogger(__name__)

# Tunable constants
_VELOCITY_WINDOW_HOURS = 6
_VELOCITY_HIGH_THRESHOLD = 10
_RECENCY_HALF_LIFE_HOURS = 6.0


def _recency_weight(signal_ts: datetime) -> float:
    """Exponential decay: newer signals score higher.

    Returns a value in (0, 1] where 1 means *just now* and the value
    halves every ``_RECENCY_HALF_LIFE_HOURS`` hours.
    """
    now = datetime.now(timezone.utc)
    age_hours = max((now - signal_ts).total_seconds() / 3600.0, 0.0)
    return math.exp(-math.log(2) * age_hours / _RECENCY_HALF_LIFE_HOURS)


class AnomalyScorer:
    """Score signals for anomalous behaviour."""

    @staticmethod
    def score(
        db: Session,
        signals: list[Signal],
    ) -> list[AnomalyResult]:
        """Compute an anomaly score (0-1) for each signal.

        Scoring dimensions:
        * **Velocity** -- how many signals share the same category + country
          in the last 6 hours.  More than 10 is considered highly anomalous.
        * **Cross-source** -- the same topic reported by multiple sources
          (e.g. *scrapling* and *worldmonitor*) increases confidence.
        * **Recency** -- exponential decay; newer signals are more anomalous.
        """
        if not signals:
            return []

        cutoff = datetime.now(timezone.utc) - timedelta(hours=_VELOCITY_WINDOW_HOURS)

        results: list[AnomalyResult] = []
        for sig in signals:
            reasons: list[str] = []
            components: list[float] = []

            # --- 1. Velocity -------------------------------------------------
            vel_stmt = (
                select(func.count())
                .select_from(Signal)
                .where(
                    Signal.category == sig.category,
                    Signal.country_code == sig.country_code,
                    Signal.timestamp >= cutoff,
                )
            )
            vel_result = db.execute(vel_stmt)
            velocity_count: int = vel_result.scalar() or 0

            velocity_score = min(velocity_count / _VELOCITY_HIGH_THRESHOLD, 1.0)
            components.append(velocity_score)
            if velocity_count >= _VELOCITY_HIGH_THRESHOLD:
                reasons.append(
                    f"High velocity: {velocity_count} signals in {sig.category}/{sig.country_code} "
                    f"over the last {_VELOCITY_WINDOW_HOURS}h"
                )
            elif velocity_count >= _VELOCITY_HIGH_THRESHOLD // 2:
                reasons.append(
                    f"Moderate velocity: {velocity_count} signals in {sig.category}/{sig.country_code}"
                )

            # --- 2. Cross-source confirmation --------------------------------
            src_stmt = (
                select(func.count(func.distinct(Signal.source)))
                .select_from(Signal)
                .where(
                    Signal.category == sig.category,
                    Signal.country_code == sig.country_code,
                    Signal.timestamp >= cutoff,
                )
            )
            src_result = db.execute(src_stmt)
            source_count: int = src_result.scalar() or 0

            cross_source_score = min((source_count - 1) / 2.0, 1.0) if source_count > 1 else 0.0
            components.append(cross_source_score)
            if source_count > 1:
                reasons.append(
                    f"Cross-source confirmation: {source_count} distinct sources"
                )

            # --- 3. Recency --------------------------------------------------
            recency = _recency_weight(sig.timestamp)
            components.append(recency)
            if recency > 0.9:
                reasons.append("Very recent signal (high recency weight)")

            # --- Combined score (weighted average) ---------------------------
            # Velocity 40%, cross-source 30%, recency 30%
            anomaly = (
                0.40 * velocity_score
                + 0.30 * cross_source_score
                + 0.30 * recency
            )
            anomaly = round(min(max(anomaly, 0.0), 1.0), 4)

            if not reasons:
                reasons.append("Below anomaly thresholds")

            results.append(
                AnomalyResult(
                    signal_id=sig.id,
                    anomaly_score=anomaly,
                    reasons=reasons,
                )
            )

        logger.info("Scored %d signals for anomalies", len(results))
        return results
