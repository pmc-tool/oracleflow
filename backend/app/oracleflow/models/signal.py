"""Signal models: Signal, Simulation, Alert, ChaosIndex."""

from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey, Integer, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.oracleflow.constants import (
    AlertSeverity,
    SignalCategory,
    SignalSource,
    SimulationStatus,
)

from .base import Base


class Signal(Base):
    """A detected signal from any source (web monitoring, world feeds, etc.)."""

    __tablename__ = "signals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    organization_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("organizations.id"), nullable=True, index=True
    )
    source: Mapped[str] = mapped_column(
        String(50), nullable=False, default=SignalSource.SCRAPLING.value
    )
    signal_type: Mapped[str] = mapped_column(String(100), nullable=False)
    category: Mapped[str] = mapped_column(
        String(50), nullable=False, default=SignalCategory.OTHER.value
    )
    country_code: Mapped[str | None] = mapped_column(String(10), nullable=True)
    title: Mapped[str] = mapped_column(String(1024), nullable=False)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    raw_data_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    sentiment_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    anomaly_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    importance: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        index=True,
    )

    # Relationships
    alerts: Mapped[list["Alert"]] = relationship(
        "Alert", back_populates="signal", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Signal(id={self.id}, title={self.title!r}, source={self.source!r})>"


class Simulation(Base):
    """A Mirofish simulation triggered by one or more signals."""

    __tablename__ = "simulations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    organization_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("organizations.id"), nullable=True, index=True
    )
    signal_ids_json: Mapped[list | None] = mapped_column(JSON, nullable=True)
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default=SimulationStatus.PENDING.value
    )
    mirofish_project_id: Mapped[str | None] = mapped_column(
        String(256), nullable=True
    )
    mirofish_simulation_id: Mapped[str | None] = mapped_column(
        String(256), nullable=True
    )
    scenario_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    report_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    alerts: Mapped[list["Alert"]] = relationship(
        "Alert", back_populates="simulation", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Simulation(id={self.id}, status={self.status!r})>"


class Alert(Base):
    """An alert generated from a signal or simulation result."""

    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    signal_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("signals.id", ondelete="SET NULL"), nullable=True
    )
    simulation_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("simulations.id", ondelete="SET NULL"), nullable=True
    )
    alert_type: Mapped[str] = mapped_column(String(100), nullable=False)
    severity: Mapped[str] = mapped_column(
        String(50), nullable=False, default=AlertSeverity.MEDIUM.value
    )
    message: Mapped[str] = mapped_column(Text, nullable=False)
    delivered_to_json: Mapped[list | None] = mapped_column(JSON, nullable=True)
    delivered_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    signal: Mapped["Signal | None"] = relationship(
        "Signal", back_populates="alerts"
    )
    simulation: Mapped["Simulation | None"] = relationship(
        "Simulation", back_populates="alerts"
    )

    def __repr__(self) -> str:
        return f"<Alert(id={self.id}, type={self.alert_type!r}, severity={self.severity!r})>"


class AlertRuleDB(Base):
    """A persisted alert rule that maps signal conditions to alert actions."""

    __tablename__ = "alert_rules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int | None] = mapped_column(
        Integer, nullable=True, index=True
    )
    organization_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("organizations.id"), nullable=True, index=True
    )
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    condition_type: Mapped[str] = mapped_column(
        String(50), nullable=False, default="anomaly_threshold"
    )
    threshold: Mapped[float] = mapped_column(Float, nullable=False, default=0.7)
    categories_json: Mapped[list | None] = mapped_column(JSON, nullable=True)
    country_codes_json: Mapped[list | None] = mapped_column(JSON, nullable=True)
    page_types_json: Mapped[list | None] = mapped_column(JSON, nullable=True)
    keywords_json: Mapped[list | None] = mapped_column(JSON, nullable=True)
    severity: Mapped[str] = mapped_column(
        String(50), nullable=False, default=AlertSeverity.MEDIUM.value
    )
    channels_json: Mapped[list | None] = mapped_column(JSON, nullable=True)
    webhook_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    enabled: Mapped[bool] = mapped_column(nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
    )

    def to_pydantic(self):
        """Convert to the Pydantic AlertRule used by RuleEvaluator."""
        from app.oracleflow.alerts.rules import AlertRule
        return AlertRule(
            name=self.name,
            condition_type=self.condition_type,
            threshold=self.threshold,
            categories=self.categories_json or [],
            country_codes=self.country_codes_json or [],
            page_types=self.page_types_json or [],
            keywords=self.keywords_json or [],
            severity=self.severity,
            channels=self.channels_json or [],
            webhook_url=self.webhook_url or "",
            enabled=self.enabled,
        )

    def __repr__(self) -> str:
        return f"<AlertRuleDB(id={self.id}, name={self.name!r}, enabled={self.enabled})>"


class Notification(Base):
    """A notification delivered to a user when a signal/alert is triggered."""

    __tablename__ = "notifications"

    id = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id = mapped_column(Integer, nullable=False, index=True)
    organization_id = mapped_column(Integer, nullable=True)
    signal_id = mapped_column(Integer, ForeignKey("signals.id"), nullable=True)
    title = mapped_column(String(512), nullable=False)
    message = mapped_column(Text, nullable=True)
    severity = mapped_column(String(20), default="info")  # critical, high, medium, low, info
    is_read = mapped_column(Integer, default=0)  # 0=unread, 1=read (Integer for SQLite compat)
    created_at = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )

    def __repr__(self) -> str:
        return f"<Notification(id={self.id}, user={self.user_id}, read={self.is_read})>"


class ChaosIndex(Base):
    """A periodic snapshot of the global chaos index score."""

    __tablename__ = "chaos_index"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        index=True,
    )
    global_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    category_scores_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    contributing_signal_ids_json: Mapped[list | None] = mapped_column(
        JSON, nullable=True
    )

    def __repr__(self) -> str:
        return f"<ChaosIndex(id={self.id}, score={self.global_score}, ts={self.timestamp})>"
