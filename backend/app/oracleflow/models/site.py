"""Site monitoring models: MonitoredSite, SitePage, PageSnapshot, PageDiff."""

from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey, Integer, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.oracleflow.constants import AntiBotLevel, DiffType, MonitoringFrequency, PageType

from .base import Base, TimestampMixin


class MonitoredSite(TimestampMixin, Base):
    """A website being monitored by OracleFlow."""

    __tablename__ = "monitored_sites"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    organization_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("organizations.id"), nullable=True, index=True
    )
    url: Mapped[str] = mapped_column(String(2048), nullable=False, unique=True)
    domain: Mapped[str] = mapped_column(String(512), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="active")
    discovered_pages_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )

    # Relationships
    pages: Mapped[list["SitePage"]] = relationship(
        "SitePage", back_populates="site", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<MonitoredSite(id={self.id}, domain={self.domain!r})>"


class SitePage(Base):
    """An individual page within a monitored site."""

    __tablename__ = "site_pages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    site_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("monitored_sites.id", ondelete="CASCADE"), nullable=False
    )
    url: Mapped[str] = mapped_column(String(2048), nullable=False, unique=True)
    path: Mapped[str] = mapped_column(String(2048), nullable=False)
    page_type: Mapped[str] = mapped_column(
        String(50), nullable=False, default=PageType.UNKNOWN.value
    )
    importance_score: Mapped[float] = mapped_column(
        Float, nullable=False, default=0.0
    )
    monitoring_frequency: Mapped[str] = mapped_column(
        String(50), nullable=False, default=MonitoringFrequency.STANDARD.value
    )
    anti_bot_level: Mapped[str] = mapped_column(
        String(50), nullable=False, default=AntiBotLevel.LOW.value
    )
    last_crawled: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    content_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    is_active: Mapped[bool] = mapped_column(nullable=False, default=True)

    # Relationships
    site: Mapped["MonitoredSite"] = relationship(
        "MonitoredSite", back_populates="pages"
    )
    snapshots: Mapped[list["PageSnapshot"]] = relationship(
        "PageSnapshot", back_populates="page", cascade="all, delete-orphan"
    )
    diffs: Mapped[list["PageDiff"]] = relationship(
        "PageDiff",
        back_populates="page",
        cascade="all, delete-orphan",
        foreign_keys="PageDiff.page_id",
    )

    def __repr__(self) -> str:
        return f"<SitePage(id={self.id}, url={self.url!r})>"


class PageSnapshot(Base):
    """A point-in-time capture of a page's content."""

    __tablename__ = "page_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    page_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("site_pages.id", ondelete="CASCADE"), nullable=False
    )
    content_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    content_html: Mapped[str | None] = mapped_column(Text, nullable=True)
    content_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    metadata_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    captured_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
    )

    # Relationships
    page: Mapped["SitePage"] = relationship("SitePage", back_populates="snapshots")

    def __repr__(self) -> str:
        return f"<PageSnapshot(id={self.id}, page_id={self.page_id})>"


class PageDiff(Base):
    """A detected difference between two snapshots of a page."""

    __tablename__ = "page_diffs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    page_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("site_pages.id", ondelete="CASCADE"), nullable=False
    )
    old_snapshot_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("page_snapshots.id", ondelete="SET NULL"), nullable=True
    )
    new_snapshot_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("page_snapshots.id", ondelete="SET NULL"), nullable=False
    )
    diff_type: Mapped[str] = mapped_column(
        String(50), nullable=False, default=DiffType.CONTENT_CHANGED.value
    )
    diff_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    diff_detail_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    detected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
    )

    # Relationships
    page: Mapped["SitePage"] = relationship(
        "SitePage", back_populates="diffs", foreign_keys=[page_id]
    )
    old_snapshot: Mapped["PageSnapshot | None"] = relationship(
        "PageSnapshot", foreign_keys=[old_snapshot_id]
    )
    new_snapshot: Mapped["PageSnapshot"] = relationship(
        "PageSnapshot", foreign_keys=[new_snapshot_id]
    )

    def __repr__(self) -> str:
        return f"<PageDiff(id={self.id}, diff_type={self.diff_type!r})>"
