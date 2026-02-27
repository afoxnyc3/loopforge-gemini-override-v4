"""Tests for bookmark_manager/exceptions.py."""
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


class TestExceptions:
    """Verify exception hierarchy and instantiation."""

    def test_base_exception(self):
        exc = BookmarkManagerError("base error")
        assert str(exc) == "base error"
        assert isinstance(exc, Exception)

    def test_bookmark_not_found_error(self):
        exc = BookmarkNotFoundError("not found")
        assert isinstance(exc, BookmarkManagerError)
        assert str(exc) == "not found"

    def test_duplicate_bookmark_error(self):
        exc = DuplicateBookmarkError("duplicate")
        assert isinstance(exc, BookmarkManagerError)

    def test_invalid_url_error(self):
        exc = InvalidURLError("bad url")
        assert isinstance(exc, BookmarkManagerError)

    def test_database_error(self):
        exc = DatabaseError("db error")
        assert isinstance(exc, BookmarkManagerError)

    def test_export_error(self):
        exc = ExportError("export failed")
        assert isinstance(exc, BookmarkManagerError)

    def test_exceptions_are_catchable_as_base(self):
        """All custom exceptions should be catchable via BookmarkManagerError."""
        exceptions = [
            BookmarkNotFoundError("test"),
            DuplicateBookmarkError("test"),
            InvalidURLError("test"),
            DatabaseError("test"),
            ExportError("test"),
        ]
        for exc in exceptions:
            with pytest.raises(BookmarkManagerError):
                raise exc
