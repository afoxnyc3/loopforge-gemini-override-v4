"""CLI interface for the bookmark manager using Click and Rich."""

import sys
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table
from rich import box

from bookmark_manager.config import (
    DB_PATH,
    DEFAULT_LIST_LIMIT,
    TAG_SEPARATOR,
    STYLE_SUCCESS,
    STYLE_ERROR,
    STYLE_WARNING,
    STYLE_INFO,
    STYLE_TAG,
    STYLE_DIM,
)
from bookmark_manager.database import Database
from bookmark_manager.repository import BookmarkRepository
from bookmark_manager.service import BookmarkService
from bookmark_manager.exceptions import (
    BookmarkNotFoundError,
    DuplicateBookmarkError,
    InvalidURLError,
    TagNotFoundError,
    BookmarkImportError,
    BookmarkExportError,
    DatabaseError,
    BookmarkManagerError,
)

console = Console()
err_console = Console(stderr=True)


def get_service(db_path: Path) -> BookmarkService:
    """Create and return a BookmarkService instance."""
    db = Database(db_path)
    repo = BookmarkRepository(db)
    return BookmarkService(repo)


@click.group()
@click.option(
    "--db",
    default=str(DB_PATH),
    envvar="BOOKMARK_DB",
    help="Path to SQLite database file.",
    show_default=True,
)
@click.version_option(version="1.0.0", prog_name="bm")
@click.pass_context
def cli(ctx: click.Context, db: str) -> None:
    """CLI Bookmark Manager — store and search URLs with tags."""
    ctx.ensure_object(dict)
    ctx.obj["db_path"] = Path(db)


@cli.command("add")
@click.argument("url")
@click.option("--title", "-t", default=None, help="Bookmark title.")
@click.option(
    "--tags",
    "-g",
    default=None,
    help="Comma-separated list of tags (e.g. python,dev).",
)
@click.option("--description", "-d", default=None, help="Optional description.")
@click.pass_context
def add_bookmark(ctx: click.Context, url: str, title: str, tags: str, description: str) -> None:
    """Add a new bookmark."""
    tag_list = [t.strip() for t in tags.split(TAG_SEPARATOR) if t.strip()] if tags else []
    try:
        service = get_service(ctx.obj["db_path"])
        bookmark = service.add_bookmark(
            url=url,
            title=title,
            tags=tag_list,
            description=description,
        )
        console.print(f"[{STYLE_SUCCESS}]✓ Bookmark added[/{STYLE_SUCCESS}] (id={bookmark.id})")
        console.print(f"  URL:   [{STYLE_INFO}]{bookmark.url}[/{STYLE_INFO}]")
        if bookmark.title:
            console.print(f"  Title: {bookmark.title}")
        if bookmark.tags:
            tags_str = " ".join(f"[{STYLE_TAG}]#{t}[/{STYLE_TAG}]" for t in bookmark.tags)
            console.print(f"  Tags:  {tags_str}")
    except DuplicateBookmarkError as e:
        err_console.print(f"[{STYLE_ERROR}]✗ Duplicate bookmark:[/{STYLE_ERROR}] {e}")
        sys.exit(1)
    except InvalidURLError as e:
        err_console.print(f"[{STYLE_ERROR}]✗ Invalid URL:[/{STYLE_ERROR}] {e}")
        sys.exit(1)
    except DatabaseError as e:
        err_console.print(f"[{STYLE_ERROR}]✗ Database error:[/{STYLE_ERROR}] {e}")
        sys.exit(1)
    except BookmarkManagerError as e:
        err_console.print(f"[{STYLE_ERROR}]✗ Error:[/{STYLE_ERROR}] {e}")
        sys.exit(1)


@cli.command("list")
@click.option("--tag", "-g", default=None, help="Filter by tag.")
@click.option(
    "--limit",
    "-n",
    default=DEFAULT_LIST_LIMIT,
    show_default=True,
    help="Maximum number of results.",
)
@click.option("--offset", default=0, help="Pagination offset.", hidden=True)
@click.pass_context
def list_bookmarks(ctx: click.Context, tag: str, limit: int, offset: int) -> None:
    """List bookmarks, optionally filtered by tag."""
    try:
        service = get_service(ctx.obj["db_path"])
        if tag:
            bookmarks = service.get_bookmarks_by_tag(tag, limit=limit, offset=offset)
        else:
            bookmarks = service.list_bookmarks(limit=limit, offset=offset)

        if not bookmarks:
            console.print(f"[{STYLE_DIM}]No bookmarks found.[/{STYLE_DIM}]")
            return

        table = Table(box=box.SIMPLE, show_header=True, header_style="bold")
        table.add_column("ID", style="dim", width=6)
        table.add_column("Title / URL", min_width=40)
        table.add_column("Tags", style=STYLE_TAG)
        table.add_column("Added", style="dim", width=12)

        for bm in bookmarks:
            title_url = f"{bm.title}\n[{STYLE_DIM}]{bm.url}[/{STYLE_DIM}]" if bm.title else bm.url
            tags_str = ", ".join(bm.tags) if bm.tags else ""
            added = bm.created_at.strftime("%Y-%m-%d") if bm.created_at else ""
            table.add_row(str(bm.id), title_url, tags_str, added)

        console.print(table)
        console.print(f"[{STYLE_DIM}]{len(bookmarks)} bookmark(s) shown.[/{STYLE_DIM}]")
    except TagNotFoundError as e:
        err_console.print(f"[{STYLE_WARNING}]⚠ Tag not found:[/{STYLE_WARNING}] {e}")
        sys.exit(1)
    except DatabaseError as e:
        err_console.print(f"[{STYLE_ERROR}]✗ Database error:[/{STYLE_ERROR}] {e}")
        sys.exit(1)
    except BookmarkManagerError as e:
        err_console.print(f"[{STYLE_ERROR}]✗ Error:[/{STYLE_ERROR}] {e}")
        sys.exit(1)


@cli.command("search")
@click.argument("query")
@click.option(
    "--limit",
    "-n",
    default=DEFAULT_LIST_LIMIT,
    show_default=True,
    help="Maximum number of results.",
)
@click.pass_context
def search_bookmarks(ctx: click.Context, query: str, limit: int) -> None:
    """Search bookmarks by URL, title, or description."""
    try:
        service = get_service(ctx.obj["db_path"])
        bookmarks = service.search_bookmarks(query, limit=limit)

        if not bookmarks:
            console.print(f"[{STYLE_DIM}]No results for '{query}'.[/{STYLE_DIM}]")
            return

        table = Table(box=box.SIMPLE, show_header=True, header_style="bold")
        table.add_column("ID", style="dim", width=6)
        table.add_column("Title / URL", min_width=40)
        table.add_column("Tags", style=STYLE_TAG)

        for bm in bookmarks:
            title_url = f"{bm.title}\n[{STYLE_DIM}]{bm.url}[/{STYLE_DIM}]" if bm.title else bm.url
            tags_str = ", ".join(bm.tags) if bm.tags else ""
            table.add_row(str(bm.id), title_url, tags_str)

        console.print(table)
        console.print(f"[{STYLE_DIM}]{len(bookmarks)} result(s) for '{query}'.[/{STYLE_DIM}]")
    except DatabaseError as e:
        err_console.print(f"[{STYLE_ERROR}]✗ Database error:[/{STYLE_ERROR}] {e}")
        sys.exit(1)
    except BookmarkManagerError as e:
        err_console.print(f"[{STYLE_ERROR}]✗ Error:[/{STYLE_ERROR}] {e}")
        sys.exit(1)


@cli.command("delete")
@click.argument("bookmark_id", type=int)
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation prompt.")
@click.pass_context
def delete_bookmark(ctx: click.Context, bookmark_id: int, yes: bool) -> None:
    """Delete a bookmark by ID."""
    try:
        if not yes:
            click.confirm(f"Delete bookmark {bookmark_id}?", abort=True)
        service = get_service(ctx.obj["db_path"])
        service.delete_bookmark(bookmark_id)
        console.print(f"[{STYLE_SUCCESS}]✓ Bookmark {bookmark_id} deleted.[/{STYLE_SUCCESS}]")
    except click.exceptions.Abort:
        console.print(f"[{STYLE_DIM}]Aborted.[/{STYLE_DIM}]")
    except BookmarkNotFoundError as e:
        err_console.print(f"[{STYLE_ERROR}]✗ Not found:[/{STYLE_ERROR}] {e}")
        sys.exit(1)
    except DatabaseError as e:
        err_console.print(f"[{STYLE_ERROR}]✗ Database error:[/{STYLE_ERROR}] {e}")
        sys.exit(1)
    except BookmarkManagerError as e:
        err_console.print(f"[{STYLE_ERROR}]✗ Error:[/{STYLE_ERROR}] {e}")
        sys.exit(1)


@cli.command("tags")
@click.option(
    "--limit",
    "-n",
    default=50,
    show_default=True,
    help="Maximum number of tags to show.",
)
@click.pass_context
def list_tags(ctx: click.Context, limit: int) -> None:
    """List all tags with bookmark counts."""
    try:
        service = get_service(ctx.obj["db_path"])
        tag_counts = service.list_tags(limit=limit)

        if not tag_counts:
            console.print(f"[{STYLE_DIM}]No tags found.[/{STYLE_DIM}]")
            return

        table = Table(box=box.SIMPLE, show_header=True, header_style="bold")
        table.add_column("Tag", style=STYLE_TAG)
        table.add_column("Count", justify="right")

        for tc in tag_counts:
            table.add_row(tc.tag, str(tc.count))

        console.print(table)
    except DatabaseError as e:
        err_console.print(f"[{STYLE_ERROR}]✗ Database error:[/{STYLE_ERROR}] {e}")
        sys.exit(1)
    except BookmarkManagerError as e:
        err_console.print(f"[{STYLE_ERROR}]✗ Error:[/{STYLE_ERROR}] {e}")
        sys.exit(1)


@cli.command("export")
@click.argument("filepath")
@click.pass_context
def export_bookmarks(ctx: click.Context, filepath: str) -> None:
    """Export all bookmarks to a Netscape HTML file."""
    try:
        service = get_service(ctx.obj["db_path"])
        count = service.export_bookmarks(Path(filepath))
        console.print(
            f"[{STYLE_SUCCESS}]✓ Exported {count} bookmark(s)[/{STYLE_SUCCESS}] to {filepath}"
        )
    except BookmarkExportError as e:
        err_console.print(f"[{STYLE_ERROR}]✗ Export failed:[/{STYLE_ERROR}] {e}")
        sys.exit(1)
    except DatabaseError as e:
        err_console.print(f"[{STYLE_ERROR}]✗ Database error:[/{STYLE_ERROR}] {e}")
        sys.exit(1)
    except BookmarkManagerError as e:
        err_console.print(f"[{STYLE_ERROR}]✗ Error:[/{STYLE_ERROR}] {e}")
        sys.exit(1)


@cli.command("import")
@click.argument("filepath")
@click.option(
    "--skip-duplicates",
    is_flag=True,
    default=True,
    show_default=True,
    help="Skip duplicate URLs instead of failing.",
)
@click.pass_context
def import_bookmarks(ctx: click.Context, filepath: str, skip_duplicates: bool) -> None:
    """Import bookmarks from a Netscape HTML file."""
    try:
        service = get_service(ctx.obj["db_path"])
        result = service.import_bookmarks(Path(filepath), skip_duplicates=skip_duplicates)
        console.print(
            f"[{STYLE_SUCCESS}]✓ Import complete:[/{STYLE_SUCCESS}] "
            f"{result.imported} imported, "
            f"[{STYLE_WARNING}]{result.skipped} skipped[/{STYLE_WARNING}], "
            f"[{STYLE_ERROR}]{result.failed} failed[/{STYLE_ERROR}]."
        )
        if result.errors:
            for err in result.errors[:5]:
                err_console.print(f"  [{STYLE_DIM}]↳ {err}[/{STYLE_DIM}]")
            if len(result.errors) > 5:
                err_console.print(
                    f"  [{STYLE_DIM}]... and {len(result.errors) - 5} more errors.[/{STYLE_DIM}]"
                )
    except BookmarkImportError as e:
        err_console.print(f"[{STYLE_ERROR}]✗ Import failed:[/{STYLE_ERROR}] {e}")
        sys.exit(1)
    except FileNotFoundError:
        err_console.print(
            f"[{STYLE_ERROR}]✗ File not found:[/{STYLE_ERROR}] '{filepath}'"
        )
        sys.exit(1)
    except DatabaseError as e:
        err_console.print(f"[{STYLE_ERROR}]✗ Database error:[/{STYLE_ERROR}] {e}")
        sys.exit(1)
    except BookmarkManagerError as e:
        err_console.print(f"[{STYLE_ERROR}]✗ Error:[/{STYLE_ERROR}] {e}")
        sys.exit(1)


if __name__ == "__main__":
    cli()
