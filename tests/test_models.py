"""Tests for bookmark_manager/models.py dataclasses."""
from __future__ import annotations

from datetime import datetime

import pytest

from bookmark_manager.models import Bookmark, ImportResult, Tag, TagCount


class TestBookmark:
    def test_bookmark_creation_minimal(self):
        bm = Bookmark(id=None, url="https://example.com", title="Example",
                      description=None, tags=[], created_at=None, updated_at=None)
        assert bm.url == "https://example.com"
        assert bm.title == "Example"
        assert bm.tags == []
        assert bm.id is None

    def test_bookmark_creation_full(self):
        now = datetime.utcnow()
        bm = Bookmark(
            id=1,
            url="https://example.com",
            title="Example",
            description="A description",
            tags=["python", "web"],
            created_at=now,
            updated_at=now,
        )
        assert bm.id == 1
        assert bm.description == "A description"
        assert "python" in bm.tags
        assert bm.created_at == now

    def test_bookmark_tags_are_list(self):
        bm = Bookmark(id=None, url="https://example.com", title="T",
                      description=None, tags=["a", "b", "c"],
                      created_at=None, updated_at=None)
        assert isinstance(bm.tags, list)
        assert len(bm.tags) == 3

    def test_bookmark_equality(self):
        bm1 = Bookmark(id=1, url="https://a.com", title="A",
                       description=None, tags=[], created_at=None, updated_at=None)
        bm2 = Bookmark(id=1, url="https://a.com", title="A",
                       description=None, tags=[], created_at=None, updated_at=None)
        assert bm1 == bm2

    def test_bookmark_inequality(self):
        bm1 = Bookmark(id=1, url="https://a.com", title="A",
                       description=None, tags=[], created_at=None, updated_at=None)
        bm2 = Bookmark(id=2, url="https://b.com", title="B",
                       description=None, tags=[], created_at=None, updated_at=None)
        assert bm1 != bm2


class TestTag:
    def test_tag_creation(self):
        tag = Tag(id=1, name="python")
        assert tag.id == 1
        assert tag.name == "python"

    def test_tag_equality(self):
        assert Tag(id=1, name="python") == Tag(id=1, name="python")

    def test_tag_inequality(self):
        assert Tag(id=1, name="python") != Tag(id=2, name="java")


class TestTagCount:
    def test_tag_count_creation(self):
        tc = TagCount(name="python", count=5)
        assert tc.name == "python"
        assert tc.count == 5

    def test_tag_count_zero(self):
        tc = TagCount(name="unused", count=0)
        assert tc.count == 0


class TestImportResult:
    def test_import_result_defaults(self):
        result = ImportResult(imported=0, skipped=0, errors=[])
        assert result.imported == 0
        assert result.skipped == 0
        assert result.errors == []

    def test_import_result_with_data(self):
        result = ImportResult(imported=5, skipped=2, errors=["bad url"])
        assert result.imported == 5
        assert result.skipped == 2
        assert len(result.errors) == 1

    def test_import_result_total(self):
        result = ImportResult(imported=3, skipped=1, errors=[])
        # total processed = imported + skipped
        assert result.imported + result.skipped == 4
