"""Tests for bookmark_manager/database.py."""
from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from bookmark_manager.database import Database


class TestDatabase:
    def test_initialize_creates_file(self, tmp_path: Path):
        db_path = tmp_path / "test.db"
        db = Database(str(db_path))
        db.initialize()
        assert db_path.exists()

    def test_initialize_creates_bookmarks_table(self, tmp_db_path: Path):
        db = Database(str(tmp_db_path))
        db.initialize()
        with db.get_connection() as conn:
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='bookmarks'"
            )
            assert cursor.fetchone() is not None

    def test_initialize_creates_tags_table(self, tmp_db_path: Path):
        db = Database(str(tmp_db_path))
        db.initialize()
        with db.get_connection() as conn:
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='tags'"
            )
            assert cursor.fetchone() is not None

    def test_initialize_creates_bookmark_tags_table(self, tmp_db_path: Path):
        db = Database(str(tmp_db_path))
        db.initialize()
        with db.get_connection() as conn:
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='bookmark_tags'"
            )
            assert cursor.fetchone() is not None

    def test_get_connection_returns_connection(self, db: Database):
        with db.get_connection() as conn:
            assert conn is not None
            assert isinstance(conn, sqlite3.Connection)

    def test_initialize_idempotent(self, tmp_db_path: Path):
        """Calling initialize() twice should not raise."""
        db = Database(str(tmp_db_path))
        db.initialize()
        db.initialize()  # second call should be safe

    def test_connection_row_factory(self, db: Database):
        """Rows should be accessible by column name."""
        with db.get_connection() as conn:
            conn.execute(
                "INSERT INTO bookmarks (url, title) VALUES (?, ?)",
                ("https://example.com", "Example"),
            )
            conn.commit()
            row = conn.execute("SELECT url, title FROM bookmarks").fetchone()
            assert row["url"] == "https://example.com"
            assert row["title"] == "Example"
