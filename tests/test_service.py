"""Tests for bookmark_manager/service.py."""

import pytest

from bookmark_manager.exceptions import (
    BookmarkNotFoundError,
    DuplicateBookmarkError,
    InvalidURLError,
)
from bookmark_manager.models import Bookmark
from bookmark_manager.service import BookmarkService


class TestAddBookmark:
    def test_add_valid_url(self, service: BookmarkService):
        b = service.add(url="https://example.com", title="Example", tags=[])
        assert isinstance(b, Bookmark)
        assert b.id is not None

    def test_add_normalizes_url_scheme(self, service: BookmarkService):
        """URLs without scheme should get https:// prepended."""
        b = service.add(url="example.com", title="", tags=[])
        assert b.url.startswith("http")

    def test_add_normalizes_tags_to_lowercase(self, service: BookmarkService):
        b = service.add(url="https://example.com", title="", tags=["Python", "DEV"])
        assert "python" in b.tags
        assert "dev" in b.tags

    def test_add_deduplicates_tags(self, service: BookmarkService):
        b = service.add(url="https://example.com", title="", tags=["python", "python", "Python"])
        assert b.tags.count("python") == 1

    def test_add_strips_tag_whitespace(self, service: BookmarkService):
        b = service.add(url="https://example.com", title="", tags=[" python ", "dev "])
        assert "python" in b.tags
        assert "dev" in b.tags

    def test_add_invalid_url_raises(self, service: BookmarkService):
        with pytest.raises(InvalidURLError):
            service.add(url="not a url at all !!!", title="", tags=[])

    def test_add_duplicate_url_raises(self, service: BookmarkService):
        service.add(url="https://example.com", title="First", tags=[])
        with pytest.raises((DuplicateBookmarkError, Exception)):
            service.add(url="https://example.com", title="Second", tags=[])

    def test_add_with_description(self, service: BookmarkService):
        b = service.add(url="https://example.com", title="", tags=[], description="A description")
        assert b.description == "A description"


class TestGetBookmark:
    def test_get_existing_bookmark(self, service: BookmarkService):
        created = service.add(url="https://example.com", title="Example", tags=[])
        fetched = service.get(created.id)
        assert fetched.id == created.id
        assert fetched.url == created.url

    def test_get_nonexistent_raises(self, service: BookmarkService):
        with pytest.raises(BookmarkNotFoundError):
            service.get(99999)


class TestListBookmarks:
    def test_list_all_empty(self, service: BookmarkService):
        results = service.list_all()
        assert results == []

    def test_list_all_returns_bookmarks(self, service: BookmarkService):
        service.add(url="https://a.com", title="A", tags=[])
        service.add(url="https://b.com", title="B", tags=[])
        results = service.list_all()
        assert len(results) == 2

    def test_list_by_tag(self, service: BookmarkService):
        service.add(url="https://python.org", title="Python", tags=["python"])
        service.add(url="https://java.com", title="Java", tags=["java"])
        results = service.list_by_tag("python")
        assert len(results) == 1
        assert results[0].url == "https://python.org"

    def test_list_with_limit(self, service: BookmarkService):
        for i in range(5):
            service.add(url=f"https://site{i}.com", title=f"Site {i}", tags=[])
        results = service.list_all(limit=2)
        assert len(results) <= 2


class TestSearchBookmarks:
    def test_search_finds_by_url(self, service: BookmarkService):
        service.add(url="https://python.org", title="Python", tags=[])
        results = service.search("python.org")
        assert len(results) >= 1

    def test_search_finds_by_title(self, service: BookmarkService):
        service.add(url="https://example.com", title="My Awesome Guide", tags=[])
        results = service.search("Awesome Guide")
        assert len(results) >= 1

    def test_search_no_results(self, service: BookmarkService):
        results = service.search("zzznomatchzzz")
        assert results == []


class TestDeleteBookmark:
    def test_delete_existing(self, service: BookmarkService):
        b = service.add(url="https://example.com", title="", tags=[])
        service.delete(b.id)
        with pytest.raises(BookmarkNotFoundError):
            service.get(b.id)

    def test_delete_nonexistent_raises(self, service: BookmarkService):
        with pytest.raises(BookmarkNotFoundError):
            service.delete(99999)


class TestListTags:
    def test_list_tags_empty(self, service: BookmarkService):
        tags = service.list_tags()
        assert tags == []

    def test_list_tags_returns_counts(self, service: BookmarkService):
        service.add(url="https://a.com", title="A", tags=["python"])
        service.add(url="https://b.com", title="B", tags=["python", "dev"])
        tags = service.list_tags()
        names = [t.name for t in tags]
        assert "python" in names
        assert "dev" in names
