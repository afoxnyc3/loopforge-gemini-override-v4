"""Tests for bookmark_manager/database.py."""
import os
import sqlite3

import pytest

from bookmark_manager.database import Database


class TestDatabase:
    """Tests for the Database class."""

    def test_initialize_creates_tables(self, database):
        """Verify that initialize() creates the expected tables."""
        conn = database.connection
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        )
        tables = {row[0] for row in cursor.fetchall()}
        assert "bookmarks" in tables
        assert "tags" in tables
        assert "bookmark_tags" in tables

    def test_initialize_creates_file(self, tmp_db_path):
        """Verify the database file is created on disk."""
        db = Database(tmp_db_path)
        db.initialize()
        assert os.path.exists(tmp_db_path)
        db.close()

    def test_connection_property(self, database):
        """Verify connection property returns a sqlite3 Connection."""
        assert isinstance(database.connection, sqlite3.Connection)

    def test_close(self, tmp_db_path):
        """Verify close() doesn't raise."""
        db = Database(tmp_db_path)
        db.initialize()
        db.close()

    def test_double_initialize_is_idempotent(self, tmp_db_path):
        """Calling initialize() twice should not raise."""
        db = Database(tmp_db_path)
        db.initialize()
        db.initialize()  # should be safe
        conn = db.connection
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='bookmarks'"
        )
        assert cursor.fetchone() is not None
        db.close()

    def test_foreign_keys_enabled(self, database):
        """Verify that foreign key enforcement is enabled."""
        cursor = database.connection.execute("PRAGMA foreign_keys")
        result = cursor.fetchone()
        assert result[0] == 1
