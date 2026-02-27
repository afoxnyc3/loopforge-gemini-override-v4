"""Formatting helpers for CLI output."""
from __future__ import annotations

from pathlib import Path
from typing import List

import click

from bookmark_manager.models import Bookmark, TagCount, ImportResult


# ---------------------------------------------------------------------------
# Styled output helpers
# ---------------------------------------------------------------------------

def success(msg: str) -> None:
    click.echo(click.style("✓ " + msg, fg="green"))


def error(msg: str) -> None:
    click.echo(click.style("✗ " + msg, fg="red"), err=True)


def info(msg: str) -> None:
    click.echo(click.style(msg, fg="cyan"))


def _truncate(text: str, max_len: int) -> str:
    if len(text) <= max_len:
        return text
    return text[: max_len - 1] + "…"


# ---------------------------------------------------------------------------
# Bookmark table
# ---------------------------------------------------------------------------

def print_bookmark_table(bookmarks: List[Bookmark]) -> None:
    """Print a compact table of bookmarks."""
    col_id = 6
    col_title = 30
    col_url = 50
    col_tags = 25

    header = (
        f"{'ID':<{col_id}} "
        f"{'Title':<{col_title}} "
        f"{'URL':<{col_url}} "
        f"{'Tags':<{col_tags}}"
    )
    separator = "-" * (col_id + col_title + col_url + col_tags + 3)

    click.echo(click.style(header, bold=True))
    click.echo(separator)

    for bm in bookmarks:
        title_str = _truncate(bm.title or "", col_title)
        url_str = _truncate(bm.url, col_url)
        tags_str = _truncate(", ".join(bm.tags) if bm.tags else "", col_tags)
        row = (
            f"{bm.id!s:<{col_id}} "
            f"{title_str:<{col_title}} "
            f"{url_str:<{col_url}} "
            f"{tags_str:<{col_tags}}"
        )
        click.echo(row)


# ---------------------------------------------------------------------------
# Bookmark detail view
# ---------------------------------------------------------------------------

def print_bookmark_detail(bookmark: Bookmark) -> None:
    """Print full details of a single bookmark."""
    click.echo("")
    click.echo(click.style(f"Bookmark #{bookmark.id}", bold=True, fg="yellow"))
    click.echo(f"  {'URL':<14}: {bookmark.url}")
    click.echo(f"  {'Title':<14}: {bookmark.title or '—'}")
    click.echo(f"  {'Description':<14}: {bookmark.description or '—'}")
    click.echo(f"  {'Tags':<14}: {', '.join(bookmark.tags) if bookmark.tags else '—'}")
    click.echo(f"  {'Created':<14}: {bookmark.created_at or '—'}")
    click.echo(f"  {'Updated':<14}: {bookmark.updated_at or '—'}")
    click.echo("")


# ---------------------------------------------------------------------------
# Tag table
# ---------------------------------------------------------------------------

def print_tag_table(tag_counts: List[TagCount]) -> None:
    """Print a table of tags with their bookmark counts."""
    col_tag = 30
    col_count = 10

    header = f"{'Tag':<{col_tag}} {'Count':>{col_count}}"
    separator = "-" * (col_tag + col_count + 1)

    click.echo(click.style(header, bold=True))
    click.echo(separator)

    for tc in tag_counts:
        click.echo(f"{tc.name:<{col_tag}} {tc.count:>{col_count}}")

    click.echo(separator)
    total = sum(tc.count for tc in tag_counts)
    click.echo(f"{'Total bookmarks tagged':<{col_tag}} {total:>{col_count}}")


# ---------------------------------------------------------------------------
# Import result summary
# ---------------------------------------------------------------------------

def print_import_result(result: ImportResult, filepath: Path) -> None:
    """Print a summary of an HTML import operation."""
    click.echo("")
    click.echo(click.style(f"Import complete: {filepath.name}", bold=True))
    click.echo(f"  Parsed   : {result.total_parsed}")
    success(f"  Imported : {result.imported}")
    if result.skipped:
        click.echo(click.style(f"  Skipped  : {result.skipped} (duplicates)", fg="yellow"))
    if result.failed:
        click.echo(click.style(f"  Failed   : {result.failed}", fg="red"))
        if result.errors:
            for err in result.errors[:10]:
                click.echo(click.style(f"    - {err}", fg="red"))
            if len(result.errors) > 10:
                click.echo(click.style(f"    ... and {len(result.errors) - 10} more", fg="red"))
    click.echo("")
