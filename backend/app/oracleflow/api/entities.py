"""Entity query API endpoints."""

import logging

from flask import g, jsonify, request

logger = logging.getLogger(__name__)
from sqlalchemy import func, or_, select
from sqlalchemy.orm import joinedload

from . import entities_bp
from app.oracleflow.auth.middleware import require_auth
from app.oracleflow.database import get_session
from app.oracleflow.models.entity import Entity, EntityRelationship, EntitySource


def _get_db():
    return get_session()


@entities_bp.route('/', methods=['GET'])
@require_auth
def list_entities():
    """List entities with filtering and pagination (org-scoped)."""
    db = _get_db()
    try:
        entity_type = request.args.get('entity_type')
        country_code = request.args.get('country_code')
        limit = request.args.get('limit', 50, type=int)
        limit = min(limit, 200)
        offset = request.args.get('offset', 0, type=int)

        # Show global entities (org_id NULL) + org-specific entities
        org_filter = or_(Entity.organization_id == g.org_id, Entity.organization_id.is_(None))
        stmt = select(Entity).where(org_filter)
        count_stmt = select(func.count()).select_from(Entity).where(org_filter)

        if entity_type:
            stmt = stmt.where(Entity.entity_type == entity_type)
            count_stmt = count_stmt.where(Entity.entity_type == entity_type)
        if country_code:
            stmt = stmt.where(Entity.country_code == country_code)
            count_stmt = count_stmt.where(Entity.country_code == country_code)

        total = db.execute(count_stmt).scalar() or 0

        stmt = stmt.order_by(Entity.id.desc()).limit(limit).offset(offset)
        result = db.execute(stmt)
        entities = list(result.scalars().all())

        data = []
        for e in entities:
            data.append({
                "id": e.id,
                "name": e.name,
                "entity_type": e.entity_type,
                "country_code": e.country_code,
                "metadata": e.metadata_json,
                "created_at": e.created_at.isoformat() if e.created_at else None,
                "updated_at": e.updated_at.isoformat() if e.updated_at else None,
            })

        return jsonify({"success": True, "data": data, "total": total})
    except Exception as e:
        db.rollback()
        logger.exception("Entities API error: %s", e)
        return jsonify({"success": False, "error": "An internal error occurred"}), 500
    finally:
        db.close()


@entities_bp.route('/<int:entity_id>', methods=['GET'])
@require_auth
def get_entity(entity_id):
    """Get entity detail with sources and relationships (org-scoped)."""
    db = _get_db()
    try:
        stmt = (
            select(Entity)
            .options(
                joinedload(Entity.sources),
                joinedload(Entity.outgoing_relationships),
                joinedload(Entity.incoming_relationships),
            )
            .where(
                Entity.id == entity_id,
                or_(Entity.organization_id == g.org_id, Entity.organization_id.is_(None)),
            )
        )
        result = db.execute(stmt)
        entity = result.unique().scalar_one_or_none()

        if not entity:
            return jsonify({"success": False, "error": f"Entity {entity_id} not found"}), 404

        sources = []
        for src in entity.sources:
            sources.append({
                "id": src.id,
                "source_type": src.source_type,
                "source_url": src.source_url,
                "confidence_score": src.confidence_score,
                "discovered_at": src.discovered_at.isoformat() if src.discovered_at else None,
            })

        relationships = []
        for rel in entity.outgoing_relationships:
            relationships.append({
                "id": rel.id,
                "direction": "outgoing",
                "to_entity_id": rel.to_entity_id,
                "relationship_type": rel.relationship_type,
                "strength": rel.strength,
                "source_evidence": rel.source_evidence,
            })
        for rel in entity.incoming_relationships:
            relationships.append({
                "id": rel.id,
                "direction": "incoming",
                "from_entity_id": rel.from_entity_id,
                "relationship_type": rel.relationship_type,
                "strength": rel.strength,
                "source_evidence": rel.source_evidence,
            })

        data = {
            "id": entity.id,
            "name": entity.name,
            "entity_type": entity.entity_type,
            "country_code": entity.country_code,
            "metadata": entity.metadata_json,
            "created_at": entity.created_at.isoformat() if entity.created_at else None,
            "updated_at": entity.updated_at.isoformat() if entity.updated_at else None,
            "sources": sources,
            "relationships": relationships,
        }

        return jsonify({"success": True, "data": data})
    except Exception as e:
        db.rollback()
        logger.exception("Entities API error: %s", e)
        return jsonify({"success": False, "error": "An internal error occurred"}), 500
    finally:
        db.close()
