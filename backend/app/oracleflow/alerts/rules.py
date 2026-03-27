"""Alert rule definitions and evaluation logic."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from pydantic import BaseModel, Field

from app.oracleflow.constants import AlertChannel, AlertSeverity, SignalSource

if TYPE_CHECKING:
    from app.oracleflow.models.signal import Signal

logger = logging.getLogger(__name__)


class AlertRule(BaseModel):
    """Declarative rule that maps signal conditions to alert actions."""

    name: str
    condition_type: str = Field(
        ...,
        description="One of: anomaly_threshold, diff_detected, chaos_spike",
    )
    threshold: float = 0.0
    country_codes: list[str] = Field(default_factory=list)
    categories: list[str] = Field(default_factory=list)
    page_types: list[str] = Field(default_factory=list)
    severity: AlertSeverity = AlertSeverity.MEDIUM
    channels: list[AlertChannel] = Field(default_factory=list)
    webhook_url: str = ""
    enabled: bool = True


class RuleEvaluator:
    """Evaluates a signal against a list of alert rules and returns matches."""

    @staticmethod
    def evaluate(signal: Signal, rules: list[AlertRule]) -> list[AlertRule]:
        """Return every enabled rule whose condition matches *signal*.

        Parameters
        ----------
        signal:
            The Signal ORM instance to test.
        rules:
            Candidate rules to evaluate.

        Returns
        -------
        list[AlertRule]
            Rules that matched the signal.
        """
        matched: list[AlertRule] = []
        for rule in rules:
            if not rule.enabled:
                continue

            # Optional country filter
            if rule.country_codes and getattr(signal, "country_code", None):
                if signal.country_code not in rule.country_codes:
                    continue

            # Optional category filter
            if rule.categories and getattr(signal, "category", None):
                if signal.category not in rule.categories:
                    continue

            if rule.condition_type == "anomaly_threshold":
                if signal.anomaly_score >= rule.threshold:
                    matched.append(rule)

            elif rule.condition_type == "diff_detected":
                if signal.source == SignalSource.SCRAPLING.value:
                    # If page_types specified, check raw_data for page_type
                    if rule.page_types:
                        raw = signal.raw_data_json or {}
                        page_type = raw.get("page_type", "")
                        if page_type in rule.page_types:
                            matched.append(rule)
                    else:
                        matched.append(rule)

            elif rule.condition_type == "chaos_spike":
                # Chaos spike rules check anomaly_score as a proxy for
                # chaos-index delta when evaluated against a signal.
                if signal.anomaly_score >= rule.threshold:
                    matched.append(rule)

            else:
                logger.warning("Unknown condition_type %r in rule %r", rule.condition_type, rule.name)

        return matched
