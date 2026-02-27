"""Shared pytest fixtures for the CLI Bookmark Manager test suite."""

import os
import tempfile
from pathlib import Path
from typing import Generator

import pytest
from click.testing import CliRunner

from bookmark_manager.database import Database
from bookmark_manager.models import Bookmark
from bookmark_manager.repository import BookmarkRepository
from bookmark_manager.service import BookmarkService


@pytest.fixture
def tmp_db_path(tmp_path: Path) -> str:
    """Return a path to a temporary SQLite database file."""
    return str(tmp_path / "test_bookmarks.db")


@pytest.fixture
def db(tmp_db_path: str) -> Generator[Database, None, None]:
    """Provide an initialised Database instance backed by a temp file."""
    database = Database(tmp_db_path)
    database.initialize()
    yield database
    database.close()


@pytest.fixture
def repo(db: Database) -> BookmarkRepository:
    """Provide a BookmarkRepository wired to the temp database."""
    return BookmarkRepository(db)


@pytest.fixture
def service(repo: BookmarkRepository) -> BookmarkService:
    """Provide a BookmarkService wired to the temp repository."""
    return BookmarkService(repo)


@pytest.fixture
def runner() -> CliRunner:
    """Provide a Click test runner that mixes stdout/stderr."""
    return CliRunner(mix_stderr=False)


@pytest.fixture
def sample_bookmark() -> Bookmark:
    """Return a detached Bookmark object (no DB id)."""
    return Bookmark(
        id=None,
        url="https://example.com",
        title="Example Domain",
        description="An example bookmark",
        tags=["example", "test"],
        created_at=None,
        updated_at=None,
    )


@pytest.fixture
def persisted_bookmark(repo: BookmarkRepository) -> Bookmark:
    """Insert a bookmark and return the persisted instance."""
    return repo.create(
        url="https://example.com",
        title="Example Domain",
        description="An example bookmark",
        tags=["example", "test"],
    )


@pytest.fixture
def sample_html_file(tmp_path: Path) -> str:
    """Write a minimal Netscape bookmark HTML file and return its path."""
    content = """<!DOCTYPE NETSCAPE-Bookmark-file-1>
<!-- This is an automatically generated file.
     It will be read and overwritten.
     DO NOT EDIT! -->
<META HTTP-EQUIV="Content-Type" CONTENT="text/html; charset=UTF-8">
<TITLE>Bookmarks</TITLE>
<H1>Bookmarks</H1>
<DL><p>
    <DT><A HREF="https://python.org" ADD_DATE="1609459200" TAGS="python,programming">Python</A>
    <DD>The Python programming language
    <DT><A HREF="https://github.com" ADD_DATE="1609459201" TAGS="git,dev">GitHub</A>
    <DT><A HREF="https://docs.python.org" ADD_DATE="1609459202">Python Docs</A>
</DL><p>
"""
    filepath = tmp_path / "bookmarks.html"
    filepath.write_text(content, encoding="utf-8")
    return str(filepath)
