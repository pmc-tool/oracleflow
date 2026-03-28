"""Watchlist model: WatchlistItem for personalized monitoring."""

from datetime import datetime, timezone

from sqlalchemy import DateTime, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class WatchlistItem(Base):
    """A user's watchlist item — an organization, person, topic, etc. to monitor."""

    __tablename__ = "watchlist_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    organization_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    item_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # organization, person, topic, competitor, location
    country_code: Mapped[str | None] = mapped_column(String(10), nullable=True)
    keywords: Mapped[list | None] = mapped_column(JSON, default=list)
    google_news_rss: Mapped[str | None] = mapped_column(String(500), nullable=True)
    websites: Mapped[list | None] = mapped_column(JSON, default=list)
    social_links: Mapped[dict | None] = mapped_column(JSON, default=dict)
    is_active: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )

    def __repr__(self) -> str:
        return f"<WatchlistItem(id={self.id}, name={self.name!r}, type={self.item_type!r})>"
