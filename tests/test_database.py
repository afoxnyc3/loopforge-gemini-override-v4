"""Unit tests for bookmark_manager/database.py."""

import sqlite3
from pathlib import Path
import pytest

from bookmark_manager.database import Database


class TestDatabase:
    def test_initialize_creates_file(self, tmp_db_path: Path):
        db = Database(tmp_db_path)
        db.initialize()
        assert tmp_db_path.exists()

    def test_initialize_creates_tables(self, tmp_db_path: Path):
        db = Database(tmp_db_path)
        db.initialize()
        with db.get_connection() as conn:
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
            tables = {row[0] for row in cursor.fetchall()}
        assert "bookmarks" in tables
        assert "tags" in tables
        assert "bookmark_tags" in tables

    def test_get_connection_returns_connection(self, db: Database):
        with db.get_connection() as conn:
            assert isinstance(conn, sqlite3.Connection)

    def test_initialize_idempotent(self, tmp_db_path: Path):
        """Calling initialize twice should not raise."""
        db = Database(tmp_db_path)
        db.initialize()
        db.initialize()  # second call — should be idempotent
        assert tmp_db_path.exists()

    def test_db_path_stored(self, tmp_db_path: Path):
        db = Database(tmp_db_path)
        assert db.db_path == tmp_db_path

    def test_creates_parent_directories(self, tmp_path: Path):
        nested_path = tmp_path / "a" / "b" / "c" / "bookmarks.db"
        db = Database(nested_path)
        db.initialize()
        assert nested_path.exists()
