"""Shared pytest fixtures for the CLI Bookmark Manager test suite."""

import pytest
from pathlib import Path
from datetime import datetime
from click.testing import CliRunner

from bookmark_manager.database import Database
from bookmark_manager.repository import BookmarkRepository
from bookmark_manager.service import BookmarkService
from bookmark_manager.models import Bookmark


@pytest.fixture
def tmp_db_path(tmp_path: Path) -> Path:
    """Return a path to a temporary SQLite database file."""
    return tmp_path / "test_bookmarks.db"


@pytest.fixture
def db(tmp_db_path: Path) -> Database:
    """Create and return an initialized Database instance."""
    database = Database(tmp_db_path)
    database.initialize()
    return database


@pytest.fixture
def repo(db: Database) -> BookmarkRepository:
    """Return a BookmarkRepository backed by the test database."""
    return BookmarkRepository(db)


@pytest.fixture
def service(repo: BookmarkRepository) -> BookmarkService:
    """Return a BookmarkService backed by the test repository."""
    return BookmarkService(repo)


@pytest.fixture
def runner() -> CliRunner:
    """Return a Click CliRunner for CLI integration tests."""
    return CliRunner()


@pytest.fixture
def sample_bookmark() -> Bookmark:
    """Return a sample Bookmark dataclass instance (not persisted)."""
    return Bookmark(
        id=None,
        url="https://example.com",
        title="Example Site",
        description="A sample bookmark for testing.",
        tags=["test", "example"],
        created_at=datetime(2024, 1, 1, 12, 0, 0),
        updated_at=datetime(2024, 1, 1, 12, 0, 0),
    )


@pytest.fixture
def persisted_bookmark(service: BookmarkService) -> Bookmark:
    """Add a bookmark via the service and return the persisted instance."""
    return service.add_bookmark(
        url="https://example.com",
        title="Example Site",
        tags=["test", "example"],
        description="A sample bookmark.",
    )


@pytest.fixture
def sample_html_file(tmp_path: Path) -> Path:
    """Write a minimal Netscape bookmark HTML file and return its path."""
    content = """<!DOCTYPE NETSCAPE-Bookmark-file-1>
<META HTTP-EQUIV="Content-Type" CONTENT="text/html; charset=UTF-8">
<TITLE>Bookmarks</TITLE>
<H1>Bookmarks</H1>
<DL><p>
    <DT><A HREF="https://python.org" ADD_DATE="1700000000" TAGS="python,dev">Python</A>
    <DD>The Python programming language.
    <DT><A HREF="https://github.com" ADD_DATE="1700000001" TAGS="git,dev">GitHub</A>
</DL><p>
"""
    path = tmp_path / "bookmarks.html"
    path.write_text(content, encoding="utf-8")
    return path
