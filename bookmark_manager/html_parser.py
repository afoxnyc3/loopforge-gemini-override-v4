"""Netscape bookmark HTML parser and exporter.

Parses the Netscape Bookmark File Format used by Chrome, Firefox, Edge, and
Safari for bookmark import/export.  Also generates compatible HTML for export.
"""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Generator, List, Optional

try:
    from bs4 import BeautifulSoup, Tag as BSTag
except ImportError as exc:  # pragma: no cover
    raise ImportError(
        "beautifulsoup4 is required for HTML import/export. "
        "Install it with: pip install beautifulsoup4"
    ) from exc

from bookmark_manager.exceptions import ExportError
from bookmark_manager.exceptions import ImportError as BMImportError
from bookmark_manager.models import Bookmark, ImportResult
from bookmark_manager.service import BookmarkService

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Internal data structure for a parsed bookmark entry
# ---------------------------------------------------------------------------


class _ParsedEntry:
    """Intermediate representation of a bookmark parsed from HTML."""

    __slots__ = ("url", "title", "description", "tags", "add_date")

    def __init__(
        self,
        url: str,
        title: str,
        description: str = "",
        tags: Optional[List[str]] = None,
        add_date: Optional[str] = None,
    ) -> None:
        self.url = url
        self.title = title
        self.description = description
        self.tags: List[str] = tags or []
        self.add_date = add_date


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------


class BookmarkHTMLParser:
    """Parses Netscape-format bookmark HTML files.

    Supports:
    - Flat and nested DL/DT/DD structures
    - TAGS attribute on <A> elements (comma-separated)
    - Descriptions in <DD> elements following a bookmark <DT>
    - ADD_DATE attribute (stored for reference, not currently persisted)
    """

    def parse_file(self, filepath: str | Path) -> List[_ParsedEntry]:
        """Parse a bookmark HTML file and return a list of parsed entries.

        Args:
            filepath: Path to the Netscape bookmark HTML file.

        Returns:
            List of ``_ParsedEntry`` objects.

        Raises:
            BMImportError: If the file cannot be read or parsed.
        """
        path = Path(filepath)
        if not path.exists():
            raise BMImportError(str(filepath), "File not found")
        if not path.is_file():
            raise BMImportError(str(filepath), "Path is not a file")

        try:
            html = path.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            raise BMImportError(str(filepath), f"Cannot read file: {exc}") from exc

        try:
            soup = BeautifulSoup(html, "html.parser")
        except Exception as exc:  # noqa: BLE001
            raise BMImportError(str(filepath), f"HTML parse error: {exc}") from exc

        entries = list(self._extract_entries(soup))
        logger.debug("Parsed %d bookmark entries from %s", len(entries), filepath)
        return entries

    # ------------------------------------------------------------------
    # Private extraction logic
    # ------------------------------------------------------------------

    def _extract_entries(self, soup: BeautifulSoup) -> Generator[_ParsedEntry, None, None]:
        """Walk all <A> tags that look like bookmarks."""
        for a_tag in soup.find_all("a"):
            href = a_tag.get("href", "").strip()
            if not href or href.startswith("javascript:"):
                continue

            title = a_tag.get_text(strip=True)
            add_date = a_tag.get("add_date") or a_tag.get("ADD_DATE")

            # Tags attribute (comma-separated)
            tags_attr = a_tag.get("tags") or a_tag.get("TAGS") or ""
            tags = [t.strip() for t in tags_attr.split(",") if t.strip()]

            # Description: look for a <DD> sibling immediately after the parent <DT>
            description = self._extract_description(a_tag)

            yield _ParsedEntry(
                url=href,
                title=title,
                description=description,
                tags=tags,
                add_date=str(add_date) if add_date else None,
            )

    @staticmethod
    def _extract_description(a_tag: BSTag) -> str:
        """Extract the description from a <DD> sibling of the parent <DT>."""
        parent = a_tag.parent  # typically <DT>
        if parent is None:
            return ""
        # Look for the next sibling that is a <DD> element
        sibling = parent.find_next_sibling()
        if sibling and sibling.name and sibling.name.lower() == "dd":
            return sibling.get_text(strip=True)
        return ""


# ---------------------------------------------------------------------------
# Import pipeline
# ---------------------------------------------------------------------------


def import_bookmarks_from_html(
    filepath: str | Path,
    service: BookmarkService,
    default_tags: Optional[List[str]] = None,
) -> ImportResult:
    """Parse a Netscape bookmark HTML file and import all bookmarks via service.

    Args:
        filepath: Path to the HTML file.
        service: BookmarkService instance used to persist bookmarks.
        default_tags: Additional tags to apply to every imported bookmark.

    Returns:
        ImportResult summarising what happened.

    Raises:
        BMImportError: If the file cannot be read or parsed at all.
    """
    parser = BookmarkHTMLParser()
    entries = parser.parse_file(filepath)  # may raise BMImportError

    result = ImportResult()
    extra_tags = default_tags or []

    for entry in entries:
        combined_tags = list(dict.fromkeys(entry.tags + extra_tags))  # preserve order, dedup
        service.import_bookmark(
            url=entry.url,
            title=entry.title,
            description=entry.description,
            tags=combined_tags,
            result=result,
        )

    logger.info(
        "Import from %s: %d imported, %d skipped, %d errors",
        filepath,
        result.imported,
        result.skipped,
        len(result.errors),
    )
    return result


# ---------------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------------


HTML_TEMPLATE = """<!DOCTYPE NETSCAPE-Bookmark-file-1>
<!-- This is an automatically generated file.
     It will be read and overwritten.
     DO NOT EDIT! -->
<META HTTP-EQUIV="Content-Type" CONTENT="text/html; charset=UTF-8">
<TITLE>Bookmarks</TITLE>
<H1>Bookmarks</H1>
<DL><p>
{entries}
</DL><p>
"""

ENTRY_TEMPLATE = '    <DT><A HREF="{url}" ADD_DATE="{add_date}" TAGS="{tags}">{title}</A>\n{description}'


def export_bookmarks_to_html(
    bookmarks: List[Bookmark],
    filepath: str | Path,
) -> None:
    """Export a list of bookmarks to a Netscape-format HTML file.

    Args:
        bookmarks: List of Bookmark objects to export.
        filepath: Destination file path.  Parent directories are created.

    Raises:
        ExportError: If the file cannot be written.
    """
    path = Path(filepath)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise ExportError(str(filepath), f"Cannot create directory: {exc}") from exc

    entry_lines: List[str] = []
    for bm in bookmarks:
        add_date = int(bm.created_at.timestamp())
        tags_str = ",".join(bm.tags)
        title = _escape_html(bm.title or bm.url)
        desc_line = ""
        if bm.description:
            desc_line = f"    <DD>{_escape_html(bm.description)}\n"
        entry = ENTRY_TEMPLATE.format(
            url=_escape_html(bm.url),
            add_date=add_date,
            tags=_escape_html(tags_str),
            title=title,
            description=desc_line,
        )
        entry_lines.append(entry)

    html_content = HTML_TEMPLATE.format(entries="\n".join(entry_lines))

    try:
        path.write_text(html_content, encoding="utf-8")
    except OSError as exc:
        raise ExportError(str(filepath), f"Cannot write file: {exc}") from exc

    logger.info("Exported %d bookmarks to %s", len(bookmarks), filepath)


def _escape_html(text: str) -> str:
    """Minimal HTML escaping for attribute values and text content."""
    return (
        text
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )
