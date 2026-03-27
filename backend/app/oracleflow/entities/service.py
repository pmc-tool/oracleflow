"""EntityService -- orchestrates extraction, expansion, and network building."""

from __future__ import annotations

import logging

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.oracleflow.exceptions import EntityError
from app.oracleflow.models.entity import Entity, EntitySource
from app.oracleflow.models.site import PageSnapshot, SitePage

from .expander import NetworkExpander
from .extractor import EntityExtractor
from .graph import EntityGraph
from .schemas import EntityNetwork

logger = logging.getLogger(__name__)


class EntityService:
    """High-level service for the Entity Network (Pyramid Effect) pipeline."""

    def __init__(
        self,
        extractor: EntityExtractor | None = None,
        expander: NetworkExpander | None = None,
        graph: EntityGraph | None = None,
    ) -> None:
        self._extractor = extractor or EntityExtractor()
        self._expander = expander or NetworkExpander()
        self._graph = graph or EntityGraph()

    # ------------------------------------------------------------------
    # process_site
    # ------------------------------------------------------------------

    def process_site(
        self, db: Session, site_id: int
    ) -> list[Entity]:
        """Extract entities from every page snapshot belonging to *site_id*.

        1. Query all :class:`PageSnapshot` records for the site.
        2. Run :class:`EntityExtractor` on each snapshot's text.
        3. Deduplicate by (name, country) and persist :class:`Entity` records.
        4. Create :class:`EntitySource` records pointing back to the page URL.
        5. Return the list of created (or existing) entities.
        """
        # Fetch snapshots via SitePage -> PageSnapshot join
        stmt = (
            select(PageSnapshot)
            .join(SitePage, SitePage.id == PageSnapshot.page_id)
            .where(SitePage.site_id == site_id)
            .options(selectinload(PageSnapshot.page))
        )
        result = db.execute(stmt)
        snapshots = list(result.scalars().all())

        if not snapshots:
            logger.info("No snapshots found for site %d", site_id)
            return []

        created_entities: list[Entity] = []
        # Track already-processed (name_lower, country) pairs to avoid duplicates
        seen: dict[tuple[str, str | None], Entity] = {}

        for snap in snapshots:
            text = snap.content_text or ""
            page_url = snap.page.url if snap.page else ""

            extracted = self._extractor.extract(text, url=page_url)

            for ext in extracted:
                key = (ext.name.lower(), None)  # country unknown at extraction time

                if key in seen:
                    entity = seen[key]
                else:
                    # Check if entity already exists in the database
                    existing_stmt = select(Entity).where(
                        Entity.name.ilike(ext.name),
                    )
                    existing_result = db.execute(existing_stmt)
                    entity = existing_result.scalar_one_or_none()

                    if entity is None:
                        entity = Entity(
                            name=ext.name,
                            entity_type=ext.entity_type.value,
                            metadata_json={
                                "role": ext.role,
                                "context": ext.context,
                            },
                        )
                        db.add(entity)
                        db.flush()
                        created_entities.append(entity)

                    seen[key] = entity

                # Create EntitySource for this page URL (avoid duplicates)
                if page_url:
                    source_exists_stmt = select(EntitySource).where(
                        EntitySource.entity_id == entity.id,
                        EntitySource.source_url == page_url,
                    )
                    source_exists_result = db.execute(source_exists_stmt)
                    if source_exists_result.scalar_one_or_none() is None:
                        source = EntitySource(
                            entity_id=entity.id,
                            source_type="web_page",
                            source_url=page_url,
                            confidence_score=0.8,
                        )
                        db.add(source)

        db.flush()
        logger.info(
            "Processed site %d: %d new entities created",
            site_id,
            len(created_entities),
        )
        return created_entities

    # ------------------------------------------------------------------
    # expand_entity
    # ------------------------------------------------------------------

    def expand_entity(
        self, db: Session, entity_id: int
    ) -> list[EntitySource]:
        """Discover social profiles for an entity and store them as sources."""
        entity = db.get(Entity, entity_id)
        if entity is None:
            raise EntityError(f"Entity {entity_id} not found")

        profiles = self._expander.expand(entity)

        sources: list[EntitySource] = []
        for profile in profiles:
            # Avoid duplicate source URLs
            dup_stmt = select(EntitySource).where(
                EntitySource.entity_id == entity_id,
                EntitySource.source_url == profile.url,
            )
            dup_result = db.execute(dup_stmt)
            if dup_result.scalar_one_or_none() is not None:
                continue

            source = EntitySource(
                entity_id=entity_id,
                source_type=profile.platform,
                source_url=profile.url,
                confidence_score=profile.confidence,
            )
            db.add(source)
            sources.append(source)

        db.flush()
        logger.info(
            "Expanded entity %d: %d new sources discovered",
            entity_id,
            len(sources),
        )
        return sources

    # ------------------------------------------------------------------
    # build_network
    # ------------------------------------------------------------------

    def build_network(
        self, db: Session, entity_id: int
    ) -> EntityNetwork:
        """Build relationships from signal co-occurrence and return the network."""
        self._graph.build_relationships(db, entity_id)
        return self._graph.get_network(db, entity_id)
