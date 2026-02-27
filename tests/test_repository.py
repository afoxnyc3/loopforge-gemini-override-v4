"""Tests for bookmark_manager/repository.py."""

import pytest

from bookmark_manager.exceptions import BookmarkNotFoundError, DuplicateBookmarkError
from bookmark_manager.models import Bookmark, TagCount
from bookmark_manager.repository import BookmarkRepository


class TestBookmarkCreate:
    def test_create_returns_bookmark(self, repo: BookmarkRepository):
        b = repo.create(url="https://example.com", title="Example", description="", tags=[])
        assert isinstance(b, Bookmark)
        assert b.id is not None

    def test_create_stores_url(self, repo: BookmarkRepository):
        b = repo.create(url="https://example.com", title="", description="", tags=[])
        assert b.url == "https://example.com"

    def test_create_stores_title(self, repo: BookmarkRepository):
        b = repo.create(url="https://example.com", title="My Title", description="", tags=[])
        assert b.title == "My Title"

    def test_create_stores_description(self, repo: BookmarkRepository):
        b = repo.create(url="https://example.com", title="", description="My desc", tags=[])
        assert b.description == "My desc"

    def test_create_stores_tags(self, repo: BookmarkRepository):
        b = repo.create(url="https://example.com", title="", description="", tags=["python", "dev"])
        assert set(b.tags) == {"python", "dev"}

    def test_create_duplicate_url_raises(self, repo: BookmarkRepository):
        repo.create(url="https://example.com", title="", description="", tags=[])
        with pytest.raises((DuplicateBookmarkError, Exception)):
            repo.create(url="https://example.com", title="Dup", description="", tags=[])

    def test_create_sets_timestamps(self, repo: BookmarkRepository):
        b = repo.create(url="https://example.com", title="", description="", tags=[])
        assert b.created_at is not None
        assert b.updated_at is not None


class TestBookmarkGetById:
    def test_get_by_id_returns_bookmark(self, persisted_bookmark: Bookmark, repo: BookmarkRepository):
        b = repo.get_by_id(persisted_bookmark.id)
        assert b.id == persisted_bookmark.id

    def test_get_by_id_not_found_raises(self, repo: BookmarkRepository):
        with pytest.raises(BookmarkNotFoundError):
            repo.get_by_id(99999)

    def test_get_by_id_includes_tags(self, persisted_bookmark: Bookmark, repo: BookmarkRepository):
        b = repo.get_by_id(persisted_bookmark.id)
        assert set(b.tags) == {"example", "test"}


class TestBookmarkGetByUrl:
    def test_get_by_url_returns_bookmark(self, persisted_bookmark: Bookmark, repo: BookmarkRepository):
        b = repo.get_by_url("https://example.com")
        assert b is not None
        assert b.url == "https://example.com"

    def test_get_by_url_not_found_returns_none(self, repo: BookmarkRepository):
        result = repo.get_by_url("https://nonexistent.example.com")
        assert result is None


class TestBookmarkList:
    def test_list_returns_all(self, repo: BookmarkRepository):
        repo.create(url="https://a.com", title="A", description="", tags=[])
        repo.create(url="https://b.com", title="B", description="", tags=[])
        results = repo.list_all()
        assert len(results) >= 2

    def test_list_by_tag(self, repo: BookmarkRepository):
        repo.create(url="https://python.org", title="Python", description="", tags=["python"])
        repo.create(url="https://java.com", title="Java", description="", tags=["java"])
        results = repo.list_by_tag("python")
        assert all("python" in b.tags for b in results)
        assert len(results) >= 1

    def test_list_by_tag_no_results(self, repo: BookmarkRepository):
        results = repo.list_by_tag("nonexistent-tag-xyz")
        assert results == []

    def test_list_with_limit(self, repo: BookmarkRepository):
        for i in range(5):
            repo.create(url=f"https://site{i}.com", title=f"Site {i}", description="", tags=[])
        results = repo.list_all(limit=3)
        assert len(results) <= 3


class TestBookmarkSearch:
    def test_search_by_url(self, repo: BookmarkRepository):
        repo.create(url="https://python.org", title="Python", description="", tags=[])
        results = repo.search("python.org")
        assert any("python.org" in b.url for b in results)

    def test_search_by_title(self, repo: BookmarkRepository):
        repo.create(url="https://example.com", title="My Python Guide", description="", tags=[])
        results = repo.search("Python Guide")
        assert any("Python Guide" in b.title for b in results)

    def test_search_no_results(self, repo: BookmarkRepository):
        results = repo.search("zzznomatchzzz")
        assert results == []


class TestBookmarkUpdate:
    def test_update_title(self, persisted_bookmark: Bookmark, repo: BookmarkRepository):
        updated = repo.update(persisted_bookmark.id, title="New Title")
        assert updated.title == "New Title"

    def test_update_tags(self, persisted_bookmark: Bookmark, repo: BookmarkRepository):
        updated = repo.update(persisted_bookmark.id, tags=["newtag"])
        assert "newtag" in updated.tags

    def test_update_nonexistent_raises(self, repo: BookmarkRepository):
        with pytest.raises(BookmarkNotFoundError):
            repo.update(99999, title="Ghost")


class TestBookmarkDelete:
    def test_delete_removes_bookmark(self, persisted_bookmark: Bookmark, repo: BookmarkRepository):
        repo.delete(persisted_bookmark.id)
        with pytest.raises(BookmarkNotFoundError):
            repo.get_by_id(persisted_bookmark.id)

    def test_delete_nonexistent_raises(self, repo: BookmarkRepository):
        with pytest.raises(BookmarkNotFoundError):
            repo.delete(99999)


class TestTagOperations:
    def test_list_tags_returns_tag_counts(self, repo: BookmarkRepository):
        repo.create(url="https://a.com", title="A", description="", tags=["python"])
        repo.create(url="https://b.com", title="B", description="", tags=["python", "dev"])
        tags = repo.list_tags()
        assert isinstance(tags, list)
        names = [t.name for t in tags]
        assert "python" in names

    def test_tag_count_reflects_usage(self, repo: BookmarkRepository):
        repo.create(url="https://a.com", title="A", description="", tags=["shared"])
        repo.create(url="https://b.com", title="B", description="", tags=["shared"])
        tags = repo.list_tags()
        shared = next((t for t in tags if t.name == "shared"), None)
        assert shared is not None
        assert shared.count == 2
