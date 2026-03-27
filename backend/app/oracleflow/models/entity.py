"""Entity models: Entity, EntitySource, EntityRelationship."""

from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey, Integer, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.oracleflow.constants import EntityType

from .base import Base, TimestampMixin


class Entity(TimestampMixin, Base):
    """A real-world entity (person, org, government, etc.) tracked by OracleFlow."""

    __tablename__ = "entities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    organization_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("organizations.id"), nullable=True, index=True
    )
    name: Mapped[str] = mapped_column(String(512), nullable=False, index=True)
    entity_type: Mapped[str] = mapped_column(
        String(50), nullable=False, default=EntityType.ORGANIZATION.value
    )
    country_code: Mapped[str | None] = mapped_column(String(10), nullable=True)
    metadata_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # Relationships
    sources: Mapped[list["EntitySource"]] = relationship(
        "EntitySource", back_populates="entity", cascade="all, delete-orphan"
    )
    outgoing_relationships: Mapped[list["EntityRelationship"]] = relationship(
        "EntityRelationship",
        back_populates="from_entity",
        foreign_keys="EntityRelationship.from_entity_id",
        cascade="all, delete-orphan",
    )
    incoming_relationships: Mapped[list["EntityRelationship"]] = relationship(
        "EntityRelationship",
        back_populates="to_entity",
        foreign_keys="EntityRelationship.to_entity_id",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Entity(id={self.id}, name={self.name!r}, type={self.entity_type!r})>"


class EntitySource(Base):
    """A source from which an entity was discovered or verified."""

    __tablename__ = "entity_sources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    entity_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("entities.id", ondelete="CASCADE"), nullable=False
    )
    source_type: Mapped[str] = mapped_column(String(100), nullable=False)
    source_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    confidence_score: Mapped[float] = mapped_column(
        Float, nullable=False, default=0.0
    )
    discovered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
    )

    # Relationships
    entity: Mapped["Entity"] = relationship("Entity", back_populates="sources")

    def __repr__(self) -> str:
        return f"<EntitySource(id={self.id}, entity_id={self.entity_id}, type={self.source_type!r})>"


class EntityRelationship(Base):
    """A relationship between two entities."""

    __tablename__ = "entity_relationships"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    from_entity_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("entities.id", ondelete="CASCADE"), nullable=False
    )
    to_entity_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("entities.id", ondelete="CASCADE"), nullable=False
    )
    relationship_type: Mapped[str] = mapped_column(String(100), nullable=False)
    strength: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    source_evidence: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    from_entity: Mapped["Entity"] = relationship(
        "Entity",
        back_populates="outgoing_relationships",
        foreign_keys=[from_entity_id],
    )
    to_entity: Mapped["Entity"] = relationship(
        "Entity",
        back_populates="incoming_relationships",
        foreign_keys=[to_entity_id],
    )

    def __repr__(self) -> str:
        return (
            f"<EntityRelationship(id={self.id}, "
            f"from={self.from_entity_id}, to={self.to_entity_id}, "
            f"type={self.relationship_type!r})>"
        )
