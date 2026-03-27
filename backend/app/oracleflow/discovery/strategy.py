"""Generate a monitoring strategy from page classifications."""

from __future__ import annotations

from app.oracleflow.constants import MonitoringFrequency, PAGE_TYPE_FREQUENCY
from app.oracleflow.discovery.schemas import PageClassification


class MonitoringStrategyGenerator:
    """Map classified pages to monitoring frequencies."""

    @staticmethod
    def generate(
        classifications: list[PageClassification],
    ) -> dict[str, MonitoringFrequency]:
        """Return a mapping of URL to recommended MonitoringFrequency.

        If the classifier already estimated a frequency, honour it;
        otherwise fall back to the default from PAGE_TYPE_FREQUENCY.
        """
        result: dict[str, MonitoringFrequency] = {}
        for cls in classifications:
            if cls.update_freq_estimate is not None:
                result[cls.url] = cls.update_freq_estimate
            else:
                result[cls.url] = PAGE_TYPE_FREQUENCY.get(
                    cls.page_type, MonitoringFrequency.LOW
                )
        return result
