"""Page classifier -- uses an LLM with heuristic fallback."""

from __future__ import annotations

import json
import logging
import re
from urllib.parse import urlparse

from app.oracleflow.constants import PageType
from app.oracleflow.exceptions import ClassificationError
from app.oracleflow.discovery.llm import LLMClient
from app.oracleflow.discovery.schemas import PageClassification

logger = logging.getLogger(__name__)

CLASSIFICATION_SYSTEM_PROMPT = """\
You are a web-page classifier. Given a page URL, title, and text excerpt, \
return a JSON object (no markdown fences) with exactly these keys:

- "page_type": one of {page_types}
- "language": ISO 639-1 code (e.g. "en", "fr", "ar")
- "org_type": short description of the organisation type (e.g. "government", "news_agency", "ngo", "political_party", "business")
- "people": list of person names mentioned prominently
- "topics": list of up to 5 topic keywords
- "update_freq_estimate": one of {frequencies} — how often you estimate this page is updated

Respond ONLY with the JSON object, nothing else.
"""


class PageClassifier:
    """Classify a page by type, language, people, and topics."""

    def __init__(self, llm_client: LLMClient | None = None) -> None:
        self._llm = llm_client or LLMClient()

    def classify_page(
        self, url: str, title: str, text: str
    ) -> PageClassification:
        """Classify a single page, falling back to heuristics on LLM failure."""
        try:
            return self._classify_via_llm(url, title, text)
        except (ClassificationError, Exception) as exc:
            logger.warning("LLM classification failed for %s: %s -- using heuristics", url, exc)
            return self._classify_heuristic(url, title, text)

    # ------------------------------------------------------------------
    # LLM path
    # ------------------------------------------------------------------

    def _classify_via_llm(
        self, url: str, title: str, text: str
    ) -> PageClassification:
        page_types = ", ".join(pt.value for pt in PageType)
        frequencies = "5m, 15m, 30m, 2h, 6h, 7d, disabled"

        system_prompt = CLASSIFICATION_SYSTEM_PROMPT.format(
            page_types=page_types,
            frequencies=frequencies,
        )

        # Truncate text to keep token usage reasonable
        content = f"URL: {url}\nTitle: {title}\n\nText (truncated):\n{text[:3000]}"

        raw = self._llm.classify(system_prompt, content)
        return self._parse_llm_response(url, raw)

    @staticmethod
    def _parse_llm_response(url: str, raw: str) -> PageClassification:
        """Parse the JSON response from the LLM into a PageClassification."""
        # Strip markdown code fences if the model wraps them anyway
        cleaned = raw.strip()
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
            cleaned = re.sub(r"\s*```$", "", cleaned)

        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError as exc:
            raise ClassificationError(f"LLM returned invalid JSON: {exc}") from exc

        # Map page_type string to enum
        raw_type = data.get("page_type", "unknown")
        try:
            page_type = PageType(raw_type)
        except ValueError:
            page_type = PageType.UNKNOWN

        # Map frequency string
        from app.oracleflow.constants import MonitoringFrequency
        raw_freq = data.get("update_freq_estimate")
        freq = None
        if raw_freq:
            try:
                freq = MonitoringFrequency(raw_freq)
            except ValueError:
                freq = None

        return PageClassification(
            url=url,
            page_type=page_type,
            language=data.get("language", "en"),
            org_type=data.get("org_type", ""),
            people=data.get("people", []),
            topics=data.get("topics", []),
            update_freq_estimate=freq,
        )

    # ------------------------------------------------------------------
    # Heuristic fallback
    # ------------------------------------------------------------------

    @staticmethod
    def _classify_heuristic(url: str, title: str, text: str) -> PageClassification:
        """Rule-based classification when the LLM is unavailable."""
        parsed = urlparse(url)
        path = parsed.path.lower().rstrip("/")
        title_lower = title.lower()

        page_type = PageType.UNKNOWN

        if path in ("", "/"):
            page_type = PageType.HOMEPAGE
        elif any(kw in path for kw in ("/news", "/press", "/media", "/blog")):
            page_type = PageType.NEWS_INDEX
        elif any(kw in path for kw in ("/article", "/post", "/story")):
            page_type = PageType.ARTICLE
        elif any(kw in path for kw in ("/policy", "/policies", "/regulation", "/law")):
            page_type = PageType.POLICY_PAGE
        elif any(kw in path for kw in ("/team", "/staff", "/people", "/about-us", "/leadership")):
            page_type = PageType.TEAM_PAGE
        elif any(kw in path for kw in ("/event", "/calendar", "/conference")):
            page_type = PageType.EVENTS
        elif any(kw in path for kw in ("/donat", "/fundrais", "/support-us", "/give")):
            page_type = PageType.FUNDRAISING
        elif any(kw in path for kw in ("/contact", "/faq", "/terms", "/privacy", "/sitemap")):
            page_type = PageType.STATIC
        elif any(kw in path for kw in ("/login", "/signup", "/register", "/cart", "/checkout")):
            page_type = PageType.IGNORE

        # Title-based overrides
        if page_type == PageType.UNKNOWN:
            if any(kw in title_lower for kw in ("news", "press release", "media")):
                page_type = PageType.NEWS_INDEX
            elif any(kw in title_lower for kw in ("team", "staff", "leadership")):
                page_type = PageType.TEAM_PAGE
            elif any(kw in title_lower for kw in ("event", "conference")):
                page_type = PageType.EVENTS

        return PageClassification(
            url=url,
            page_type=page_type,
            language="en",
            org_type="",
            people=[],
            topics=[],
            update_freq_estimate=None,
        )
