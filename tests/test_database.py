"""Tests for bookmark_manager/database.py."""

import sqlite3
from pathlib import Path

import pytest

from bookmark_manager.database import Database


class TestDatabaseInitialization:
    def test_creates_database_file(self, tmp_db_path: str):
        db = Database(tmp_db_path)
        db.initialize()
        assert Path(tmp_db_path).exists()
        db.close()

    def test_creates_bookmarks_table(self, db: Database):
        with db.get_connection() as conn:
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='bookmarks'"
            )
            assert cursor.fetchone() is not None

    def test_creates_tags_table(self, db: Database):
        with db.get_connection() as conn:
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='tags'"
            )
            assert cursor.fetchone() is not None

    def test_creates_bookmark_tags_table(self, db: Database):
        with db.get_connection() as conn:
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='bookmark_tags'"
            )
            assert cursor.fetchone() is not None

    def test_initialize_is_idempotent(self, tmp_db_path: str):
        """Calling initialize twice should not raise an error."""
        db = Database(tmp_db_path)
        db.initialize()
        db.initialize()  # second call should be safe
        db.close()

    def test_in_memory_database(self):
        """Database should work with :memory: path."""
        db = Database(":memory:")
        db.initialize()
        with db.get_connection() as conn:
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
            tables = {row[0] for row in cursor.fetchall()}
        assert "bookmarks" in tables
        assert "tags" in tables
        db.close()


class TestDatabaseConnection:
    def test_get_connection_returns_connection(self, db: Database):
        with db.get_connection() as conn:
            assert conn is not None

    def test_connection_is_sqlite3(self, db: Database):
        with db.get_connection() as conn:
            assert isinstance(conn, sqlite3.Connection)

    def test_foreign_keys_enabled(self, db: Database):
        with db.get_connection() as conn:
            cursor = conn.execute("PRAGMA foreign_keys")
            row = cursor.fetchone()
            assert row[0] == 1

    def test_row_factory_set(self, db: Database):
        with db.get_connection() as conn:
            conn.execute(
                "INSERT INTO bookmarks (url, title, description) VALUES (?, ?, ?)",
                ("https://example.com", "Example", ""),
            )
            cursor = conn.execute("SELECT url, title FROM bookmarks")
            row = cursor.fetchone()
            # Row factory should allow column-name access
            assert row["url"] == "https://example.com"

    def test_close_does_not_raise(self, tmp_db_path: str):
        db = Database(tmp_db_path)
        db.initialize()
        db.close()  # should not raise
