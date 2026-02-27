"""Tests for bookmark_manager/service.py business logic."""
from __future__ import annotations

import pytest

from bookmark_manager.exceptions import BookmarkNotFoundError, DuplicateBookmarkError, InvalidURLError
from bookmark_manager.models import Bookmark
from bookmark_manager.service import BookmarkService


class TestServiceAddBookmark:
    def test_add_valid_bookmark(self, service: BookmarkService):
        bm = service.add_bookmark(url="https://example.com", title="Example")
        assert bm.id is not None
        assert bm.url == "https://example.com"

    def test_add_bookmark_normalizes_url_scheme(self, service: BookmarkService):
        """URLs missing scheme should get https:// prepended."""
        bm = service.add_bookmark(url="example.com", title="Example")
        assert bm.url.startswith("http")

    def test_add_bookmark_with_tags(self, service: BookmarkService):
        bm = service.add_bookmark(url="https://example.com", title="Example",
                                   tags=["python", "web"])
        assert "python" in bm.tags
        assert "web" in bm.tags

    def test_add_bookmark_normalizes_tags_lowercase(self, service: BookmarkService):
        bm = service.add_bookmark(url="https://example.com", title="Example",
                                   tags=["Python", "WEB"])
        assert "python" in bm.tags
        assert "web" in bm.tags

    def test_add_bookmark_deduplicates_tags(self, service: BookmarkService):
        bm = service.add_bookmark(url="https://example.com", title="Example",
                                   tags=["python", "python", "Python"])
        assert bm.tags.count("python") == 1

    def test_add_bookmark_strips_tag_whitespace(self, service: BookmarkService):
        bm = service.add_bookmark(url="https://example.com", title="Example",
                                   tags=["  python  ", " web "])
        assert "python" in bm.tags
        assert "web" in bm.tags

    def test_add_duplicate_url_raises(self, service: BookmarkService):
        service.add_bookmark(url="https://example.com", title="Example")
        with pytest.raises(DuplicateBookmarkError):
            service.add_bookmark(url="https://example.com", title="Example 2")

    def test_add_invalid_url_raises(self, service: BookmarkService):
        with pytest.raises(InvalidURLError):
            service.add_bookmark(url="not-a-url-at-all!!!", title="Bad")

    def test_add_bookmark_with_description(self, service: BookmarkService):
        bm = service.add_bookmark(url="https://example.com", title="Example",
                                   description="A test bookmark")
        assert bm.description == "A test bookmark"


class TestServiceGetBookmark:
    def test_get_existing_bookmark(self, service: BookmarkService):
        created = service.add_bookmark(url="https://example.com", title="Example")
        fetched = service.get_bookmark(created.id)
        assert fetched.url == "https://example.com"

    def test_get_nonexistent_raises(self, service: BookmarkService):
        with pytest.raises(BookmarkNotFoundError):
            service.get_bookmark(99999)


class TestServiceDeleteBookmark:
    def test_delete_existing_bookmark(self, service: BookmarkService):
        bm = service.add_bookmark(url="https://example.com", title="Example")
        service.delete_bookmark(bm.id)  # should not raise
        with pytest.raises(BookmarkNotFoundError):
            service.get_bookmark(bm.id)

    def test_delete_nonexistent_raises(self, service: BookmarkService):
        with pytest.raises(BookmarkNotFoundError):
            service.delete_bookmark(99999)


class TestServiceListBookmarks:
    def test_list_all_empty(self, service: BookmarkService):
        results = service.list_bookmarks()
        assert results == []

    def test_list_all_returns_added(self, service: BookmarkService):
        service.add_bookmark(url="https://example.com", title="Example")
        service.add_bookmark(url="https://python.org", title="Python")
        results = service.list_bookmarks()
        assert len(results) == 2

    def test_list_by_tag(self, service: BookmarkService):
        service.add_bookmark(url="https://example.com", title="Example", tags=["python"])
        service.add_bookmark(url="https://other.com", title="Other", tags=["java"])
        results = service.list_bookmarks(tag="python")
        assert len(results) == 1
        assert results[0].url == "https://example.com"

    def test_list_with_limit(self, service: BookmarkService):
        for i in range(5):
            service.add_bookmark(url=f"https://example{i}.com", title=f"Example {i}")
        results = service.list_bookmarks(limit=3)
        assert len(results) == 3


class TestServiceSearchBookmarks:
    def test_search_finds_by_url(self, service: BookmarkService):
        service.add_bookmark(url="https://python.org", title="Python")
        results = service.search_bookmarks("python")
        assert len(results) >= 1

    def test_search_empty_returns_empty(self, service: BookmarkService):
        results = service.search_bookmarks("zzznomatch")
        assert results == []


class TestServiceGetTags:
    def test_get_tags_empty(self, service: BookmarkService):
        tags = service.get_tags()
        assert tags == []

    def test_get_tags_returns_used_tags(self, service: BookmarkService):
        service.add_bookmark(url="https://example.com", title="Example", tags=["python", "web"])
        tags = service.get_tags()
        tag_names = [t.name for t in tags]
        assert "python" in tag_names
        assert "web" in tag_names
