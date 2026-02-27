"""Unit tests for bookmark_manager/repository.py."""

import pytest
from bookmark_manager.repository import BookmarkRepository
from bookmark_manager.models import Bookmark
from bookmark_manager.exceptions import BookmarkNotFoundError, DuplicateBookmarkError


class TestBookmarkRepository:
    def test_create_bookmark(self, repo: BookmarkRepository):
        bm = repo.create(
            url="https://example.com",
            title="Example",
            tags=["test"],
            description=None,
        )
        assert bm.id is not None
        assert bm.url == "https://example.com"
        assert bm.title == "Example"
        assert "test" in bm.tags

    def test_create_duplicate_raises(self, repo: BookmarkRepository):
        repo.create(url="https://example.com", title=None, tags=[], description=None)
        with pytest.raises(DuplicateBookmarkError):
            repo.create(url="https://example.com", title=None, tags=[], description=None)

    def test_get_by_id(self, repo: BookmarkRepository):
        created = repo.create(url="https://example.com", title="Ex", tags=[], description=None)
        fetched = repo.get_by_id(created.id)
        assert fetched is not None
        assert fetched.id == created.id
        assert fetched.url == "https://example.com"

    def test_get_by_id_not_found(self, repo: BookmarkRepository):
        result = repo.get_by_id(99999)
        assert result is None

    def test_get_by_url(self, repo: BookmarkRepository):
        repo.create(url="https://example.com", title=None, tags=[], description=None)
        bm = repo.get_by_url("https://example.com")
        assert bm is not None
        assert bm.url == "https://example.com"

    def test_list_all(self, repo: BookmarkRepository):
        repo.create(url="https://a.com", title=None, tags=[], description=None)
        repo.create(url="https://b.com", title=None, tags=[], description=None)
        results = repo.list_all(limit=10, offset=0)
        assert len(results) == 2

    def test_list_limit(self, repo: BookmarkRepository):
        for i in range(5):
            repo.create(url=f"https://site{i}.com", title=None, tags=[], description=None)
        results = repo.list_all(limit=3, offset=0)
        assert len(results) == 3

    def test_list_by_tag(self, repo: BookmarkRepository):
        repo.create(url="https://python.org", title=None, tags=["python"], description=None)
        repo.create(url="https://github.com", title=None, tags=["git"], description=None)
        results = repo.list_by_tag("python", limit=10, offset=0)
        assert len(results) == 1
        assert results[0].url == "https://python.org"

    def test_delete_bookmark(self, repo: BookmarkRepository):
        bm = repo.create(url="https://example.com", title=None, tags=[], description=None)
        repo.delete(bm.id)
        assert repo.get_by_id(bm.id) is None

    def test_delete_not_found_raises(self, repo: BookmarkRepository):
        with pytest.raises(BookmarkNotFoundError):
            repo.delete(99999)

    def test_search(self, repo: BookmarkRepository):
        repo.create(url="https://python.org", title="Python", tags=[], description=None)
        repo.create(url="https://github.com", title="GitHub", tags=[], description=None)
        results = repo.search("python", limit=10)
        assert any("python" in bm.url.lower() or (bm.title and "python" in bm.title.lower()) for bm in results)

    def test_list_tags(self, repo: BookmarkRepository):
        repo.create(url="https://a.com", title=None, tags=["python", "dev"], description=None)
        repo.create(url="https://b.com", title=None, tags=["python"], description=None)
        tag_counts = repo.list_tags(limit=10)
        tag_names = [tc.tag for tc in tag_counts]
        assert "python" in tag_names
        python_count = next(tc.count for tc in tag_counts if tc.tag == "python")
        assert python_count == 2
