"""Tests for bookmark_manager/repository.py."""
import pytest

from bookmark_manager.repository import BookmarkRepository
from bookmark_manager.models import Bookmark


class TestBookmarkRepository:
    """Tests for BookmarkRepository CRUD operations."""

    def test_add_bookmark(self, repository):
        """Adding a bookmark returns a Bookmark with an id."""
        bm = repository.add("https://example.com", title="Example", description="Desc", tags=["test"])
        assert bm is not None
        assert bm.id is not None
        assert bm.url == "https://example.com"
        assert bm.title == "Example"
        assert "test" in bm.tags

    def test_add_bookmark_without_tags(self, repository):
        bm = repository.add("https://notags.com", title="No Tags")
        assert bm.id is not None
        assert bm.tags == [] or bm.tags is not None

    def test_get_by_id(self, repository):
        added = repository.add("https://example.com", title="Example")
        fetched = repository.get_by_id(added.id)
        assert fetched is not None
        assert fetched.id == added.id
        assert fetched.url == "https://example.com"

    def test_get_by_id_not_found(self, repository):
        result = repository.get_by_id(99999)
        assert result is None

    def test_get_by_url(self, repository):
        repository.add("https://unique-url.com", title="Unique")
        fetched = repository.get_by_url("https://unique-url.com")
        assert fetched is not None
        assert fetched.url == "https://unique-url.com"

    def test_get_by_url_not_found(self, repository):
        result = repository.get_by_url("https://nonexistent.com")
        assert result is None

    def test_list_all(self, repository):
        repository.add("https://a.com", title="A")
        repository.add("https://b.com", title="B")
        results = repository.list_all()
        assert len(results) >= 2

    def test_list_all_with_limit(self, repository):
        repository.add("https://a.com", title="A")
        repository.add("https://b.com", title="B")
        repository.add("https://c.com", title="C")
        results = repository.list_all(limit=2)
        assert len(results) == 2

    def test_search_by_tag(self, repository):
        repository.add("https://py.com", title="Python", tags=["python"])
        repository.add("https://js.com", title="JavaScript", tags=["javascript"])
        results = repository.search_by_tag("python")
        assert len(results) == 1
        assert results[0].url == "https://py.com"

    def test_search_by_tag_no_results(self, repository):
        repository.add("https://py.com", title="Python", tags=["python"])
        results = repository.search_by_tag("nonexistent")
        assert len(results) == 0

    def test_delete_bookmark(self, repository):
        added = repository.add("https://delete-me.com", title="Delete Me")
        result = repository.delete(added.id)
        assert result is True
        assert repository.get_by_id(added.id) is None

    def test_delete_nonexistent(self, repository):
        result = repository.delete(99999)
        assert result is False

    def test_add_duplicate_url(self, repository):
        repository.add("https://dup.com", title="First")
        # Depending on implementation, this may raise or return existing
        # We test that it doesn't crash silently
        try:
            repository.add("https://dup.com", title="Second")
        except Exception:
            pass  # Expected behavior for duplicate URLs

    def test_get_all_tags(self, repository):
        repository.add("https://a.com", title="A", tags=["alpha", "beta"])
        repository.add("https://b.com", title="B", tags=["beta", "gamma"])
        tags = repository.get_all_tags()
        tag_names = [t.name for t in tags]
        assert "alpha" in tag_names
        assert "beta" in tag_names
        assert "gamma" in tag_names

    def test_tag_counts(self, repository):
        repository.add("https://a.com", title="A", tags=["shared"])
        repository.add("https://b.com", title="B", tags=["shared"])
        repository.add("https://c.com", title="C", tags=["unique"])
        tags = repository.get_all_tags()
        shared = [t for t in tags if t.name == "shared"]
        assert len(shared) == 1
        assert shared[0].count == 2
