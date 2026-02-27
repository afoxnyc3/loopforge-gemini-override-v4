"""Tests for bookmark_manager/repository.py CRUD operations."""
from __future__ import annotations

import pytest

from bookmark_manager.models import Bookmark
from bookmark_manager.repository import BookmarkRepository


class TestBookmarkRepositoryCreate:
    def test_create_returns_bookmark_with_id(self, repository: BookmarkRepository, sample_bookmark: Bookmark):
        saved = repository.create(sample_bookmark)
        assert saved.id is not None
        assert saved.id > 0

    def test_create_persists_url(self, repository: BookmarkRepository, sample_bookmark: Bookmark):
        saved = repository.create(sample_bookmark)
        fetched = repository.get_by_id(saved.id)
        assert fetched is not None
        assert fetched.url == sample_bookmark.url

    def test_create_persists_title(self, repository: BookmarkRepository, sample_bookmark: Bookmark):
        saved = repository.create(sample_bookmark)
        fetched = repository.get_by_id(saved.id)
        assert fetched.title == sample_bookmark.title

    def test_create_persists_tags(self, repository: BookmarkRepository, sample_bookmark: Bookmark):
        saved = repository.create(sample_bookmark)
        fetched = repository.get_by_id(saved.id)
        assert set(fetched.tags) == set(sample_bookmark.tags)

    def test_create_persists_description(self, repository: BookmarkRepository, sample_bookmark: Bookmark):
        saved = repository.create(sample_bookmark)
        fetched = repository.get_by_id(saved.id)
        assert fetched.description == sample_bookmark.description

    def test_create_sets_timestamps(self, repository: BookmarkRepository, sample_bookmark: Bookmark):
        saved = repository.create(sample_bookmark)
        fetched = repository.get_by_id(saved.id)
        assert fetched.created_at is not None
        assert fetched.updated_at is not None


class TestBookmarkRepositoryGetById:
    def test_get_by_id_returns_none_for_missing(self, repository: BookmarkRepository):
        result = repository.get_by_id(99999)
        assert result is None

    def test_get_by_id_returns_correct_bookmark(self, repository: BookmarkRepository, sample_bookmark: Bookmark):
        saved = repository.create(sample_bookmark)
        fetched = repository.get_by_id(saved.id)
        assert fetched.url == sample_bookmark.url


class TestBookmarkRepositoryGetByUrl:
    def test_get_by_url_returns_bookmark(self, repository: BookmarkRepository, sample_bookmark: Bookmark):
        repository.create(sample_bookmark)
        fetched = repository.get_by_url(sample_bookmark.url)
        assert fetched is not None
        assert fetched.url == sample_bookmark.url

    def test_get_by_url_returns_none_for_missing(self, repository: BookmarkRepository):
        result = repository.get_by_url("https://notexist.example.com")
        assert result is None


class TestBookmarkRepositoryList:
    def test_list_all_returns_all(self, repository: BookmarkRepository, sample_bookmarks: list):
        for bm in sample_bookmarks:
            repository.create(bm)
        results = repository.list_all()
        assert len(results) == len(sample_bookmarks)

    def test_list_all_empty(self, repository: BookmarkRepository):
        results = repository.list_all()
        assert results == []

    def test_list_all_with_limit(self, repository: BookmarkRepository, sample_bookmarks: list):
        for bm in sample_bookmarks:
            repository.create(bm)
        results = repository.list_all(limit=2)
        assert len(results) == 2

    def test_list_by_tag(self, repository: BookmarkRepository, sample_bookmarks: list):
        for bm in sample_bookmarks:
            repository.create(bm)
        results = repository.list_by_tag("python")
        # python.org and pytest.org both have the 'python' tag
        assert len(results) >= 2
        for bm in results:
            assert "python" in bm.tags

    def test_list_by_tag_no_results(self, repository: BookmarkRepository, sample_bookmark: Bookmark):
        repository.create(sample_bookmark)
        results = repository.list_by_tag("nonexistenttag")
        assert results == []


class TestBookmarkRepositoryDelete:
    def test_delete_removes_bookmark(self, repository: BookmarkRepository, sample_bookmark: Bookmark):
        saved = repository.create(sample_bookmark)
        repository.delete(saved.id)
        assert repository.get_by_id(saved.id) is None

    def test_delete_nonexistent_does_not_raise(self, repository: BookmarkRepository):
        # Deleting a non-existent ID should not raise an exception
        repository.delete(99999)


class TestBookmarkRepositorySearch:
    def test_search_by_url_fragment(self, repository: BookmarkRepository, sample_bookmarks: list):
        for bm in sample_bookmarks:
            repository.create(bm)
        results = repository.search("python")
        assert len(results) >= 1

    def test_search_returns_empty_for_no_match(self, repository: BookmarkRepository, sample_bookmark: Bookmark):
        repository.create(sample_bookmark)
        results = repository.search("zzznomatch")
        assert results == []


class TestBookmarkRepositoryTags:
    def test_get_all_tags(self, repository: BookmarkRepository, sample_bookmarks: list):
        for bm in sample_bookmarks:
            repository.create(bm)
        tags = repository.get_all_tags()
        tag_names = [t.name for t in tags]
        assert "python" in tag_names

    def test_get_all_tags_empty(self, repository: BookmarkRepository):
        tags = repository.get_all_tags()
        assert tags == []
