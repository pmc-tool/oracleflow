"""Snapshot manager -- captures and retrieves page snapshots."""

from __future__ import annotations

import hashlib
import unicodedata
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.oracleflow.models.site import PageSnapshot


class SnapshotManager:
    """Create and query PageSnapshot records."""

    @staticmethod
    def _compute_hash(text: str) -> str:
        """Compute SHA-256 of normalised text content."""
        normalised = unicodedata.normalize("NFKC", text).strip()
        return hashlib.sha256(normalised.encode("utf-8")).hexdigest()

    def take_snapshot(
        self,
        db: Session,
        page_id: int,
        content_text: str,
        content_html: str,
        metadata: dict,
    ) -> PageSnapshot:
        """Create and persist a new PageSnapshot.

        :param db: Active database session.
        :param page_id: ID of the parent SitePage.
        :param content_text: Visible text of the page.
        :param content_html: Raw HTML of the page.
        :param metadata: Arbitrary metadata dict (stored as JSON).
        :returns: The newly created PageSnapshot instance.
        """
        content_hash = self._compute_hash(content_text)

        snapshot = PageSnapshot(
            page_id=page_id,
            content_text=content_text,
            content_html=content_html,
            content_hash=content_hash,
            metadata_json=metadata,
            captured_at=datetime.now(timezone.utc),
        )
        db.add(snapshot)
        db.flush()
        return snapshot

    def get_latest(
        self, db: Session, page_id: int
    ) -> PageSnapshot | None:
        """Return the most recent snapshot for a given page, or None."""
        stmt = (
            select(PageSnapshot)
            .where(PageSnapshot.page_id == page_id)
            .order_by(PageSnapshot.captured_at.desc())
            .limit(1)
        )
        result = db.execute(stmt)
        return result.scalar_one_or_none()
