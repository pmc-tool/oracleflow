"""Pydantic schemas for the signal processing pipeline."""

from datetime import datetime

from pydantic import BaseModel, Field


class SignalCluster(BaseModel):
    """A group of related signals sharing country and category."""

    signals: list[int] = Field(description="Signal IDs in this cluster")
    topic: str = Field(description="Shared topic / category label")
    country_code: str = Field(default="", description="ISO country code")
    avg_sentiment: float = Field(default=0.0, description="Mean sentiment across signals")
    combined_importance: float = Field(
        default=0.0, description="Sum of importance scores in this cluster"
    )


class AnomalyResult(BaseModel):
    """Anomaly score and explanation for a single signal."""

    signal_id: int
    anomaly_score: float = Field(ge=0.0, le=1.0, description="Anomaly score 0-1")
    reasons: list[str] = Field(default_factory=list)


class ChaosIndexSnapshot(BaseModel):
    """Point-in-time global chaos index reading."""

    global_score: float = Field(ge=0.0, le=100.0)
    categories: dict[str, float] = Field(
        default_factory=dict,
        description="Per-category scores (0-100)",
    )
    timestamp: datetime
    contributing_signals: int = Field(default=0)


class CountryRiskSnapshot(BaseModel):
    """Point-in-time risk snapshot for a single country."""

    country_code: str
    risk_score: float = Field(ge=0.0, le=100.0)
    categories: dict[str, float] = Field(
        default_factory=dict,
        description="Per-category scores (0-100)",
    )
    signal_count: int = Field(default=0)
