"""Pydantic models for the discovery engine request/response cycle."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field, HttpUrl

from app.oracleflow.constants import MonitoringFrequency, PageType


class DiscoveryRequest(BaseModel):
    """Input parameters for a site discovery run."""

    url: HttpUrl
    max_depth: int = Field(default=3, ge=1, le=10)
    max_pages: int = Field(default=100, ge=1, le=10_000)


class PageClassification(BaseModel):
    """Classification result for a single discovered page."""

    url: str
    page_type: PageType = PageType.UNKNOWN
    language: str = "en"
    org_type: str = ""
    people: list[str] = Field(default_factory=list)
    topics: list[str] = Field(default_factory=list)
    update_freq_estimate: Optional[MonitoringFrequency] = None


class DiscoveryResult(BaseModel):
    """Output of a complete discovery run."""

    site_id: int
    pages_found: int
    classifications: list[PageClassification] = Field(default_factory=list)
