"""Pydantic models for the entity extraction and network pipeline."""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.oracleflow.constants import EntityType


class ExtractedEntity(BaseModel):
    """An entity extracted from text by the LLM or regex fallback."""

    name: str
    entity_type: EntityType
    role: str = ""
    context: str = ""


class ExpandedProfile(BaseModel):
    """A social / web profile discovered for an entity."""

    entity_id: int
    platform: str
    url: str
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)


class EntityNetworkNode(BaseModel):
    """A single node inside an entity relationship network."""

    entity_id: int
    name: str
    entity_type: str
    relationship_type: str
    strength: float = Field(default=0.0, ge=0.0, le=1.0)


class EntityNetwork(BaseModel):
    """Tree-shaped view of an entity and its connections up to *depth* levels."""

    entity_id: int
    name: str
    entity_type: str
    depth: int
    connections: list[EntityNetworkNode] = Field(default_factory=list)
