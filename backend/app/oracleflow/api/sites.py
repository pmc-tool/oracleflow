"""Site monitoring API endpoints."""

import logging
import threading
from urllib.parse import urlparse

from flask import current_app, g, jsonify, request

logger = logging.getLogger(__name__)
from sqlalchemy import func, select
from sqlalchemy.orm import joinedload

from . import sites_bp
from app.oracleflow.auth.middleware import require_auth
from app.oracleflow.auth.models import PLAN_LIMITS
from app.oracleflow.database import get_session
from app.oracleflow.models.site import MonitoredSite, PageDiff, PageSnapshot, SitePage
from app.oracleflow.discovery.service import DiscoveryService


def _get_db():
    return get_session()


def _run_discovery(url, max_pages, site_id, app):
    """Run site discovery in a background thread."""
    with app.app_context():
        db = _get_db()
        try:
            service = DiscoveryService()
            service.discover(db=db, url=url, max_pages=max_pages, site_id=site_id)
            db.commit()
        except Exception:
            db.rollback()
        finally:
            db.close()


@sites_bp.route('/', methods=['POST'])
@require_auth
def create_site():
    """Create a MonitoredSite and run discovery in background."""
    db = _get_db()
    try:
        # --- Plan limit enforcement ---
        current_count = db.execute(
            select(func.count()).select_from(MonitoredSite).where(
                MonitoredSite.organization_id == g.org_id
            )
        ).scalar() or 0
        plan_limit = PLAN_LIMITS.get(g.plan, PLAN_LIMITS['free'])['max_sites']
        if current_count >= plan_limit:
            return jsonify({
                "error": "Plan limit reached",
                "upgrade": True,
                "limit": plan_limit,
            }), 403

        data = request.get_json()
        if not data or not data.get('url'):
            return jsonify({"success": False, "error": "url is required"}), 400

        url = data['url'].strip()
        if not url.startswith('http://') and not url.startswith('https://'):
            url = 'https://' + url
        max_pages = data.get('max_pages', 100)

        parsed = urlparse(url)
        domain = parsed.netloc
        if not domain:
            return jsonify({"success": False, "error": "Invalid URL"}), 400

        site = MonitoredSite(url=url, domain=domain, status="discovering",
                             organization_id=g.org_id)
        db.add(site)
        db.commit()

        site_id = site.id

        # Run discovery in background thread
        app = current_app._get_current_object()
        threading.Thread(
            target=_run_discovery,
            args=(url, max_pages, site_id, app),
            daemon=True,
        ).start()

        return jsonify({
            "success": True,
            "data": {
                "site_id": site_id,
                "message": f"Discovery started for {url}",
            }
        }), 201
    except Exception as e:
        db.rollback()
        logger.exception("Sites API error: %s", e)
        return jsonify({"success": False, "error": "An internal error occurred"}), 500
    finally:
        db.close()


@sites_bp.route('/', methods=['GET'])
@require_auth
def list_sites():
    """List MonitoredSite records scoped to the authenticated org."""
    db = _get_db()
    try:
        stmt = select(MonitoredSite).where(
            MonitoredSite.organization_id == g.org_id
        ).order_by(MonitoredSite.id.desc())
        result = db.execute(stmt)
        sites = list(result.scalars().all())

        data = []
        for s in sites:
            # Count total diffs (changes) across all pages for this site
            total_changes = db.execute(
                select(func.count()).select_from(PageDiff)
                .join(SitePage, PageDiff.page_id == SitePage.id)
                .where(SitePage.site_id == s.id)
            ).scalar() or 0

            # Get most recent last_crawled across all pages
            last_checked = db.execute(
                select(func.max(SitePage.last_crawled))
                .where(SitePage.site_id == s.id)
            ).scalar()

            data.append({
                "id": s.id,
                "url": s.url,
                "domain": s.domain,
                "status": s.status,
                "discovered_pages_count": s.discovered_pages_count,
                "total_changes": total_changes,
                "last_checked_at": last_checked.isoformat() if last_checked else None,
                "created_at": s.created_at.isoformat() if s.created_at else None,
                "updated_at": s.updated_at.isoformat() if s.updated_at else None,
            })

        return jsonify({"success": True, "data": data, "total": len(data)})
    except Exception as e:
        db.rollback()
        logger.exception("Sites API error: %s", e)
        return jsonify({"success": False, "error": "An internal error occurred"}), 500
    finally:
        db.close()


@sites_bp.route('/<int:site_id>', methods=['GET'])
@require_auth
def get_site(site_id):
    """Get site detail with pages (org-scoped)."""
    db = _get_db()
    try:
        stmt = (
            select(MonitoredSite)
            .options(joinedload(MonitoredSite.pages))
            .where(MonitoredSite.id == site_id,
                   MonitoredSite.organization_id == g.org_id)
        )
        result = db.execute(stmt)
        site = result.unique().scalar_one_or_none()

        if not site:
            return jsonify({"success": False, "error": f"Site {site_id} not found"}), 404

        pages = []
        for p in site.pages:
            pages.append({
                "id": p.id,
                "url": p.url,
                "path": p.path,
                "page_type": p.page_type,
                "importance_score": p.importance_score,
                "monitoring_frequency": p.monitoring_frequency,
                "anti_bot_level": p.anti_bot_level,
                "last_crawled": p.last_crawled.isoformat() if p.last_crawled else None,
                "is_active": p.is_active,
            })

        data = {
            "id": site.id,
            "url": site.url,
            "domain": site.domain,
            "status": site.status,
            "discovered_pages_count": site.discovered_pages_count,
            "created_at": site.created_at.isoformat() if site.created_at else None,
            "updated_at": site.updated_at.isoformat() if site.updated_at else None,
            "pages": pages,
        }

        return jsonify({"success": True, "data": data})
    except Exception as e:
        db.rollback()
        logger.exception("Sites API error: %s", e)
        return jsonify({"success": False, "error": "An internal error occurred"}), 500
    finally:
        db.close()


@sites_bp.route('/<int:site_id>', methods=['DELETE'])
@require_auth
def delete_site(site_id):
    """Set site status to inactive (org-scoped)."""
    db = _get_db()
    try:
        stmt = select(MonitoredSite).where(
            MonitoredSite.id == site_id,
            MonitoredSite.organization_id == g.org_id,
        )
        result = db.execute(stmt)
        site = result.scalar_one_or_none()

        if not site:
            return jsonify({"success": False, "error": f"Site {site_id} not found"}), 404

        site.status = "inactive"
        db.commit()

        return jsonify({
            "success": True,
            "data": {"message": f"Site {site_id} set to inactive"}
        })
    except Exception as e:
        db.rollback()
        logger.exception("Sites API error: %s", e)
        return jsonify({"success": False, "error": "An internal error occurred"}), 500
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Page-level endpoints
# ---------------------------------------------------------------------------

@sites_bp.route('/<int:site_id>/pages', methods=['GET'])
@require_auth
def list_pages(site_id):
    """Return all pages for a site with their last snapshot info and change count.

    Response includes per-page: id, url, path, page_type, importance_score,
    last_crawled, is_active, last_snapshot (hash + captured_at), and
    diff_count (total number of PageDiff records).
    """
    db = _get_db()
    try:
        # Verify site belongs to the authenticated org
        site_stmt = select(MonitoredSite).where(
            MonitoredSite.id == site_id,
            MonitoredSite.organization_id == g.org_id,
        )
        site = db.execute(site_stmt).scalar_one_or_none()
        if not site:
            return jsonify({"success": False, "error": f"Site {site_id} not found"}), 404

        # Load pages
        pages_stmt = (
            select(SitePage)
            .where(SitePage.site_id == site_id)
            .order_by(SitePage.id)
        )
        pages = list(db.execute(pages_stmt).scalars().all())

        data = []
        for p in pages:
            # Last snapshot
            snap_stmt = (
                select(PageSnapshot)
                .where(PageSnapshot.page_id == p.id)
                .order_by(PageSnapshot.captured_at.desc())
                .limit(1)
            )
            last_snap = db.execute(snap_stmt).scalar_one_or_none()

            # Diff count
            diff_count = db.execute(
                select(func.count()).select_from(PageDiff).where(PageDiff.page_id == p.id)
            ).scalar() or 0

            last_snapshot_info = None
            if last_snap:
                last_snapshot_info = {
                    "id": last_snap.id,
                    "content_hash": last_snap.content_hash,
                    "captured_at": last_snap.captured_at.isoformat() if last_snap.captured_at else None,
                }

            data.append({
                "id": p.id,
                "url": p.url,
                "path": p.path,
                "page_type": p.page_type,
                "importance_score": p.importance_score,
                "monitoring_frequency": p.monitoring_frequency,
                "anti_bot_level": p.anti_bot_level,
                "last_crawled": p.last_crawled.isoformat() if p.last_crawled else None,
                "content_hash": p.content_hash,
                "is_active": p.is_active,
                "last_snapshot": last_snapshot_info,
                "diff_count": diff_count,
            })

        return jsonify({"success": True, "data": data, "total": len(data)})
    except Exception as e:
        db.rollback()
        logger.exception("Sites API error: %s", e)
        return jsonify({"success": False, "error": "An internal error occurred"}), 500
    finally:
        db.close()


@sites_bp.route('/<int:site_id>/pages/<int:page_id>/diffs', methods=['GET'])
@require_auth
def list_page_diffs(site_id, page_id):
    """Return the diff history for a specific page (org-scoped).

    Supports optional query params: ``limit`` (default 50) and ``offset``
    (default 0) for pagination.  Results are ordered newest-first.
    """
    db = _get_db()
    try:
        # Verify site + page ownership
        site_stmt = select(MonitoredSite).where(
            MonitoredSite.id == site_id,
            MonitoredSite.organization_id == g.org_id,
        )
        site = db.execute(site_stmt).scalar_one_or_none()
        if not site:
            return jsonify({"success": False, "error": f"Site {site_id} not found"}), 404

        page_stmt = select(SitePage).where(
            SitePage.id == page_id,
            SitePage.site_id == site_id,
        )
        page = db.execute(page_stmt).scalar_one_or_none()
        if not page:
            return jsonify({"success": False, "error": f"Page {page_id} not found"}), 404

        limit = min(int(request.args.get("limit", 50)), 200)
        offset = int(request.args.get("offset", 0))

        # Total count
        total = db.execute(
            select(func.count()).select_from(PageDiff).where(PageDiff.page_id == page_id)
        ).scalar() or 0

        diffs_stmt = (
            select(PageDiff)
            .where(PageDiff.page_id == page_id)
            .order_by(PageDiff.detected_at.desc())
            .limit(limit)
            .offset(offset)
        )
        diffs = list(db.execute(diffs_stmt).scalars().all())

        data = []
        for d in diffs:
            data.append({
                "id": d.id,
                "diff_type": d.diff_type,
                "diff_summary": d.diff_summary,
                "significance_score": (d.diff_detail_json or {}).get("significance_score"),
                "change_percentage": (d.diff_detail_json or {}).get("change_percentage"),
                "old_snapshot_id": d.old_snapshot_id,
                "new_snapshot_id": d.new_snapshot_id,
                "detected_at": d.detected_at.isoformat() if d.detected_at else None,
            })

        return jsonify({
            "success": True,
            "data": data,
            "total": total,
            "limit": limit,
            "offset": offset,
        })
    except Exception as e:
        db.rollback()
        logger.exception("Sites API error: %s", e)
        return jsonify({"success": False, "error": "An internal error occurred"}), 500
    finally:
        db.close()


@sites_bp.route('/<int:site_id>/pages/<int:page_id>/diffs/<int:diff_id>', methods=['GET'])
@require_auth
def get_page_diff(site_id, page_id, diff_id):
    """Return a specific diff with before/after content.

    The response includes the diff metadata plus ``before`` and ``after``
    objects each containing ``content_text``, ``content_hash``, and
    ``captured_at`` from the corresponding snapshot.
    """
    db = _get_db()
    try:
        # Verify ownership chain: org -> site -> page -> diff
        site_stmt = select(MonitoredSite).where(
            MonitoredSite.id == site_id,
            MonitoredSite.organization_id == g.org_id,
        )
        site = db.execute(site_stmt).scalar_one_or_none()
        if not site:
            return jsonify({"success": False, "error": f"Site {site_id} not found"}), 404

        page_stmt = select(SitePage).where(
            SitePage.id == page_id,
            SitePage.site_id == site_id,
        )
        page = db.execute(page_stmt).scalar_one_or_none()
        if not page:
            return jsonify({"success": False, "error": f"Page {page_id} not found"}), 404

        diff_stmt = select(PageDiff).where(
            PageDiff.id == diff_id,
            PageDiff.page_id == page_id,
        )
        diff = db.execute(diff_stmt).scalar_one_or_none()
        if not diff:
            return jsonify({"success": False, "error": f"Diff {diff_id} not found"}), 404

        # Clean text helper — strip JS/HTML/ad garbage from stored snapshots
        def _clean_text(text):
            if not text:
                return ""
            import re
            t = text
            # Strip any remaining HTML tags
            t = re.sub(r"<script[\s\S]*?</script>", " ", t, flags=re.IGNORECASE)
            t = re.sub(r"<style[\s\S]*?</style>", " ", t, flags=re.IGNORECASE)
            t = re.sub(r"<noscript[\s\S]*?</noscript>", " ", t, flags=re.IGNORECASE)
            t = re.sub(r"<!--[\s\S]*?-->", " ", t)
            t = re.sub(r"<[^>]+>", " ", t)
            # HTML entities
            t = t.replace("&#x27;", "'").replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">").replace("&nbsp;", " ")
            t = re.sub(r"&#\d+;", " ", t)
            t = re.sub(r"&\w+;", " ", t)
            # JS code patterns (the main problem — stored text has inline JS)
            t = re.sub(r"\bfunction\s*\([^)]*\)\s*\{[\s\S]*?\}", " ", t)
            t = re.sub(r"\bvar\s+\w+\s*=[\s\S]*?;", " ", t)
            t = re.sub(r"\$\s*\([^)]*\)\s*\.\w+\([\s\S]*?\)", " ", t)
            t = re.sub(r"googletag\.[^\n;]+[;\n]?", " ", t)
            t = re.sub(r"navigator\.\w+[\s\S]*?;", " ", t)
            t = re.sub(r"document\.\w+[\s\S]*?;", " ", t)
            t = re.sub(r"window\.\w+[\s\S]*?;", " ", t)
            t = re.sub(r"\$\(\s*document\s*\)[\s\S]*?;", " ", t)
            t = re.sub(r"\.ajax\s*\([\s\S]*?\)", " ", t)
            t = re.sub(r"\.ready\s*\([\s\S]*?\)", " ", t)
            t = re.sub(r"\{[\"'][^{}]{0,200}:[^{}]{0,200}\}", " ", t)
            t = re.sub(r"@(context|type|graph|id)\b[^\n]*", " ", t)
            # Remove lines that are mostly non-alpha (JS/CSS residue)
            lines = t.split("\n")
            clean_lines = []
            for line in lines:
                stripped = line.strip()
                if not stripped:
                    continue
                alpha_count = sum(1 for c in stripped if c.isalpha() or c == ' ')
                if len(stripped) > 0 and alpha_count / len(stripped) > 0.5:
                    clean_lines.append(stripped)
            t = "\n".join(clean_lines)
            t = re.sub(r"\s+", " ", t).strip()
            # Truncate to 30KB
            return t[:30000] if len(t) > 30000 else t

        # Load before/after snapshots
        before = None
        if diff.old_snapshot_id:
            old_snap = db.execute(
                select(PageSnapshot).where(PageSnapshot.id == diff.old_snapshot_id)
            ).scalar_one_or_none()
            if old_snap:
                before = {
                    "id": old_snap.id,
                    "content_text": _clean_text(old_snap.content_text),
                    "content_hash": old_snap.content_hash,
                    "metadata": old_snap.metadata_json,
                    "captured_at": old_snap.captured_at.isoformat() if old_snap.captured_at else None,
                }

        after = None
        if diff.new_snapshot_id:
            new_snap = db.execute(
                select(PageSnapshot).where(PageSnapshot.id == diff.new_snapshot_id)
            ).scalar_one_or_none()
            if new_snap:
                after = {
                    "id": new_snap.id,
                    "content_text": _clean_text(new_snap.content_text),
                    "content_hash": new_snap.content_hash,
                    "metadata": new_snap.metadata_json,
                    "captured_at": new_snap.captured_at.isoformat() if new_snap.captured_at else None,
                }

        data = {
            "id": diff.id,
            "page_id": diff.page_id,
            "diff_type": diff.diff_type,
            "diff_summary": diff.diff_summary,
            "diff_detail": diff.diff_detail_json,
            "significance_score": (diff.diff_detail_json or {}).get("significance_score"),
            "change_percentage": (diff.diff_detail_json or {}).get("change_percentage"),
            "old_snapshot_id": diff.old_snapshot_id,
            "new_snapshot_id": diff.new_snapshot_id,
            "detected_at": diff.detected_at.isoformat() if diff.detected_at else None,
            "before": before,
            "after": after,
        }

        return jsonify({"success": True, "data": data})
    except Exception as e:
        db.rollback()
        logger.exception("Sites API error: %s", e)
        return jsonify({"success": False, "error": "An internal error occurred"}), 500
    finally:
        db.close()
