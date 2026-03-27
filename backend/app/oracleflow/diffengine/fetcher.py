"""MonitorFetcher -- sync wrapper around Scrapling fetchers."""

from __future__ import annotations

import logging
import re
import sys
from typing import Any

import requests

from app.oracleflow.constants import AntiBotLevel
from app.oracleflow.exceptions import ScrapingError

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Attempt to make Scrapling importable from the parent project directory.
# ---------------------------------------------------------------------------
_SCRAPLING_ROOT = "/Users/nowshidalamsayem/Downloads/Scrapling-main"
if _SCRAPLING_ROOT not in sys.path:
    sys.path.insert(0, _SCRAPLING_ROOT)

_scrapling_available = False
try:
    from scrapling.fetchers import Fetcher, StealthyFetcher  # noqa: F401
    _scrapling_available = True
    logger.info("Scrapling fetchers loaded successfully")
except Exception as exc:
    logger.warning("Scrapling not importable (%s), will use requests fallback", exc)


_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)


def _extract_text_from_html(html: str) -> str:
    """Strip HTML tags, scripts, styles, and noise to produce clean readable text."""
    # Remove script tags and their content (handle multiline, nested, with attributes)
    text = re.sub(r"<script[\s\S]*?</script>", " ", html, flags=re.IGNORECASE)
    # Remove noscript
    text = re.sub(r"<noscript[\s\S]*?</noscript>", " ", text, flags=re.IGNORECASE)
    # Remove style tags and content
    text = re.sub(r"<style[\s\S]*?</style>", " ", text, flags=re.IGNORECASE)
    # Remove HTML comments
    text = re.sub(r"<!--[\s\S]*?-->", " ", text)
    # Remove SVG blocks
    text = re.sub(r"<svg[\s\S]*?</svg>", " ", text, flags=re.IGNORECASE)
    # Remove all remaining HTML tags
    text = re.sub(r"<[^>]+>", " ", text)
    # Decode common HTML entities
    text = text.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
    text = text.replace("&nbsp;", " ").replace("&quot;", '"').replace("&#x27;", "'")
    text = re.sub(r"&#\d+;", " ", text)
    text = re.sub(r"&\w+;", " ", text)
    # Remove any remaining JS-like fragments (function calls, var declarations, JSON blobs)
    text = re.sub(r"\bfunction\s*\([^)]*\)\s*\{[^}]*\}", " ", text)
    text = re.sub(r"\bvar\s+\w+\s*=", " ", text)
    text = re.sub(r"\{[^{}]*:[^{}]*\}", " ", text)
    # Normalize whitespace
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _extract_metadata_from_html(html: str) -> dict[str, Any]:
    """Extract title, meta description and og tags from raw HTML."""
    metadata: dict[str, Any] = {}
    title_m = re.search(r"<title[^>]*>(.*?)</title>", html, re.IGNORECASE | re.DOTALL)
    if title_m:
        metadata["title"] = title_m.group(1).strip()

    for m in re.finditer(
        r'<meta\s[^>]*(?:name|property)\s*=\s*["\']([^"\']+)["\'][^>]*'
        r'content\s*=\s*["\']([^"\']*)["\']',
        html,
        re.IGNORECASE,
    ):
        metadata[m.group(1)] = m.group(2)
    # Also handle reversed attribute order (content before name)
    for m in re.finditer(
        r'<meta\s[^>]*content\s*=\s*["\']([^"\']*)["\'][^>]*'
        r'(?:name|property)\s*=\s*["\']([^"\']+)["\']',
        html,
        re.IGNORECASE,
    ):
        metadata[m.group(2)] = m.group(1)

    return metadata


class MonitorFetcher:
    """Fetch a page synchronously using the appropriate Scrapling fetcher.

    For ``AntiBotLevel.LOW`` / ``AntiBotLevel.MEDIUM`` the lightweight
    :class:`Fetcher` is used.  For ``AntiBotLevel.HIGH`` the browser-based
    :class:`StealthyFetcher` is selected instead.

    Falls back to ``requests`` with a realistic User-Agent when Scrapling is
    unavailable.
    """

    @staticmethod
    def _fetch_with_scrapling(url: str, anti_bot_level: str) -> tuple[str, str, dict[str, Any]]:
        """Fetch using Scrapling and return (text, html, metadata)."""
        from scrapling.fetchers import Fetcher, StealthyFetcher  # noqa: F811

        level = anti_bot_level.lower()

        if level == AntiBotLevel.HIGH.value:
            response = StealthyFetcher().fetch(url)
        else:
            response = Fetcher().fetch(url)

        html = response.html_content if hasattr(response, "html_content") else str(response)
        text = response.get_all_text() if hasattr(response, "get_all_text") else _extract_text_from_html(html)

        metadata: dict[str, Any] = {}
        if hasattr(response, "title"):
            metadata["title"] = response.title or ""
        if hasattr(response, "css"):
            try:
                for meta_tag in response.css("meta"):
                    name = (
                        meta_tag.attrib.get("name", "")
                        or meta_tag.attrib.get("property", "")
                    )
                    content = meta_tag.attrib.get("content", "")
                    if name and content:
                        metadata[name] = content
            except Exception:
                pass

        # Fill any missing metadata from raw HTML
        if not metadata:
            metadata = _extract_metadata_from_html(html)

        return text, html, metadata

    @staticmethod
    def _fetch_with_requests(url: str) -> tuple[str, str, dict[str, Any]]:
        """Fetch using plain requests and return (text, html, metadata)."""
        resp = requests.get(
            url,
            timeout=30,
            headers={
                "User-Agent": _USER_AGENT,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
            },
        )
        resp.raise_for_status()
        html = resp.text
        text = _extract_text_from_html(html)
        metadata = _extract_metadata_from_html(html)
        return text, html, metadata

    def fetch_page(
        self, url: str, anti_bot_level: str = "low"
    ) -> tuple[str, str, dict[str, Any]]:
        """Fetch a page and return ``(text, html, metadata)``.

        Tries Scrapling first, falls back to requests on failure.

        :param url: The URL to fetch.
        :param anti_bot_level: One of ``"low"``, ``"medium"``, ``"high"``.
        :returns: Tuple of (visible_text, raw_html, metadata_dict).
        :raises ScrapingError: When both fetchers fail.
        """
        # --- Try Scrapling ---
        if _scrapling_available:
            try:
                return self._fetch_with_scrapling(url, anti_bot_level)
            except Exception as exc:
                logger.warning("Scrapling fetch failed for %s (%s), falling back to requests", url, exc)

        # --- Fallback to requests ---
        try:
            return self._fetch_with_requests(url)
        except Exception as exc:
            logger.error("Failed to fetch %s with requests: %s", url, exc)
            raise ScrapingError(f"Failed to fetch {url}: {exc}") from exc
