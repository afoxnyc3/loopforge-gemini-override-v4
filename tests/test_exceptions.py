"""Tests for bookmark_manager/exceptions.py custom exception hierarchy."""
from __future__ import annotations

import pytest

from bookmark_manager.exceptions import (
    BookmarkManagerError,
    BookmarkNotFoundError,
    DuplicateBookmarkError,
    InvalidURLError,
    DatabaseError,
    ImportError as BMImportError,
    ExportError,
)


class TestExceptionHierarchy:
    def test_bookmark_not_found_is_bookmark_manager_error(self):
        assert issubclass(BookmarkNotFoundError, BookmarkManagerError)

    def test_duplicate_bookmark_is_bookmark_manager_error(self):
        assert issubclass(DuplicateBookmarkError, BookmarkManagerError)

    def test_invalid_url_is_bookmark_manager_error(self):
        assert issubclass(InvalidURLError, BookmarkManagerError)

    def test_database_error_is_bookmark_manager_error(self):
        assert issubclass(DatabaseError, BookmarkManagerError)

    def test_import_error_is_bookmark_manager_error(self):
        assert issubclass(BMImportError, BookmarkManagerError)

    def test_export_error_is_bookmark_manager_error(self):
        assert issubclass(ExportError, BookmarkManagerError)

    def test_bookmark_manager_error_is_exception(self):
        assert issubclass(BookmarkManagerError, Exception)


class TestExceptionInstantiation:
    def test_bookmark_not_found_with_id(self):
        exc = BookmarkNotFoundError(bookmark_id=42)
        assert "42" in str(exc)

    def test_duplicate_bookmark_with_url(self):
        exc = DuplicateBookmarkError(url="https://example.com")
        assert "example.com" in str(exc)

    def test_invalid_url_with_url(self):
        exc = InvalidURLError(url="not-a-url")
        assert "not-a-url" in str(exc)

    def test_database_error_with_message(self):
        exc = DatabaseError("connection failed")
        assert "connection failed" in str(exc)

    def test_export_error_with_message(self):
        exc = ExportError("write failed")
        assert "write failed" in str(exc)


class TestExceptionRaising:
    def test_raise_bookmark_not_found(self):
        with pytest.raises(BookmarkNotFoundError):
            raise BookmarkNotFoundError(bookmark_id=1)

    def test_raise_duplicate_bookmark(self):
        with pytest.raises(DuplicateBookmarkError):
            raise DuplicateBookmarkError(url="https://example.com")

    def test_raise_invalid_url(self):
        with pytest.raises(InvalidURLError):
            raise InvalidURLError(url="bad")

    def test_catch_as_base_class(self):
        with pytest.raises(BookmarkManagerError):
            raise BookmarkNotFoundError(bookmark_id=99)
