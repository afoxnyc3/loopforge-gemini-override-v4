"""Tests for bookmark_manager/models.py."""

from datetime import datetime

import pytest

from bookmark_manager.models import Bookmark, ImportResult, Tag, TagCount


class TestBookmark:
    def test_bookmark_creation_minimal(self):
        b = Bookmark(id=None, url="https://example.com", title="", description="", tags=[], created_at=None, updated_at=None)
        assert b.url == "https://example.com"
        assert b.tags == []
        assert b.id is None

    def test_bookmark_creation_full(self):
        now = datetime.utcnow()
        b = Bookmark(
            id=1,
            url="https://example.com",
            title="Example",
            description="A description",
            tags=["foo", "bar"],
            created_at=now,
            updated_at=now,
        )
        assert b.id == 1
        assert b.title == "Example"
        assert b.description == "A description"
        assert b.tags == ["foo", "bar"]
        assert b.created_at == now

    def test_bookmark_tags_are_list(self):
        b = Bookmark(id=1, url="https://x.com", title="X", description="", tags=["a", "b", "c"], created_at=None, updated_at=None)
        assert isinstance(b.tags, list)
        assert len(b.tags) == 3

    def test_bookmark_equality(self):
        now = datetime.utcnow()
        b1 = Bookmark(id=1, url="https://a.com", title="A", description="", tags=[], created_at=now, updated_at=now)
        b2 = Bookmark(id=1, url="https://a.com", title="A", description="", tags=[], created_at=now, updated_at=now)
        assert b1 == b2

    def test_bookmark_inequality(self):
        now = datetime.utcnow()
        b1 = Bookmark(id=1, url="https://a.com", title="A", description="", tags=[], created_at=now, updated_at=now)
        b2 = Bookmark(id=2, url="https://b.com", title="B", description="", tags=[], created_at=now, updated_at=now)
        assert b1 != b2


class TestTag:
    def test_tag_creation(self):
        t = Tag(id=1, name="python")
        assert t.id == 1
        assert t.name == "python"

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
        result = ImportResult()
        assert result.imported == 0
        assert result.skipped == 0
        assert result.errors == 0
        assert result.total == 0

    def test_import_result_with_values(self):
        result = ImportResult(imported=10, skipped=2, errors=1, total=13)
        assert result.imported == 10
        assert result.skipped == 2
        assert result.errors == 1
        assert result.total == 13

    def test_import_result_total_calculation(self):
        """total should equal imported + skipped + errors."""
        result = ImportResult(imported=5, skipped=3, errors=2, total=10)
        assert result.total == result.imported + result.skipped + result.errors
