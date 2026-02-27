"""Service layer — business logic, URL/tag normalization, and orchestration.

BookmarkService is the single entry point for all application operations.
It validates and normalizes inputs before delegating to BookmarkRepository.
"""

from __future__ import annotations

import logging
import re
from typing import List, Optional
from urllib.parse import urlparse, urlunparse

from bookmark_manager.config import (
    ACCEPTED_SCHEMES,
    DEFAULT_LIST_LIMIT,
    DEFAULT_SCHEME,
    MAX_DESCRIPTION_LENGTH,
    MAX_TAGS_PER_BOOKMARK,
    MAX_TAG_LENGTH,
    MAX_TITLE_LENGTH,
)
from bookmark_manager.exceptions import (
    BookmarkNotFoundError,
    DuplicateBookmarkError,
    InvalidURLError,
)
from bookmark_manager.models import Bookmark, ImportResult, TagCount
from bookmark_manager.repository import BookmarkRepository

logger = logging.getLogger(__name__)


class BookmarkService:
    """High-level bookmark operations with validation and normalization.

    Args:
        repository: A ``BookmarkRepository`` instance backed by an initialized
                    ``Database``.
    """

    def __init__(self, repository: BookmarkRepository) -> None:
        self._repo = repository

    # ------------------------------------------------------------------
    # Bookmark operations
    # ------------------------------------------------------------------

    def add_bookmark(
        self,
        url: str,
        title: str = "",
        description: str = "",
        tags: Optional[List[str]] = None,
    ) -> Bookmark:
        """Validate, normalize, and persist a new bookmark.

        Args:
            url: The URL to bookmark (scheme may be omitted — https assumed).
            title: Human-readable title.  Truncated to MAX_TITLE_LENGTH.
            description: Optional description.  Truncated to MAX_DESCRIPTION_LENGTH.
            tags: Optional list of tag strings to associate.

        Returns:
            The newly created Bookmark.

        Raises:
            InvalidURLError: If the URL is malformed or uses a disallowed scheme.
            DuplicateBookmarkError: If the URL already exists.
        """
        normalized_url = self._normalize_url(url)
        clean_title = self._clean_title(title or normalized_url)
        clean_desc = description.strip()[:MAX_DESCRIPTION_LENGTH]
        normalized_tags = self._normalize_tags(tags or [])

        bookmark = self._repo.create_bookmark(
            url=normalized_url,
            title=clean_title,
            description=clean_desc,
        )

        if normalized_tags:
            self._repo.add_tags_to_bookmark(bookmark.id, normalized_tags)
            bookmark = self._repo.get_bookmark_by_id(bookmark.id)

        logger.info("Added bookmark id=%s url=%s", bookmark.id, normalized_url)
        return bookmark

    def get_bookmark(self, bookmark_id: int) -> Bookmark:
        """Retrieve a bookmark by ID.

        Raises:
            BookmarkNotFoundError: If not found.
        """
        return self._repo.get_bookmark_by_id(bookmark_id)

    def list_bookmarks(
        self,
        tag: Optional[str] = None,
        limit: int = DEFAULT_LIST_LIMIT,
        offset: int = 0,
    ) -> List[Bookmark]:
        """List bookmarks, optionally filtered by tag.

        Args:
            tag: If provided, only bookmarks with this tag are returned.
            limit: Maximum results to return.
            offset: Pagination offset.

        Returns:
            List of Bookmark objects ordered by creation date descending.
        """
        clean_tag = self._normalize_single_tag(tag) if tag else None
        return self._repo.list_bookmarks(tag=clean_tag, limit=limit, offset=offset)

    def search_bookmarks(self, query: str, limit: int = DEFAULT_LIST_LIMIT) -> List[Bookmark]:
        """Search bookmarks by URL, title, or description substring.

        Args:
            query: Search string.
            limit: Maximum results.

        Returns:
            Matching Bookmark objects.
        """
        if not query or not query.strip():
            return []
        return self._repo.search_bookmarks(query.strip(), limit=limit)

    def delete_bookmark(self, bookmark_id: int) -> None:
        """Delete a bookmark by ID.

        Raises:
            BookmarkNotFoundError: If not found.
        """
        self._repo.delete_bookmark(bookmark_id)
        logger.info("Deleted bookmark id=%s", bookmark_id)

    def update_bookmark(
        self,
        bookmark_id: int,
        title: Optional[str] = None,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> Bookmark:
        """Update mutable fields of a bookmark.

        Only non-None arguments are updated.  Tags, if provided, *replace*
        the existing tag set entirely.

        Raises:
            BookmarkNotFoundError: If not found.
        """
        clean_title = self._clean_title(title) if title is not None else None
        clean_desc = description.strip()[:MAX_DESCRIPTION_LENGTH] if description is not None else None

        bookmark = self._repo.update_bookmark(
            bookmark_id,
            title=clean_title,
            description=clean_desc,
        )

        if tags is not None:
            normalized_tags = self._normalize_tags(tags)
            self._repo.set_tags_for_bookmark(bookmark_id, normalized_tags)
            bookmark = self._repo.get_bookmark_by_id(bookmark_id)

        return bookmark

    # ------------------------------------------------------------------
    # Tag operations
    # ------------------------------------------------------------------

    def list_tags(self) -> List[TagCount]:
        """Return all tags with their usage counts."""
        return self._repo.list_all_tags()

    # ------------------------------------------------------------------
    # Import helper (called by HTML parser pipeline)
    # ------------------------------------------------------------------

    def import_bookmark(
        self,
        url: str,
        title: str = "",
        description: str = "",
        tags: Optional[List[str]] = None,
        result: Optional[ImportResult] = None,
    ) -> Optional[Bookmark]:
        """Import a single bookmark, recording outcome in ImportResult.

        Duplicate URLs are silently skipped (counted as skipped, not errors).
        Invalid URLs are counted as errors.

        Args:
            url: Raw URL from the import source.
            title: Bookmark title.
            description: Bookmark description.
            tags: Tag list.
            result: ImportResult accumulator.  If None, a new one is created.

        Returns:
            The created Bookmark, or None if skipped/errored.
        """
        if result is None:
            result = ImportResult()

        try:
            bookmark = self.add_bookmark(
                url=url,
                title=title,
                description=description,
                tags=tags,
            )
            result.add_success()
            return bookmark
        except DuplicateBookmarkError:
            logger.debug("Skipping duplicate URL during import: %s", url)
            result.add_skip()
            return None
        except InvalidURLError as exc:
            logger.debug("Skipping invalid URL during import: %s — %s", url, exc)
            result.add_error(f"Invalid URL '{url}': {exc.reason or 'unknown reason'}")
            return None

    # ------------------------------------------------------------------
    # URL normalization & validation
    # ------------------------------------------------------------------

    def _normalize_url(self, raw_url: str) -> str:
        """Normalize and validate a URL.

        Steps:
        1. Strip whitespace.
        2. Add default scheme (https) if missing.
        3. Parse and validate with urlparse.
        4. Remove trailing slash from path if path is exactly '/'.
        5. Reject URLs with disallowed schemes or missing netloc.

        Raises:
            InvalidURLError: On validation failure.
        """
        url = raw_url.strip()
        if not url:
            raise InvalidURLError(raw_url, "URL is empty")

        # Add scheme if missing
        if not re.match(r'^[a-zA-Z][a-zA-Z0-9+\-.]*://', url):
            url = f"{DEFAULT_SCHEME}://{url}"

        try:
            parsed = urlparse(url)
        except ValueError as exc:
            raise InvalidURLError(raw_url, str(exc)) from exc

        if parsed.scheme not in ACCEPTED_SCHEMES:
            raise InvalidURLError(
                raw_url,
                f"Scheme '{parsed.scheme}' is not allowed; use one of {sorted(ACCEPTED_SCHEMES)}",
            )

        if not parsed.netloc:
            raise InvalidURLError(raw_url, "URL has no host")

        # Normalize: strip trailing slash from root path only
        path = parsed.path
        if path == "/":
            path = ""

        normalized = urlunparse((
            parsed.scheme,
            parsed.netloc.lower(),
            path,
            parsed.params,
            parsed.query,
            parsed.fragment,
        ))
        return normalized

    # ------------------------------------------------------------------
    # Tag normalization
    # ------------------------------------------------------------------

    def _normalize_tags(self, tags: List[str]) -> List[str]:
        """Lowercase, strip, deduplicate, and truncate tags.

        Returns a sorted list of unique normalized tag names.
        Silently drops empty strings.
        """
        seen: set[str] = set()
        normalized: List[str] = []
        for raw in tags:
            tag = self._normalize_single_tag(raw)
            if tag and tag not in seen:
                seen.add(tag)
                normalized.append(tag)
            if len(normalized) >= MAX_TAGS_PER_BOOKMARK:
                break
        return sorted(normalized)

    @staticmethod
    def _normalize_single_tag(tag: str) -> str:
        """Normalize a single tag: lowercase, strip whitespace, truncate."""
        return tag.strip().lower()[:MAX_TAG_LENGTH]

    @staticmethod
    def _clean_title(title: str) -> str:
        """Strip and truncate a title."""
        return title.strip()[:MAX_TITLE_LENGTH]
