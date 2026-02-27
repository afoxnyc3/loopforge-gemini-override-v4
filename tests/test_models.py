"""Unit tests for bookmark_manager/models.py."""

from datetime import datetime
import pytest

from bookmark_manager.models import Bookmark, Tag, TagCount, ImportResult


class TestBookmark:
    def test_default_fields(self):
        bm = Bookmark(url="https://example.com")
        assert bm.url == "https://example.com"
        assert bm.id is None
        assert bm.title is None
        assert bm.description is None
        assert bm.tags == []
        assert bm.created_at is None
        assert bm.updated_at is None

    def test_full_construction(self):
        now = datetime.now()
        bm = Bookmark(
            id=1,
            url="https://example.com",
            title="Example",
            description="Desc",
            tags=["a", "b"],
            created_at=now,
            updated_at=now,
        )
        assert bm.id == 1
        assert bm.title == "Example"
        assert bm.description == "Desc"
        assert bm.tags == ["a", "b"]
        assert bm.created_at == now

    def test_tags_default_is_empty_list(self):
        bm = Bookmark(url="https://a.com")
        assert isinstance(bm.tags, list)
        assert len(bm.tags) == 0

    def test_bookmark_equality(self):
        bm1 = Bookmark(id=1, url="https://a.com")
        bm2 = Bookmark(id=1, url="https://a.com")
        assert bm1 == bm2


class TestTag:
    def test_tag_construction(self):
        tag = Tag(name="python")
        assert tag.name == "python"
        assert tag.id is None

    def test_tag_with_id(self):
        tag = Tag(id=5, name="dev")
        assert tag.id == 5
        assert tag.name == "dev"


class TestTagCount:
    def test_tag_count(self):
        tc = TagCount(tag="python", count=10)
        assert tc.tag == "python"
        assert tc.count == 10

    def test_tag_count_zero(self):
        tc = TagCount(tag="unused", count=0)
        assert tc.count == 0


class TestImportResult:
    def test_default_import_result(self):
        result = ImportResult()
        assert result.imported == 0
        assert result.skipped == 0
        assert result.failed == 0
        assert result.errors == []

    def test_import_result_with_values(self):
        result = ImportResult(imported=5, skipped=2, failed=1, errors=["err1"])
        assert result.imported == 5
        assert result.skipped == 2
        assert result.failed == 1
        assert result.errors == ["err1"]

    def test_total_property(self):
        result = ImportResult(imported=3, skipped=1, failed=1)
        # total processed = imported + skipped + failed
        assert result.imported + result.skipped + result.failed == 5
