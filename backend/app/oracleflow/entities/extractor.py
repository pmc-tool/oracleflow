"""EntityExtractor -- discover people and organisations in free text."""

from __future__ import annotations

import json
import logging
import re

from app.oracleflow.constants import EntityType
from app.oracleflow.discovery.llm import LLMClient
from app.oracleflow.exceptions import EntityError

from .schemas import ExtractedEntity

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = (
    "Extract all people and organizations mentioned in this text. "
    "For each, provide: name, type (person/organization/political_party/"
    "media/government), role if mentioned, and a brief context sentence.\n\n"
    "Return ONLY a JSON array. Each element must have the keys: "
    '"name", "type", "role", "context".\n'
    "Example:\n"
    '[{"name": "John Doe", "type": "person", "role": "CEO", '
    '"context": "John Doe announced a new policy."}]\n'
    "If no entities are found, return an empty array: []"
)

# Maps LLM type strings to EntityType enum values
_TYPE_MAP: dict[str, EntityType] = {
    "person": EntityType.PERSON,
    "organization": EntityType.ORGANIZATION,
    "organisation": EntityType.ORGANIZATION,
    "political_party": EntityType.POLITICAL_PARTY,
    "media": EntityType.MEDIA,
    "government": EntityType.GOVERNMENT,
    "ngo": EntityType.NGO,
    "business": EntityType.BUSINESS,
}

# Regex fallback: sequences of 2+ capitalised words (simple NER heuristic)
_CAPITALIZED_NAME_RE = re.compile(r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\b")


class EntityExtractor:
    """Extract named entities from text using an LLM with regex fallback."""

    def __init__(self, llm: LLMClient | None = None) -> None:
        self._llm = llm or LLMClient()

    def extract(self, text: str, url: str = "") -> list[ExtractedEntity]:
        """Return deduplicated entities found in *text*.

        Tries the LLM first; falls back to regex-based extraction on failure.
        """
        if not text or not text.strip():
            return []

        # Truncate very long text to keep token usage reasonable
        truncated = text[:8000]

        try:
            entities = self._extract_via_llm(truncated)
        except Exception:
            logger.warning(
                "LLM extraction failed for url=%s -- falling back to regex", url
            )
            entities = self._extract_via_regex(truncated)

        return self._deduplicate(entities)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _extract_via_llm(self, text: str) -> list[ExtractedEntity]:
        raw = self._llm.classify(_SYSTEM_PROMPT, text)

        # The LLM sometimes wraps JSON in markdown fences; strip them.
        raw = raw.strip()
        if raw.startswith("```"):
            raw = re.sub(r"^```(?:json)?\s*", "", raw)
            raw = re.sub(r"\s*```$", "", raw)

        try:
            items = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise EntityError(f"Failed to parse LLM JSON: {exc}") from exc

        if not isinstance(items, list):
            raise EntityError("LLM response is not a JSON array")

        results: list[ExtractedEntity] = []
        for item in items:
            if not isinstance(item, dict) or "name" not in item:
                continue
            entity_type = _TYPE_MAP.get(
                item.get("type", "").lower(), EntityType.ORGANIZATION
            )
            results.append(
                ExtractedEntity(
                    name=item["name"].strip(),
                    entity_type=entity_type,
                    role=item.get("role", "").strip(),
                    context=item.get("context", "").strip(),
                )
            )
        return results

    @staticmethod
    def _extract_via_regex(text: str) -> list[ExtractedEntity]:
        """Fallback: find capitalised multi-word names."""
        matches = _CAPITALIZED_NAME_RE.findall(text)
        results: list[ExtractedEntity] = []
        for name in matches:
            name = name.strip()
            if len(name) < 4:
                continue
            results.append(
                ExtractedEntity(
                    name=name,
                    entity_type=EntityType.ORGANIZATION,
                    role="",
                    context="",
                )
            )
        return results

    @staticmethod
    def _deduplicate(entities: list[ExtractedEntity]) -> list[ExtractedEntity]:
        """Keep the first occurrence of each name (case-insensitive)."""
        seen: set[str] = set()
        unique: list[ExtractedEntity] = []
        for ent in entities:
            key = ent.name.lower()
            if key not in seen:
                seen.add(key)
                unique.append(ent)
        return unique
