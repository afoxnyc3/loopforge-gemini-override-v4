"""Unit tests for bookmark_manager/service.py."""

import pytest
from bookmark_manager.service import BookmarkService
from bookmark_manager.exceptions import (
    InvalidURLError,
    DuplicateBookmarkError,
    BookmarkNotFoundError,
)


class TestBookmarkService:
    def test_add_bookmark_valid_url(self, service: BookmarkService):
        bm = service.add_bookmark(url="https://example.com", title="Example")
        assert bm.id is not None
        assert bm.url == "https://example.com"

    def test_add_bookmark_normalizes_scheme(self, service: BookmarkService):
        """URLs without a scheme should get https:// prepended."""
        bm = service.add_bookmark(url="example.com", title=None)
        assert bm.url.startswith("http")

    def test_add_bookmark_invalid_url_raises(self, service: BookmarkService):
        with pytest.raises(InvalidURLError):
            service.add_bookmark(url="not a url at all !!!", title=None)

    def test_add_duplicate_raises(self, service: BookmarkService):
        service.add_bookmark(url="https://example.com")
        with pytest.raises(DuplicateBookmarkError):
            service.add_bookmark(url="https://example.com")

    def test_add_bookmark_normalizes_tags(self, service: BookmarkService):
        bm = service.add_bookmark(url="https://example.com", tags=["  Python ", "DEV", "python"])
        # Tags should be lowercased, stripped, and deduplicated
        assert "python" in bm.tags
        assert "dev" in bm.tags
        assert len(bm.tags) == 2

    def test_delete_bookmark(self, service: BookmarkService, persisted_bookmark):
        service.delete_bookmark(persisted_bookmark.id)
        with pytest.raises(BookmarkNotFoundError):
            service.get_bookmark(persisted_bookmark.id)

    def test_delete_nonexistent_raises(self, service: BookmarkService):
        with pytest.raises(BookmarkNotFoundError):
            service.delete_bookmark(99999)

    def test_list_bookmarks(self, service: BookmarkService):
        service.add_bookmark(url="https://a.com")
        service.add_bookmark(url="https://b.com")
        results = service.list_bookmarks(limit=10)
        assert len(results) >= 2

    def test_get_bookmarks_by_tag(self, service: BookmarkService):
        service.add_bookmark(url="https://python.org", tags=["python"])
        service.add_bookmark(url="https://github.com", tags=["git"])
        results = service.get_bookmarks_by_tag("python")
        assert len(results) == 1
        assert results[0].url == "https://python.org"

    def test_search_bookmarks(self, service: BookmarkService):
        service.add_bookmark(url="https://python.org", title="Python")
        results = service.search_bookmarks("python")
        assert len(results) >= 1

    def test_list_tags(self, service: BookmarkService):
        service.add_bookmark(url="https://a.com", tags=["alpha"])
        service.add_bookmark(url="https://b.com", tags=["alpha", "beta"])
        tags = service.list_tags()
        tag_names = [t.tag for t in tags]
        assert "alpha" in tag_names
        assert "beta" in tag_names
