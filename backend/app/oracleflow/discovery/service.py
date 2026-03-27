"""Discovery service -- orchestrates spider, classifier, strategy, and snapshots."""

from __future__ import annotations

import logging
from urllib.parse import urlparse

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.oracleflow.exceptions import ScrapingError
from app.oracleflow.models.site import MonitoredSite, SitePage

from app.oracleflow.discovery.classifier import PageClassifier
from app.oracleflow.discovery.schemas import DiscoveryResult, PageClassification
from app.oracleflow.discovery.snapshot import SnapshotManager
from app.oracleflow.discovery.spider import SiteDiscoverySpider
from app.oracleflow.discovery.strategy import MonitoringStrategyGenerator

logger = logging.getLogger(__name__)


class DiscoveryService:
    """High-level service that discovers, classifies, and stores site pages."""

    def __init__(
        self,
        classifier: PageClassifier | None = None,
        snapshot_mgr: SnapshotManager | None = None,
    ) -> None:
        self._classifier = classifier or PageClassifier()
        self._snapshot_mgr = snapshot_mgr or SnapshotManager()

    def discover(
        self,
        db: Session,
        url: str,
        max_pages: int = 100,
        site_id: int | None = None,
    ) -> DiscoveryResult:
        """Run a full discovery cycle for the given URL.

        1. Create a MonitoredSite record (or use existing site_id).
        2. Crawl the site with SiteDiscoverySpider (sync).
        3. Classify each discovered page via the LLM/heuristic classifier.
        4. Create SitePage records and initial snapshots.
        5. Generate a monitoring strategy and update SitePage frequencies.
        6. Return a DiscoveryResult summary.
        """
        parsed = urlparse(url)
        domain = parsed.netloc

        if site_id is None:
            # ---- 1. Create MonitoredSite --------------------------------
            site = MonitoredSite(url=url, domain=domain, status="discovering")
            db.add(site)
            db.flush()
            site_id = site.id
        else:
            # Update existing site record
            stmt = select(MonitoredSite).where(MonitoredSite.id == site_id)
            result = db.execute(stmt)
            site = result.scalar_one()
            site.status = "discovering"

        # ---- 2. Crawl ---------------------------------------------------
        logger.info("Starting discovery spider for %s (max %d pages)", url, max_pages)
        try:
            crawl_result = self._run_spider(url, max_pages)
        except Exception as exc:
            logger.error("Spider failed for %s: %s", url, exc)
            site.status = "failed"
            raise ScrapingError(f"Spider failed: {exc}") from exc

        items = crawl_result.items
        logger.info("Spider finished for %s -- %d pages discovered", url, len(items))

        # ---- 3 & 4. Classify + persist pages + snapshots ----------------
        classifications: list[PageClassification] = []

        for item in items:
            page_url = item.get("url", "")
            title = item.get("title", "")
            text = item.get("text", "")
            html = item.get("html", "")
            meta_desc = item.get("meta_description", "")

            # Classify
            cls = self._classifier.classify_page(page_url, title, text)
            classifications.append(cls)

            # Create SitePage
            page_path = urlparse(page_url).path or "/"
            site_page = SitePage(
                site_id=site_id,
                url=page_url,
                path=page_path,
                page_type=cls.page_type.value,
            )
            db.add(site_page)
            db.flush()

            # Take initial snapshot
            self._snapshot_mgr.take_snapshot(
                db=db,
                page_id=site_page.id,
                content_text=text,
                content_html=html,
                metadata={
                    "title": title,
                    "meta_description": meta_desc,
                    "language": cls.language,
                    "org_type": cls.org_type,
                    "people": cls.people,
                    "topics": cls.topics,
                },
            )

        # ---- 5. Generate monitoring strategy ----------------------------
        freq_map = MonitoringStrategyGenerator.generate(classifications)

        # Update each SitePage with the recommended frequency
        for cls in classifications:
            freq = freq_map.get(cls.url)
            if freq is not None:
                for page in _get_pages_by_site(db, site_id):
                    if page.url == cls.url:
                        page.monitoring_frequency = freq.value
                        break

        # Finalise site record
        site.discovered_pages_count = len(items)
        site.status = "active"

        # ---- 6. Return result -------------------------------------------
        return DiscoveryResult(
            site_id=site_id,
            pages_found=len(items),
            classifications=classifications,
        )

    @staticmethod
    def _run_spider(url: str, max_pages: int):
        """Synchronous spider execution."""
        spider = SiteDiscoverySpider(url=url, max_pages=max_pages)
        return spider.start()


def _get_pages_by_site(db: Session, site_id: int) -> list[SitePage]:
    """Load all SitePages belonging to a site."""
    stmt = select(SitePage).where(SitePage.site_id == site_id)
    result = db.execute(stmt)
    return list(result.scalars().all())
