"""EntityGraph -- build and query co-occurrence relationship networks."""

from __future__ import annotations

import logging
from collections import Counter

from sqlalchemy import select, or_
from sqlalchemy.orm import Session

from app.oracleflow.models.entity import Entity, EntityRelationship
from app.oracleflow.models.signal import Signal

from .schemas import EntityNetwork, EntityNetworkNode

logger = logging.getLogger(__name__)


class EntityGraph:
    """Discover and traverse entity relationships via signal co-occurrence."""

    def build_relationships(
        self, db: Session, entity_id: int
    ) -> None:
        """Find other entities co-mentioned in the same signals and persist
        :class:`EntityRelationship` records.

        Strength is derived from the number of co-occurring signals normalised
        to [0, 1].
        """
        # Load the target entity
        entity = db.get(Entity, entity_id)
        if entity is None:
            logger.warning("Entity %d not found -- skipping relationship build", entity_id)
            return

        # Fetch all signals whose title or summary mention this entity's name
        name = entity.name
        stmt = select(Signal).where(
            or_(
                Signal.title.ilike(f"%{name}%"),
                Signal.summary.ilike(f"%{name}%"),
            )
        )
        result = db.execute(stmt)
        signals = list(result.scalars().all())

        if not signals:
            logger.info("No signals mention entity %d (%s)", entity_id, name)
            return

        # For each signal, find other entities mentioned in the same text
        all_entities_stmt = select(Entity).where(Entity.id != entity_id)
        all_entities_result = db.execute(all_entities_stmt)
        other_entities = list(all_entities_result.scalars().all())

        co_occurrence: Counter[int] = Counter()

        for signal in signals:
            text = f"{signal.title or ''} {signal.summary or ''}".lower()
            for other in other_entities:
                if other.name.lower() in text:
                    co_occurrence[other.id] += 1

        if not co_occurrence:
            logger.info("No co-occurring entities for entity %d", entity_id)
            return

        max_count = max(co_occurrence.values())

        for other_id, count in co_occurrence.items():
            strength = count / max_count if max_count > 0 else 0.0

            # Upsert: check if relationship already exists
            existing_stmt = select(EntityRelationship).where(
                EntityRelationship.from_entity_id == entity_id,
                EntityRelationship.to_entity_id == other_id,
            )
            existing_result = db.execute(existing_stmt)
            existing = existing_result.scalar_one_or_none()

            if existing:
                existing.strength = strength
                existing.source_evidence = f"co-occurrence in {count} signal(s)"
            else:
                rel = EntityRelationship(
                    from_entity_id=entity_id,
                    to_entity_id=other_id,
                    relationship_type="co_occurrence",
                    strength=strength,
                    source_evidence=f"co-occurrence in {count} signal(s)",
                )
                db.add(rel)

        db.flush()
        logger.info(
            "Built %d relationships for entity %d",
            len(co_occurrence),
            entity_id,
        )

    def get_network(
        self, db: Session, entity_id: int, depth: int = 2
    ) -> EntityNetwork:
        """Traverse relationships up to *depth* levels and return a tree."""
        entity = db.get(Entity, entity_id)
        if entity is None:
            return EntityNetwork(
                entity_id=entity_id,
                name="(unknown)",
                entity_type="",
                depth=depth,
                connections=[],
            )

        connections = self._collect_connections(db, entity_id, depth, set())

        return EntityNetwork(
            entity_id=entity.id,
            name=entity.name,
            entity_type=entity.entity_type,
            depth=depth,
            connections=connections,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _collect_connections(
        self,
        db: Session,
        entity_id: int,
        remaining_depth: int,
        visited: set[int],
    ) -> list[EntityNetworkNode]:
        """Recursively gather connected entity nodes."""
        if remaining_depth <= 0:
            return []

        visited.add(entity_id)

        stmt = select(EntityRelationship).where(
            or_(
                EntityRelationship.from_entity_id == entity_id,
                EntityRelationship.to_entity_id == entity_id,
            )
        )
        result = db.execute(stmt)
        relationships = list(result.scalars().all())

        nodes: list[EntityNetworkNode] = []

        for rel in relationships:
            # Determine the "other" entity
            other_id = (
                rel.to_entity_id
                if rel.from_entity_id == entity_id
                else rel.from_entity_id
            )
            if other_id in visited:
                continue

            other = db.get(Entity, other_id)
            if other is None:
                continue

            nodes.append(
                EntityNetworkNode(
                    entity_id=other.id,
                    name=other.name,
                    entity_type=other.entity_type,
                    relationship_type=rel.relationship_type,
                    strength=rel.strength,
                )
            )

            # Recurse deeper (children are flattened into the same list)
            if remaining_depth > 1:
                children = self._collect_connections(
                    db, other_id, remaining_depth - 1, visited
                )
                nodes.extend(children)

        return nodes
