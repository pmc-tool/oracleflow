"""NetworkExpander -- discover an entity's digital footprint via web search."""

from __future__ import annotations

import logging
import re

from scrapling import Fetcher

from app.oracleflow.exceptions import EntityError
from app.oracleflow.models.entity import Entity

from .schemas import ExpandedProfile

logger = logging.getLogger(__name__)

# Platforms to search for profiles
_PLATFORM_QUERIES: list[tuple[str, str]] = [
    ("twitter", "site:twitter.com"),
    ("facebook", "site:facebook.com"),
    ("linkedin", "site:linkedin.com"),
]

_URL_RE = re.compile(r"https?://[^\s\"'<>]+")


class NetworkExpander:
    """Search for an entity's profiles across social platforms."""

    def __init__(self) -> None:
        self._fetcher = Fetcher(auto_match=False)

    def expand(self, entity: Entity) -> list[ExpandedProfile]:
        """Search Google for *entity* profiles and return discovered URLs.

        This is best-effort: if scraping Google fails the method returns an
        empty list rather than raising.
        """
        profiles: list[ExpandedProfile] = []

        country = entity.country_code or ""
        name = entity.name

        for platform, site_filter in _PLATFORM_QUERIES:
            query = f"{name} {country} {site_filter}".strip()
            try:
                result = self._search_google(query, platform)
                if result:
                    profiles.append(
                        ExpandedProfile(
                            entity_id=entity.id,
                            platform=platform,
                            url=result["url"],
                            confidence=result["confidence"],
                        )
                    )
            except Exception:
                logger.debug(
                    "Google search failed for entity=%s platform=%s",
                    name,
                    platform,
                    exc_info=True,
                )
                continue

        return profiles

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _search_google(
        self, query: str, platform: str
    ) -> dict | None:
        """Fetch a Google search results page and pick the best profile URL."""
        search_url = f"https://www.google.com/search?q={query}"

        try:
            page = self._fetcher.get(search_url)
        except Exception as exc:
            logger.debug("Fetcher failed for %s: %s", search_url, exc)
            return None

        text = page.get_all_text() if page else ""
        if not text:
            return None

        # Look for URLs matching the target platform domain
        urls = _URL_RE.findall(text)
        platform_domain = f"{platform}.com"

        for url in urls:
            if platform_domain in url:
                # Simple confidence heuristic: if entity name appears near
                # the URL in the snippet text, higher confidence.
                confidence = self._compute_confidence(query, text, url)
                return {"url": url, "confidence": confidence}

        return None

    @staticmethod
    def _compute_confidence(query: str, snippet: str, url: str) -> float:
        """Heuristic confidence score based on name presence in the snippet."""
        # Extract the entity name (everything before "site:")
        name_part = query.split("site:")[0].strip().lower()
        snippet_lower = snippet.lower()

        score = 0.3  # base score for having a URL on the right domain

        if name_part in snippet_lower:
            score += 0.3
        if name_part.replace(" ", "") in url.lower():
            score += 0.2
        # Cap at 1.0
        return min(score, 1.0)
