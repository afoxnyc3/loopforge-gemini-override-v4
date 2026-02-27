"""Shared test fixtures for the CLI Bookmark Manager test suite."""
import os
import tempfile
from datetime import datetime, timezone

import pytest

from bookmark_manager.database import Database
from bookmark_manager.models import Bookmark
from bookmark_manager.repository import BookmarkRepository
from bookmark_manager.service import BookmarkService


@pytest.fixture
def tmp_db_path(tmp_path):
    """Return a temporary database file path."""
    return str(tmp_path / "test_bookmarks.db")


@pytest.fixture
def database(tmp_db_path):
    """Create a Database instance with a temporary SQLite file."""
    db = Database(tmp_db_path)
    db.initialize()
    yield db
    db.close()


@pytest.fixture
def repository(database):
    """Create a BookmarkRepository backed by the temp database."""
    return BookmarkRepository(database)


@pytest.fixture
def service(tmp_db_path):
    """Create a BookmarkService backed by a temp database."""
    svc = BookmarkService(tmp_db_path)
    yield svc


@pytest.fixture
def sample_bookmark():
    """Return a sample Bookmark dataclass instance."""
    return Bookmark(
        id=1,
        url="https://example.com",
        title="Example Site",
        description="An example website",
        tags=["example", "test"],
        created_at=datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc),
        updated_at=datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc),
    )


@pytest.fixture
def sample_bookmarks():
    """Return a list of sample Bookmark instances for bulk testing."""
    now = datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc)
    return [
        Bookmark(
            id=1,
            url="https://example.com",
            title="Example",
            description="Example site",
            tags=["example", "web"],
            created_at=now,
            updated_at=now,
        ),
        Bookmark(
            id=2,
            url="https://python.org",
            title="Python",
            description="Python language",
            tags=["python", "programming"],
            created_at=now,
            updated_at=now,
        ),
        Bookmark(
            id=3,
            url="https://github.com",
            title="GitHub",
            description="Code hosting",
            tags=["git", "programming", "web"],
            created_at=now,
            updated_at=now,
        ),
    ]


@pytest.fixture
def sample_html_bookmarks():
    """Return a sample Netscape bookmark HTML string."""
    return """<!DOCTYPE NETSCAPE-Bookmark-file-1>
<META HTTP-EQUIV="Content-Type" CONTENT="text/html; charset=UTF-8">
<TITLE>Bookmarks</TITLE>
<H1>Bookmarks</H1>
<DL><p>
    <DT><H3>Programming</H3>
    <DL><p>
        <DT><A HREF="https://python.org" ADD_DATE="1700000000" TAGS="python,programming">Python</A>
        <DD>The Python programming language
        <DT><A HREF="https://github.com" ADD_DATE="1700000001" TAGS="git,code">GitHub</A>
    </DL><p>
    <DT><A HREF="https://example.com" ADD_DATE="1700000002">Example</A>
</DL><p>
"""


@pytest.fixture
def html_file(tmp_path, sample_html_bookmarks):
    """Write sample bookmark HTML to a temp file and return its path."""
    filepath = tmp_path / "bookmarks.html"
    filepath.write_text(sample_html_bookmarks, encoding="utf-8")
    return str(filepath)
