"""Site discovery spider -- crawls a target site and extracts page data."""

from __future__ import annotations

import logging
from urllib.parse import urlparse

from scrapling.fetchers import FetcherSession
from scrapling.spiders.spider import Spider
from scrapling.spiders.request import Request
from scrapling.spiders.session import SessionManager

from app.config import Config

from typing import TYPE_CHECKING, Any, Dict, AsyncGenerator

if TYPE_CHECKING:
    from scrapling.engines.toolbelt.custom import Response


class SiteDiscoverySpider(Spider):
    """Crawl a single site, extract content and links up to *max_pages*."""

    name = "site_discovery"
    download_delay: float = Config.OF_DEFAULT_DOWNLOAD_DELAY
    logging_level: int = logging.INFO

    def __init__(self, url: str, max_pages: int = 100, **kwargs: Any) -> None:
        parsed = urlparse(url)
        self.start_urls = [url]
        self.allowed_domains = {parsed.netloc}
        self._max_pages = max_pages
        self._pages_crawled = 0
        super().__init__(**kwargs)

    def configure_sessions(self, manager: SessionManager) -> None:
        """Add a FetcherSession configured with the project SSL setting."""
        manager.add(
            "default",
            FetcherSession(verify=Config.OF_VERIFY_SSL),
        )

    async def parse(self, response: "Response") -> AsyncGenerator[Dict[str, Any] | Request | None, None]:
        """Extract page content and follow internal links."""
        if self._pages_crawled >= self._max_pages:
            return

        self._pages_crawled += 1

        # --- extract page data ------------------------------------------------
        title = response.css("title::text").get() or ""
        title = str(title).strip()

        meta_desc = ""
        meta_tags = response.css('meta[name="description"]')
        if meta_tags:
            meta_desc = meta_tags[0].attrib.get("content", "")

        # Collect visible text
        all_text = response.css("body ::text").getall()
        text = "\n".join(str(t).strip() for t in all_text if str(t).strip())

        # Collect all anchor hrefs
        links: list[str] = []
        for anchor in response.css("a"):
            href = anchor.attrib.get("href")
            if href:
                links.append(href)

        html = response.body.decode("utf-8", errors="replace") if isinstance(response.body, bytes) else str(response.body)

        yield {
            "url": response.url,
            "title": title,
            "meta_description": meta_desc,
            "text": text,
            "links": links,
            "html": html,
        }

        # --- follow internal links --------------------------------------------
        if self._pages_crawled < self._max_pages:
            for href in links:
                if self._pages_crawled >= self._max_pages:
                    break
                # Only follow links that stay within allowed domains
                try:
                    parsed = urlparse(href)
                    # Skip non-http schemes, anchors-only, mailto, javascript, etc.
                    if parsed.scheme and parsed.scheme not in ("http", "https"):
                        continue
                    # If it has a netloc, check domain; relative links are fine
                    if parsed.netloc and parsed.netloc not in self.allowed_domains:
                        continue
                except Exception:
                    continue

                yield response.follow(href, callback=self.parse)
