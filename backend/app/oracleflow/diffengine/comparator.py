"""PageComparator -- orchestrates the three diff functions over snapshots."""

from __future__ import annotations

from app.oracleflow.constants import DiffType
from app.oracleflow.models.site import PageSnapshot

from .differ import metadata_diff, structural_diff, text_diff
from .schemas import DiffResult


class PageComparator:
    """Run all diff functions against two PageSnapshot objects."""

    def compare(
        self, old_snapshot: PageSnapshot, new_snapshot: PageSnapshot
    ) -> list[DiffResult]:
        """Compare *old_snapshot* with *new_snapshot* and return detected diffs.

        Each diff function maps to a specific :class:`DiffType`:

        * text changes   -> ``CONTENT_CHANGED``
        * structural     -> ``STRUCTURAL_CHANGE``
        * metadata       -> ``METADATA_CHANGE``
        """
        results: list[DiffResult] = []

        # --- Text diff ---
        old_text = old_snapshot.content_text or ""
        new_text = new_snapshot.content_text or ""
        td = text_diff(old_text, new_text)
        if td is not None:
            td.diff_type = DiffType.CONTENT_CHANGED
            td.old_hash = old_snapshot.content_hash
            td.new_hash = new_snapshot.content_hash
            results.append(td)

        # --- Structural diff ---
        old_html = old_snapshot.content_html or ""
        new_html = new_snapshot.content_html or ""
        sd = structural_diff(old_html, new_html)
        if sd is not None:
            results.append(
                DiffResult(
                    diff_type=DiffType.STRUCTURAL_CHANGE,
                    summary=_structural_summary(sd),
                    detail=sd.model_dump(),
                    old_hash=old_snapshot.content_hash,
                    new_hash=new_snapshot.content_hash,
                )
            )

        # --- Metadata diff ---
        old_meta = old_snapshot.metadata_json or {}
        new_meta = new_snapshot.metadata_json or {}
        md = metadata_diff(old_meta, new_meta)
        if md is not None:
            results.append(
                DiffResult(
                    diff_type=DiffType.METADATA_CHANGE,
                    summary=_meta_summary(md),
                    detail=md.model_dump(),
                    old_hash=old_snapshot.content_hash,
                    new_hash=new_snapshot.content_hash,
                )
            )

        return results


def _structural_summary(sd) -> str:
    parts: list[str] = []
    if sd.nav_items_added:
        parts.append(f"{len(sd.nav_items_added)} nav items added")
    if sd.nav_items_removed:
        parts.append(f"{len(sd.nav_items_removed)} nav items removed")
    if sd.headings_changed:
        parts.append("heading structure changed")
    if sd.links_count_delta:
        parts.append(f"link count delta {sd.links_count_delta:+d}")
    return "; ".join(parts) or "structural change detected"


def _meta_summary(md) -> str:
    parts: list[str] = []
    if md.title_changed:
        parts.append(f"title: '{md.old_title}' -> '{md.new_title}'")
    if md.description_changed:
        parts.append("description changed")
    if md.og_tags_changed:
        parts.append(f"{len(md.og_tags_changed)} og tag(s) changed")
    return "; ".join(parts) or "metadata change detected"
