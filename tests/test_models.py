"""Tests for bookmark_manager/models.py dataclasses."""
from datetime import datetime, timezone

from bookmark_manager.models import Bookmark, Tag, TagCount, ImportResult


class TestBookmark:
    """Tests for the Bookmark dataclass."""

    def test_create_bookmark_with_all_fields(self, sample_bookmark):
        assert sample_bookmark.id == 1
        assert sample_bookmark.url == "https://example.com"
        assert sample_bookmark.title == "Example Site"
        assert sample_bookmark.description == "An example website"
        assert sample_bookmark.tags == ["example", "test"]
        assert isinstance(sample_bookmark.created_at, datetime)
        assert isinstance(sample_bookmark.updated_at, datetime)

    def test_create_bookmark_minimal(self):
        bm = Bookmark(url="https://example.com")
        assert bm.id is None
        assert bm.url == "https://example.com"
        assert bm.title is None
        assert bm.description is None
        assert bm.tags == []
        assert bm.created_at is None
        assert bm.updated_at is None

    def test_bookmark_default_tags_is_empty_list(self):
        bm = Bookmark(url="https://test.com")
        assert bm.tags == []

    def test_bookmark_equality(self):
        now = datetime.now(timezone.utc)
        bm1 = Bookmark(id=1, url="https://a.com", created_at=now, updated_at=now)
        bm2 = Bookmark(id=1, url="https://a.com", created_at=now, updated_at=now)
        assert bm1 == bm2

    def test_bookmark_inequality(self):
        bm1 = Bookmark(url="https://a.com")
        bm2 = Bookmark(url="https://b.com")
        assert bm1 != bm2


class TestTag:
    """Tests for the Tag dataclass."""

    def test_create_tag(self):
        tag = Tag(id=1, name="python")
        assert tag.id == 1
        assert tag.name == "python"

    def test_tag_minimal(self):
        tag = Tag(name="test")
        assert tag.id is None
        assert tag.name == "test"


class TestTagCount:
    """Tests for the TagCount dataclass."""

    def test_create_tag_count(self):
        tc = TagCount(name="python", count=42)
        assert tc.name == "python"
        assert tc.count == 42


class TestImportResult:
    """Tests for the ImportResult dataclass."""

    def test_create_import_result(self):
        result = ImportResult(total=10, imported=8, skipped=1, errors=1)
        assert result.total == 10
        assert result.imported == 8
        assert result.skipped == 1
        assert result.errors == 1

    def test_import_result_defaults(self):
        result = ImportResult()
        assert result.total == 0
        assert result.imported == 0
        assert result.skipped == 0
        assert result.errors == 0
