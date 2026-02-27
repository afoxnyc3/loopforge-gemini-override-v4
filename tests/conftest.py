"""Shared pytest fixtures for the CLI Bookmark Manager test suite."""
from __future__ import annotations

import os
import tempfile
from datetime import datetime
from pathlib import Path

import pytest
from click.testing import CliRunner

from bookmark_manager.database import Database
from bookmark_manager.models import Bookmark
from bookmark_manager.repository import BookmarkRepository
from bookmark_manager.service import BookmarkService


@pytest.fixture
def tmp_db_path(tmp_path: Path) -> Path:
    """Return a path to a temporary SQLite database file."""
    return tmp_path / "test_bookmarks.db"


@pytest.fixture
def db(tmp_db_path: Path) -> Database:
    """Create and return an initialised Database instance backed by a temp file."""
    database = Database(str(tmp_db_path))
    database.initialize()
    return database


@pytest.fixture
def repository(db: Database) -> BookmarkRepository:
    """Return a BookmarkRepository wired to the temp database."""
    return BookmarkRepository(db)


@pytest.fixture
def service(repository: BookmarkRepository) -> BookmarkService:
    """Return a BookmarkService wired to the temp repository."""
    return BookmarkService(repository)


@pytest.fixture
def sample_bookmark() -> Bookmark:
    """Return a single sample Bookmark object (not yet persisted)."""
    return Bookmark(
        id=None,
        url="https://example.com",
        title="Example Site",
        description="A sample bookmark for testing",
        tags=["python", "testing"],
        created_at=None,
        updated_at=None,
    )


@pytest.fixture
def sample_bookmarks() -> list[Bookmark]:
    """Return a list of sample Bookmark objects (not yet persisted)."""
    return [
        Bookmark(
            id=None,
            url="https://python.org",
            title="Python",
            description="The Python programming language",
            tags=["python", "programming"],
            created_at=None,
            updated_at=None,
        ),
        Bookmark(
            id=None,
            url="https://pytest.org",
            title="pytest",
            description="Testing framework",
            tags=["python", "testing"],
            created_at=None,
            updated_at=None,
        ),
        Bookmark(
            id=None,
            url="https://github.com",
            title="GitHub",
            description="Code hosting",
            tags=["git", "hosting"],
            created_at=None,
            updated_at=None,
        ),
    ]


@pytest.fixture
def runner() -> CliRunner:
    """Return a Click CliRunner instance."""
    return CliRunner()


@pytest.fixture
def cli_env(tmp_db_path: Path) -> dict[str, str]:
    """Environment variables pointing the CLI at the temp database."""
    return {"BOOKMARK_DB_PATH": str(tmp_db_path)}


@pytest.fixture
def sample_html() -> str:
    """Return a minimal Netscape bookmark HTML string for parser tests."""
    return """<!DOCTYPE NETSCAPE-Bookmark-file-1>
<!-- This is an automatically generated file.
     It will be read and overwritten.
     DO NOT EDIT! -->
<META HTTP-EQUIV="Content-Type" CONTENT="text/html; charset=UTF-8">
<TITLE>Bookmarks</TITLE>
<H1>Bookmarks</H1>
<DL><p>
    <DT><A HREF="https://python.org" ADD_DATE="1609459200" TAGS="python,programming">Python</A>
    <DD>The Python programming language
    <DT><A HREF="https://pytest.org" ADD_DATE="1609459200" TAGS="python,testing">pytest</A>
    <DD>Testing framework
    <DT><A HREF="https://github.com" ADD_DATE="1609459200">GitHub</A>
</DL><p>
"""
