"""Unit tests for bookmark_manager/exceptions.py."""

import pytest
from bookmark_manager.exceptions import (
    BookmarkManagerError,
    InvalidURLError,
    DuplicateBookmarkError,
    BookmarkNotFoundError,
    TagNotFoundError,
    InvalidTagError,
    BookmarkImportError,
    BookmarkExportError,
    DatabaseError,
    DatabaseInitError,
)


class TestExceptionHierarchy:
    def test_all_inherit_from_base(self):
        exceptions = [
            InvalidURLError("http://x.com"),
            DuplicateBookmarkError("http://x.com"),
            BookmarkNotFoundError(1),
            TagNotFoundError("python"),
            InvalidTagError("bad tag"),
            BookmarkImportError("file.html"),
            BookmarkExportError("file.html"),
            DatabaseError(),
            DatabaseInitError(),
        ]
        for exc in exceptions:
            assert isinstance(exc, BookmarkManagerError)

    def test_database_init_error_inherits_database_error(self):
        assert isinstance(DatabaseInitError(), DatabaseError)

    def test_can_be_raised_and_caught_as_base(self):
        with pytest.raises(BookmarkManagerError):
            raise InvalidURLError("http://x.com", "bad scheme")


class TestInvalidURLError:
    def test_stores_url_and_reason(self):
        exc = InvalidURLError("http://x.com", "bad scheme")
        assert exc.url == "http://x.com"
        assert exc.reason == "bad scheme"

    def test_str_contains_url(self):
        exc = InvalidURLError("http://x.com")
        assert "http://x.com" in str(exc)


class TestDuplicateBookmarkError:
    def test_stores_url(self):
        exc = DuplicateBookmarkError("https://example.com")
        assert exc.url == "https://example.com"

    def test_str_contains_url(self):
        exc = DuplicateBookmarkError("https://example.com")
        assert "example.com" in str(exc)


class TestBookmarkNotFoundError:
    def test_stores_identifier_int(self):
        exc = BookmarkNotFoundError(42)
        assert exc.identifier == 42

    def test_stores_identifier_str(self):
        exc = BookmarkNotFoundError("https://missing.com")
        assert exc.identifier == "https://missing.com"


class TestDatabaseError:
    def test_default_message(self):
        exc = DatabaseError()
        assert "database" in str(exc).lower()

    def test_custom_operation_and_reason(self):
        exc = DatabaseError(operation="insert", reason="constraint violated")
        assert "insert" in str(exc)
        assert "constraint violated" in str(exc)
