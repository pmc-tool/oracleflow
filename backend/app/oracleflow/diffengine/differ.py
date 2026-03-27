"""Pure diff functions -- no DB, no async, easily testable."""

from __future__ import annotations

import difflib
import re
from html.parser import HTMLParser

from app.oracleflow.constants import DiffType

from .schemas import DiffResult, MetaDiff, StructuralDiff


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

class _TagTextExtractor(HTMLParser):
    """Extract text content from specific HTML tags."""

    def __init__(self, target_tags: set[str]) -> None:
        super().__init__()
        self._target_tags = target_tags
        self._inside: list[str] = []
        self.items: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in self._target_tags:
            self._inside.append(tag)

    def handle_endtag(self, tag: str) -> None:
        if self._inside and self._inside[-1] == tag:
            self._inside.pop()

    def handle_data(self, data: str) -> None:
        if self._inside:
            text = data.strip()
            if text:
                self.items.append(text)


def _extract_nav_items(html: str) -> list[str]:
    """Return text items found inside <nav> and header <ul> elements."""
    parser = _TagTextExtractor({"nav"})
    parser.feed(html)
    return sorted(set(parser.items))


_HEADING_RE = re.compile(r"<(h[1-3])[^>]*>(.*?)</\1>", re.IGNORECASE | re.DOTALL)
_LINK_RE = re.compile(r"<a\s", re.IGNORECASE)


def _extract_headings(html: str) -> list[str]:
    return [re.sub(r"<[^>]+>", "", m.group(2)).strip() for m in _HEADING_RE.finditer(html)]


def _count_links(html: str) -> int:
    return len(_LINK_RE.findall(html))


# ---------------------------------------------------------------------------
# Public diff functions
# ---------------------------------------------------------------------------

def text_diff(old_text: str, new_text: str) -> DiffResult | None:
    """Compare two text strings and return a DiffResult or None if identical.

    Uses ``difflib.SequenceMatcher`` to compute a similarity ratio.  The
    summary includes the change percentage and a sample of changed phrases.
    """
    if old_text == new_text:
        return None

    matcher = difflib.SequenceMatcher(None, old_text, new_text)
    ratio = matcher.ratio()
    change_pct = round((1 - ratio) * 100, 2)

    # Collect a sample of changed phrases (up to 5)
    opcodes = matcher.get_opcodes()
    changed_phrases: list[str] = []
    for tag, i1, i2, j1, j2 in opcodes:
        if tag in ("replace", "insert"):
            phrase = new_text[j1:j2].strip()
            if phrase and len(phrase) < 200:
                changed_phrases.append(phrase)
            if len(changed_phrases) >= 5:
                break

    summary = f"{change_pct}% changed"
    if changed_phrases:
        summary += f"; key phrases: {', '.join(changed_phrases[:3])}"

    return DiffResult(
        diff_type=DiffType.CONTENT_CHANGED,
        summary=summary,
        detail={
            "change_percentage": change_pct,
            "similarity_ratio": round(ratio, 4),
            "changed_phrases": changed_phrases,
        },
    )


def structural_diff(old_html: str, new_html: str) -> StructuralDiff | None:
    """Compare structural elements of two HTML documents.

    Looks at navigation items, heading structure (h1-h3), and total link
    count.  Returns ``None`` if all structures are identical.
    """
    old_nav = _extract_nav_items(old_html)
    new_nav = _extract_nav_items(new_html)

    old_headings = _extract_headings(old_html)
    new_headings = _extract_headings(new_html)

    old_links = _count_links(old_html)
    new_links = _count_links(new_html)

    nav_added = sorted(set(new_nav) - set(old_nav))
    nav_removed = sorted(set(old_nav) - set(new_nav))
    headings_changed = old_headings != new_headings
    links_delta = new_links - old_links

    if not nav_added and not nav_removed and not headings_changed and links_delta == 0:
        return None

    return StructuralDiff(
        nav_items_added=nav_added,
        nav_items_removed=nav_removed,
        headings_changed=headings_changed,
        links_count_delta=links_delta,
    )


def metadata_diff(old_meta: dict, new_meta: dict) -> MetaDiff | None:
    """Compare metadata dicts (title, description, og:* tags).

    Returns ``None`` when both dicts are equivalent.
    """
    old_title = str(old_meta.get("title", ""))
    new_title = str(new_meta.get("title", ""))
    title_changed = old_title != new_title

    old_desc = str(old_meta.get("description", ""))
    new_desc = str(new_meta.get("description", ""))
    description_changed = old_desc != new_desc

    # Compare og:* tags
    og_changes: dict[str, dict[str, str]] = {}
    all_keys = {k for k in list(old_meta) + list(new_meta) if k.startswith("og:")}
    for key in sorted(all_keys):
        old_val = str(old_meta.get(key, ""))
        new_val = str(new_meta.get(key, ""))
        if old_val != new_val:
            og_changes[key] = {"old": old_val, "new": new_val}

    if not title_changed and not description_changed and not og_changes:
        return None

    return MetaDiff(
        title_changed=title_changed,
        old_title=old_title,
        new_title=new_title,
        description_changed=description_changed,
        old_description=old_desc,
        new_description=new_desc,
        og_tags_changed=og_changes,
    )
