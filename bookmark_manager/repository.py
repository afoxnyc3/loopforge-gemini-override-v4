"""Repository layer — thin data-access wrappers over SQLite.

BookmarkRepository contains all SQL and is the *only* layer that touches
the database.  It returns plain model objects so the service layer stays
decoupled from persistence concerns.
"""

from __future__ import annotations

import logging
import sqlite3
from datetime import datetime
from typing import List, Optional

from bookmark_manager.database import Database
from bookmark_manager.exceptions import (
    BookmarkNotFoundError,
    DatabaseError,
    DuplicateBookmarkError,
    TagNotFoundError,
)
from bookmark_manager.models import Bookmark, Tag, TagCount

logger = logging.getLogger(__name__)


def _parse_dt(value: str) -> datetime:
    """Parse an ISO-8601 datetime string stored in SQLite."""
    # SQLite stores as 'YYYY-MM-DDTHH:MM:SSZ'
    return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")


class BookmarkRepository:
    """Data-access object for bookmarks and tags.

    All public methods use ``Database.connection()`` as a context manager so
    connections are always closed after each operation.
    """

    def __init__(self, db: Database) -> None:
        self._db = db

    # ------------------------------------------------------------------
    # Bookmark CRUD
    # ------------------------------------------------------------------

    def create_bookmark(
        self,
        url: str,
        title: str,
        description: str = "",
    ) -> Bookmark:
        """Insert a new bookmark row and return the created Bookmark.

        Raises:
            DuplicateBookmarkError: If the URL already exists.
            DatabaseError: On unexpected DB errors.
        """
        sql = """
            INSERT INTO bookmarks (url, title, description)
            VALUES (?, ?, ?)
        """
        try:
            with self._db.connection() as conn:
                cur = conn.execute(sql, (url, title, description))
                bookmark_id = cur.lastrowid
            logger.debug("Created bookmark id=%s url=%s", bookmark_id, url)
            return self.get_bookmark_by_id(bookmark_id)  # type: ignore[arg-type]
        except sqlite3.IntegrityError:
            raise DuplicateBookmarkError(url)

    def get_bookmark_by_id(self, bookmark_id: int) -> Bookmark:
        """Fetch a single bookmark by primary key.

        Raises:
            BookmarkNotFoundError: If no bookmark exists with that id.
        """
        sql = "SELECT * FROM bookmarks WHERE id = ?"
        with self._db.connection() as conn:
            row = conn.execute(sql, (bookmark_id,)).fetchone()
        if row is None:
            raise BookmarkNotFoundError(bookmark_id)
        tags = self._get_tag_names_for_bookmark(bookmark_id)
        return self._row_to_bookmark(row, tags)

    def get_bookmark_by_url(self, url: str) -> Optional[Bookmark]:
        """Return a Bookmark for the given URL, or None if not found."""
        sql = "SELECT * FROM bookmarks WHERE url = ?"
        with self._db.connection() as conn:
            row = conn.execute(sql, (url,)).fetchone()
        if row is None:
            return None
        tags = self._get_tag_names_for_bookmark(row["id"])
        return self._row_to_bookmark(row, tags)

    def list_bookmarks(
        self,
        tag: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Bookmark]:
        """Return a paginated list of bookmarks, optionally filtered by tag."""
        if tag:
            sql = """
                SELECT b.*
                  FROM bookmarks b
                  JOIN bookmark_tags bt ON bt.bookmark_id = b.id
                  JOIN tags t           ON t.id = bt.tag_id
                 WHERE t.name = ?
                 ORDER BY b.created_at DESC
                 LIMIT ? OFFSET ?
            """
            params = (tag, limit, offset)
        else:
            sql = """
                SELECT * FROM bookmarks
                 ORDER BY created_at DESC
                 LIMIT ? OFFSET ?
            """
            params = (limit, offset)

        with self._db.connection() as conn:
            rows = conn.execute(sql, params).fetchall()

        bookmarks = []
        for row in rows:
            tags = self._get_tag_names_for_bookmark(row["id"])
            bookmarks.append(self._row_to_bookmark(row, tags))
        return bookmarks

    def update_bookmark(
        self,
        bookmark_id: int,
        title: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Bookmark:
        """Update mutable fields of a bookmark.

        Raises:
            BookmarkNotFoundError: If the bookmark does not exist.
        """
        # Verify existence first
        existing = self.get_bookmark_by_id(bookmark_id)

        new_title = title if title is not None else existing.title
        new_desc = description if description is not None else existing.description

        sql = """
            UPDATE bookmarks
               SET title = ?, description = ?
             WHERE id = ?
        """
        with self._db.connection() as conn:
            conn.execute(sql, (new_title, new_desc, bookmark_id))

        return self.get_bookmark_by_id(bookmark_id)

    def delete_bookmark(self, bookmark_id: int) -> None:
        """Delete a bookmark and its tag associations (cascade handles tags).

        Raises:
            BookmarkNotFoundError: If no bookmark with that id exists.
        """
        # Verify existence
        self.get_bookmark_by_id(bookmark_id)
        sql = "DELETE FROM bookmarks WHERE id = ?"
        with self._db.connection() as conn:
            conn.execute(sql, (bookmark_id,))
        logger.debug("Deleted bookmark id=%s", bookmark_id)

    def search_bookmarks(self, query: str, limit: int = 50) -> List[Bookmark]:
        """Full-text search across URL, title, and description."""
        pattern = f"%{query}%"
        sql = """
            SELECT * FROM bookmarks
             WHERE url LIKE ?
                OR title LIKE ?
                OR description LIKE ?
             ORDER BY created_at DESC
             LIMIT ?
        """
        with self._db.connection() as conn:
            rows = conn.execute(sql, (pattern, pattern, pattern, limit)).fetchall()

        bookmarks = []
        for row in rows:
            tags = self._get_tag_names_for_bookmark(row["id"])
            bookmarks.append(self._row_to_bookmark(row, tags))
        return bookmarks

    # ------------------------------------------------------------------
    # Tag management
    # ------------------------------------------------------------------

    def get_or_create_tag(self, name: str) -> Tag:
        """Return existing tag or create a new one."""
        sql_select = "SELECT * FROM tags WHERE name = ?"
        sql_insert = "INSERT INTO tags (name) VALUES (?)"
        with self._db.connection() as conn:
            row = conn.execute(sql_select, (name,)).fetchone()
            if row:
                return Tag(id=row["id"], name=row["name"], created_at=_parse_dt(row["created_at"]))
            cur = conn.execute(sql_insert, (name,))
            tag_id = cur.lastrowid
            row = conn.execute(sql_select, (name,)).fetchone()
        return Tag(id=tag_id, name=name)  # type: ignore[arg-type]

    def add_tags_to_bookmark(self, bookmark_id: int, tag_names: List[str]) -> None:
        """Associate tags with a bookmark, creating tags that don't exist."""
        for name in tag_names:
            tag = self.get_or_create_tag(name)
            sql = """
                INSERT OR IGNORE INTO bookmark_tags (bookmark_id, tag_id)
                VALUES (?, ?)
            """
            with self._db.connection() as conn:
                conn.execute(sql, (bookmark_id, tag.id))

    def remove_tags_from_bookmark(self, bookmark_id: int, tag_names: List[str]) -> None:
        """Remove specific tag associations from a bookmark."""
        for name in tag_names:
            sql = """
                DELETE FROM bookmark_tags
                 WHERE bookmark_id = ?
                   AND tag_id = (SELECT id FROM tags WHERE name = ?)
            """
            with self._db.connection() as conn:
                conn.execute(sql, (bookmark_id, name))

    def set_tags_for_bookmark(self, bookmark_id: int, tag_names: List[str]) -> None:
        """Replace all tags for a bookmark with the given list."""
        sql_delete = "DELETE FROM bookmark_tags WHERE bookmark_id = ?"
        with self._db.connection() as conn:
            conn.execute(sql_delete, (bookmark_id,))
        if tag_names:
            self.add_tags_to_bookmark(bookmark_id, tag_names)

    def list_all_tags(self) -> List[TagCount]:
        """Return all tags with their bookmark usage counts, sorted by count desc."""
        sql = """
            SELECT t.name, COUNT(bt.bookmark_id) AS count
              FROM tags t
              LEFT JOIN bookmark_tags bt ON bt.tag_id = t.id
             GROUP BY t.id, t.name
             ORDER BY count DESC, t.name ASC
        """
        with self._db.connection() as conn:
            rows = conn.execute(sql).fetchall()
        return [TagCount(name=row["name"], count=row["count"]) for row in rows]

    def delete_tag(self, name: str) -> None:
        """Delete a tag and all its bookmark associations.

        Raises:
            TagNotFoundError: If the tag does not exist.
        """
        sql_find = "SELECT id FROM tags WHERE name = ?"
        with self._db.connection() as conn:
            row = conn.execute(sql_find, (name,)).fetchone()
            if row is None:
                raise TagNotFoundError(name)
            conn.execute("DELETE FROM tags WHERE id = ?", (row["id"],))

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _get_tag_names_for_bookmark(self, bookmark_id: int) -> List[str]:
        """Return sorted list of tag names for a bookmark."""
        sql = """
            SELECT t.name
              FROM tags t
              JOIN bookmark_tags bt ON bt.tag_id = t.id
             WHERE bt.bookmark_id = ?
             ORDER BY t.name ASC
        """
        with self._db.connection() as conn:
            rows = conn.execute(sql, (bookmark_id,)).fetchall()
        return [row["name"] for row in rows]

    @staticmethod
    def _row_to_bookmark(row: sqlite3.Row, tags: List[str]) -> Bookmark:
        """Convert a sqlite3.Row to a Bookmark dataclass."""
        return Bookmark(
            id=row["id"],
            url=row["url"],
            title=row["title"],
            description=row["description"],
            created_at=_parse_dt(row["created_at"]),
            updated_at=_parse_dt(row["updated_at"]),
            tags=tags,
        )
