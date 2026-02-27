"""Database connection management and schema initialization.

The Database class wraps sqlite3 connections using context managers to prevent
resource leaks. All connections have WAL journal mode and foreign keys enabled.
"""

from __future__ import annotations

import logging
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Generator, Optional

from bookmark_manager.config import DEFAULT_DB_PATH, SCHEMA_FILE, DB_PATH_ENV_VAR
from bookmark_manager.exceptions import DatabaseError

import os

logger = logging.getLogger(__name__)


class Database:
    """Manages SQLite connections and schema lifecycle.

    Usage::

        db = Database()
        db.initialize()

        with db.connection() as conn:
            conn.execute("SELECT 1")
    """

    def __init__(self, db_path: Optional[Path] = None) -> None:
        """Initialise the Database manager.

        Args:
            db_path: Path to the SQLite file.  Defaults to the value of the
                ``BOOKMARK_MANAGER_DB`` environment variable, or
                ``~/.local/share/bookmark_manager/bookmarks.db``.
        """
        if db_path is not None:
            self._db_path = Path(db_path)
        else:
            env_path = os.environ.get(DB_PATH_ENV_VAR)
            self._db_path = Path(env_path) if env_path else DEFAULT_DB_PATH

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @property
    def path(self) -> Path:
        """Resolved path to the SQLite database file."""
        return self._db_path

    def initialize(self) -> None:
        """Create the database directory and apply the schema (idempotent).

        Raises:
            DatabaseError: If the schema file cannot be read or the schema
                           cannot be applied.
        """
        try:
            self._db_path.parent.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            raise DatabaseError("initialize", f"Cannot create data directory: {exc}") from exc

        schema_sql = self._load_schema()
        try:
            with self.connection() as conn:
                conn.executescript(schema_sql)
            logger.debug("Database initialized at %s", self._db_path)
        except sqlite3.Error as exc:
            raise DatabaseError("initialize", str(exc)) from exc

    @contextmanager
    def connection(self) -> Generator[sqlite3.Connection, None, None]:
        """Yield a sqlite3 connection that is committed on success or rolled
        back on exception, and always closed afterwards.

        Yields:
            sqlite3.Connection with ``row_factory = sqlite3.Row`` set so that
            rows can be accessed by column name.

        Raises:
            DatabaseError: On any sqlite3 error.
        """
        conn: Optional[sqlite3.Connection] = None
        try:
            conn = sqlite3.connect(str(self._db_path))
            conn.row_factory = sqlite3.Row
            # Enforce WAL and FK at connection level (schema PRAGMA runs once
            # at init, but we re-apply per connection for safety).
            conn.execute("PRAGMA journal_mode = WAL")
            conn.execute("PRAGMA foreign_keys = ON")
            yield conn
            conn.commit()
        except sqlite3.IntegrityError:
            if conn:
                conn.rollback()
            raise  # Let callers handle integrity violations (duplicates, FK)
        except sqlite3.Error as exc:
            if conn:
                conn.rollback()
            raise DatabaseError("connection", str(exc)) from exc
        finally:
            if conn:
                conn.close()

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _load_schema(self) -> str:
        """Read the SQL schema file.

        Returns:
            SQL text.

        Raises:
            DatabaseError: If the file cannot be found or read.
        """
        if not SCHEMA_FILE.exists():
            raise DatabaseError(
                "initialize",
                f"Schema file not found: {SCHEMA_FILE}",
            )
        try:
            return SCHEMA_FILE.read_text(encoding="utf-8")
        except OSError as exc:
            raise DatabaseError("initialize", f"Cannot read schema file: {exc}") from exc
