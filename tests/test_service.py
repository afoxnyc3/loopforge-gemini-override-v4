"""Tests for bookmark_manager/service.py."""
import pytest

from bookmark_manager.service import BookmarkService
from bookmark_manager.exceptions import (
    BookmarkNotFoundError,
    DuplicateBookmarkError,
    InvalidURLError,
)


class TestBookmarkService:
    """Tests for the BookmarkService business logic layer."""

    def test_add_bookmark(self, service):
        bm = service.add_bookmark("https://example.com", title="Example", tags=["test"])
        assert bm is not None
        assert bm.url == "https://example.com"
        assert bm.title == "Example"

    def test_add_bookmark_normalizes_url_scheme(self, service):
        """URLs without a scheme should get https:// prepended."""
        bm = service.add_bookmark("example.com", title="Example")
        assert bm.url.startswith("http")  # should have scheme added

    def test_add_bookmark_normalizes_tags(self, service):
        """Tags should be lowercased and stripped."""
        bm = service.add_bookmark(
            "https://example.com", title="Example", tags=[" Python ", "WEB"]
        )
        for tag in bm.tags:
            assert tag == tag.lower().strip()

    def test_add_duplicate_url_raises(self, service):
        service.add_bookmark("https://dup.com", title="First")
        with pytest.raises(DuplicateBookmarkError):
            service.add_bookmark("https://dup.com", title="Second")

    def test_add_invalid_url_raises(self, service):
        with pytest.raises(InvalidURLError):
            service.add_bookmark("", title="Empty URL")

    def test_list_bookmarks(self, service):
        service.add_bookmark("https://a.com", title="A")
        service.add_bookmark("https://b.com", title="B")
        results = service.list_bookmarks()
        assert len(results) >= 2

    def test_list_bookmarks_with_limit(self, service):
        service.add_bookmark("https://a.com", title="A")
        service.add_bookmark("https://b.com", title="B")
        service.add_bookmark("https://c.com", title="C")
        results = service.list_bookmarks(limit=2)
        assert len(results) == 2

    def test_search_by_tag(self, service):
        service.add_bookmark("https://py.com", title="Python", tags=["python"])
        service.add_bookmark("https://js.com", title="JS", tags=["javascript"])
        results = service.search_by_tag("python")
        assert len(results) == 1
        assert results[0].url == "https://py.com"

    def test_search_by_tag_empty_results(self, service):
        results = service.search_by_tag("nonexistent")
        assert len(results) == 0

    def test_delete_bookmark(self, service):
        bm = service.add_bookmark("https://delete.com", title="Delete")
        result = service.delete_bookmark(bm.id)
        assert result is True

    def test_delete_nonexistent_raises(self, service):
        with pytest.raises(BookmarkNotFoundError):
            service.delete_bookmark(99999)

    def test_get_bookmark(self, service):
        added = service.add_bookmark("https://get.com", title="Get")
        fetched = service.get_bookmark(added.id)
        assert fetched.url == "https://get.com"

    def test_get_nonexistent_raises(self, service):
        with pytest.raises(BookmarkNotFoundError):
            service.get_bookmark(99999)

    def test_get_all_tags(self, service):
        service.add_bookmark("https://a.com", title="A", tags=["alpha", "beta"])
        tags = service.get_all_tags()
        tag_names = [t.name for t in tags]
        assert "alpha" in tag_names
        assert "beta" in tag_names

    def test_tag_deduplication(self, service):
        """Duplicate tags in input should be deduplicated."""
        bm = service.add_bookmark(
            "https://dedup.com", title="Dedup", tags=["python", "python", "PYTHON"]
        )
        assert len(bm.tags) == len(set(bm.tags))
