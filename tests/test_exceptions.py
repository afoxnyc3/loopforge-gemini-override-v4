"""Tests for bookmark_manager/exceptions.py."""

import pytest

from bookmark_manager.exceptions import (
    BookmarkError,
    BookmarkNotFoundError,
    DatabaseError,
    DuplicateBookmarkError,
    ImportError as BMImportError,
    InvalidURLError,
    TagError,
)


class TestExceptionHierarchy:
    def test_bookmark_error_is_base_exception(self):
        assert issubclass(BookmarkError, Exception)

    def test_bookmark_not_found_inherits_bookmark_error(self):
        assert issubclass(BookmarkNotFoundError, BookmarkError)

    def test_duplicate_bookmark_inherits_bookmark_error(self):
        assert issubclass(DuplicateBookmarkError, BookmarkError)

    def test_invalid_url_inherits_bookmark_error(self):
        assert issubclass(InvalidURLError, BookmarkError)

    def test_database_error_inherits_bookmark_error(self):
        assert issubclass(DatabaseError, BookmarkError)

    def test_tag_error_inherits_bookmark_error(self):
        assert issubclass(TagError, BookmarkError)

    def test_import_error_inherits_bookmark_error(self):
        assert issubclass(BMImportError, BookmarkError)


class TestExceptionMessages:
    def test_bookmark_not_found_message(self):
        exc = BookmarkNotFoundError(42)
        assert "42" in str(exc)

    def test_duplicate_bookmark_message(self):
        url = "https://example.com"
        exc = DuplicateBookmarkError(url)
        assert url in str(exc)

    def test_invalid_url_message(self):
        url = "not-a-url"
        exc = InvalidURLError(url)
        assert url in str(exc)

    def test_database_error_message(self):
        exc = DatabaseError("connection failed")
        assert "connection failed" in str(exc)

    def test_tag_error_message(self):
        exc = TagError("invalid tag")
        assert "invalid tag" in str(exc)


class TestExceptionRaising:
    def test_raise_bookmark_not_found(self):
        with pytest.raises(BookmarkNotFoundError):
            raise BookmarkNotFoundError(99)

    def test_raise_duplicate_bookmark(self):
        with pytest.raises(DuplicateBookmarkError):
            raise DuplicateBookmarkError("https://dup.com")

    def test_raise_invalid_url(self):
        with pytest.raises(InvalidURLError):
            raise InvalidURLError("bad-url")

    def test_catch_as_bookmark_error(self):
        """All custom exceptions should be catchable as BookmarkError."""
        for exc_class, args in [
            (BookmarkNotFoundError, (1,)),
            (DuplicateBookmarkError, ("https://x.com",)),
            (InvalidURLError, ("bad",)),
            (DatabaseError, ("err",)),
            (TagError, ("err",)),
        ]:
            with pytest.raises(BookmarkError):
                raise exc_class(*args)
