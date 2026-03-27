"""Pydantic schemas for the diff engine."""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.oracleflow.constants import DiffType


class DiffResult(BaseModel):
    """Result of comparing two snapshots along a single dimension."""

    diff_type: DiffType
    summary: str
    detail: dict = Field(default_factory=dict)
    old_hash: str = ""
    new_hash: str = ""


class StructuralDiff(BaseModel):
    """Structural changes detected between two HTML documents."""

    nav_items_added: list[str] = Field(default_factory=list)
    nav_items_removed: list[str] = Field(default_factory=list)
    headings_changed: bool = False
    links_count_delta: int = 0


class MetaDiff(BaseModel):
    """Metadata changes detected between two snapshots."""

    title_changed: bool = False
    old_title: str = ""
    new_title: str = ""
    description_changed: bool = False
    old_description: str = ""
    new_description: str = ""
    og_tags_changed: dict = Field(default_factory=dict)


class MonitoringJob(BaseModel):
    """Describes a scheduled monitoring job for a single page."""

    page_id: int
    url: str
    frequency_seconds: int
