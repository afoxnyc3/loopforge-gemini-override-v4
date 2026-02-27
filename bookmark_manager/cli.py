"""CLI entry point for the Bookmark Manager using Click."""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

import click

from bookmark_manager.database import DatabaseManager
from bookmark_manager.exceptions import (
    BookmarkNotFoundError,
    DuplicateBookmarkError,
    InvalidURLError,
    InvalidTagError,
    StorageError,
    ImportError as BmImportError,
    ExportError,
)
from bookmark_manager.service import BookmarkService
from bookmark_manager.formatters import (
    print_bookmark_table,
    print_bookmark_detail,
    print_tag_table,
    print_import_result,
    success,
    error,
    info,
)


def get_service() -> BookmarkService:
    """Initialize database and return a BookmarkService instance."""
    db_manager = DatabaseManager()
    db_manager.initialize()
    return BookmarkService(db_manager)


@click.group()
@click.version_option(package_name="bookmark-manager", prog_name="bookmark-manager")
def cli() -> None:
    """A command-line bookmark manager. Store, search, and organize URLs with tags."""


@cli.command("add")
@click.argument("url")
@click.option("-t", "--tag", "tags", multiple=True, help="Tag to attach (repeatable).")
@click.option("-T", "--title", default=None, help="Human-readable title for the bookmark.")
@click.option("-d", "--description", default=None, help="Optional description.")
def add_bookmark(url: str, tags: tuple[str, ...], title: Optional[str], description: Optional[str]) -> None:
    """Add a new bookmark for URL."""
    try:
        service = get_service()
        bookmark = service.add_bookmark(
            url=url,
            title=title,
            description=description,
            tags=list(tags),
        )
        success(f"Bookmark added (id={bookmark.id}): {bookmark.url}")
        if bookmark.tags:
            info(f"  Tags: {', '.join(bookmark.tags)}")
    except InvalidURLError as exc:
        error(f"Invalid URL: {exc}")
        sys.exit(1)
    except InvalidTagError as exc:
        error(f"Invalid tag: {exc}")
        sys.exit(1)
    except DuplicateBookmarkError as exc:
        error(f"Duplicate bookmark: {exc}")
        sys.exit(1)
    except StorageError as exc:
        error(f"Storage error: {exc}")
        sys.exit(1)


@cli.command("delete")
@click.argument("bookmark_id", type=int)
@click.option("-y", "--yes", is_flag=True, default=False, help="Skip confirmation prompt.")
def delete_bookmark(bookmark_id: int, yes: bool) -> None:
    """Delete a bookmark by its ID."""
    if not yes:
        confirmed = click.confirm(f"Delete bookmark {bookmark_id}?", default=False)
        if not confirmed:
            info("Aborted.")
            return
    try:
        service = get_service()
        service.delete_bookmark(bookmark_id)
        success(f"Bookmark {bookmark_id} deleted.")
    except BookmarkNotFoundError as exc:
        error(f"Not found: {exc}")
        sys.exit(1)
    except StorageError as exc:
        error(f"Storage error: {exc}")
        sys.exit(1)


@cli.command("list")
@click.option("-t", "--tag", "tags", multiple=True, help="Filter by tag (repeatable, AND logic).")
@click.option("-l", "--limit", default=50, show_default=True, help="Maximum number of results.")
@click.option("-o", "--offset", default=0, show_default=True, help="Result offset for pagination.")
def list_bookmarks(tags: tuple[str, ...], limit: int, offset: int) -> None:
    """List bookmarks, optionally filtered by tags."""
    try:
        service = get_service()
        if tags:
            bookmarks = service.get_bookmarks_by_tags(list(tags), limit=limit, offset=offset)
        else:
            bookmarks = service.list_bookmarks(limit=limit, offset=offset)
        if not bookmarks:
            info("No bookmarks found.")
            return
        print_bookmark_table(bookmarks)
        info(f"\n{len(bookmarks)} bookmark(s) shown.")
    except StorageError as exc:
        error(f"Storage error: {exc}")
        sys.exit(1)


@cli.command("search")
@click.argument("query")
@click.option("-l", "--limit", default=50, show_default=True, help="Maximum number of results.")
def search_bookmarks(query: str, limit: int) -> None:
    """Search bookmarks by keyword (matches URL, title, description)."""
    try:
        service = get_service()
        bookmarks = service.search_bookmarks(query, limit=limit)
        if not bookmarks:
            info(f"No bookmarks matching '{query}'.")
            return
        print_bookmark_table(bookmarks)
        info(f"\n{len(bookmarks)} bookmark(s) found.")
    except StorageError as exc:
        error(f"Storage error: {exc}")
        sys.exit(1)


@cli.command("show")
@click.argument("bookmark_id", type=int)
def show_bookmark(bookmark_id: int) -> None:
    """Show full details of a single bookmark."""
    try:
        service = get_service()
        bookmark = service.get_bookmark(bookmark_id)
        print_bookmark_detail(bookmark)
    except BookmarkNotFoundError as exc:
        error(f"Not found: {exc}")
        sys.exit(1)
    except StorageError as exc:
        error(f"Storage error: {exc}")
        sys.exit(1)


@cli.command("tags")
@click.option("-l", "--limit", default=100, show_default=True, help="Maximum number of tags to show.")
def list_tags(limit: int) -> None:
    """List all tags with their bookmark counts."""
    try:
        service = get_service()
        tag_counts = service.list_tags(limit=limit)
        if not tag_counts:
            info("No tags found.")
            return
        print_tag_table(tag_counts)
    except StorageError as exc:
        error(f"Storage error: {exc}")
        sys.exit(1)


@cli.command("import-html")
@click.argument("filepath", type=click.Path(exists=True, readable=True, path_type=Path))
@click.option("--skip-duplicates", is_flag=True, default=True, show_default=True,
              help="Silently skip duplicate URLs instead of failing.")
def import_html(filepath: Path, skip_duplicates: bool) -> None:
    """Import bookmarks from a browser-exported HTML file."""
    try:
        service = get_service()
        result = service.import_from_html(filepath, skip_duplicates=skip_duplicates)
        print_import_result(result, filepath)
    except BmImportError as exc:
        error(f"Import failed: {exc}")
        sys.exit(1)
    except StorageError as exc:
        error(f"Storage error during import: {exc}")
        sys.exit(1)


@cli.command("export-html")
@click.argument("filepath", type=click.Path(writable=True, path_type=Path))
@click.option("-t", "--tag", "tags", multiple=True, help="Export only bookmarks with these tags.")
def export_html(filepath: Path, tags: tuple[str, ...]) -> None:
    """Export bookmarks to a browser-compatible HTML file."""
    try:
        service = get_service()
        count = service.export_to_html(filepath, tags=list(tags) if tags else None)
        success(f"Exported {count} bookmark(s) to {filepath}")
    except ExportError as exc:
        error(f"Export failed: {exc}")
        sys.exit(1)
    except StorageError as exc:
        error(f"Storage error during export: {exc}")
        sys.exit(1)


@cli.command("update")
@click.argument("bookmark_id", type=int)
@click.option("-T", "--title", default=None, help="New title.")
@click.option("-d", "--description", default=None, help="New description.")
@click.option("-t", "--tag", "tags", multiple=True, help="Replace all tags with these (repeatable).")
def update_bookmark(
    bookmark_id: int,
    title: Optional[str],
    description: Optional[str],
    tags: tuple[str, ...],
) -> None:
    """Update title, description, or tags of an existing bookmark."""
    if not title and not description and not tags:
        error("Provide at least one of --title, --description, or --tag to update.")
        sys.exit(1)
    try:
        service = get_service()
        bookmark = service.update_bookmark(
            bookmark_id=bookmark_id,
            title=title,
            description=description,
            tags=list(tags) if tags else None,
        )
        success(f"Bookmark {bookmark_id} updated.")
        print_bookmark_detail(bookmark)
    except BookmarkNotFoundError as exc:
        error(f"Not found: {exc}")
        sys.exit(1)
    except InvalidTagError as exc:
        error(f"Invalid tag: {exc}")
        sys.exit(1)
    except StorageError as exc:
        error(f"Storage error: {exc}")
        sys.exit(1)
