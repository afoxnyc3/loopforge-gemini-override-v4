"""Unit tests for bookmark_manager/service.py."""
import pytest
from unittest.mock import MagicMock, patch
from bookmark_manager.service import BookmarkService
from bookmark_manager.models import Bookmark, ImportResult
from bookmark_manager.exceptions import (
    InvalidURLError,
    DuplicateBookmarkError,
    BookmarkNotFoundError,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_repo():
    return MagicMock()


@pytest.fixture
def service(mock_repo):
    svc = BookmarkService.__new__(BookmarkService)
    svc.repo = mock_repo
    return svc


@pytest.fixture
def sample_bookmark():
    return Bookmark(
        id=1,
        url="https://example.com",
        title="Example",
        description="A test bookmark",
        tags=["python", "test"],
        created_at="2024-01-01T00:00:00",
        updated_at="2024-01-01T00:00:00",
    )


# ---------------------------------------------------------------------------
# URL validation
# ---------------------------------------------------------------------------

class TestURLValidation:
    def test_valid_https_url(self, service):
        result = service._normalize_url("https://example.com")
        assert result == "https://example.com"

    def test_valid_http_url(self, service):
        result = service._normalize_url("http://example.com")
        assert result == "http://example.com"

    def test_adds_https_scheme(self, service):
        result = service._normalize_url("example.com")
        assert result.startswith("https://")

    def test_rejects_empty_url(self, service):
        with pytest.raises(InvalidURLError):
            service._normalize_url("")

    def test_rejects_non_http_scheme(self, service):
        with pytest.raises(InvalidURLError):
            service._normalize_url("ftp://example.com")


# ---------------------------------------------------------------------------
# Tag normalization
# ---------------------------------------------------------------------------

class TestTagNormalization:
    def test_lowercases_tags(self, service):
        result = service._normalize_tags(["Python", "DJANGO"])
        assert result == ["python", "django"]

    def test_strips_whitespace(self, service):
        result = service._normalize_tags(["  python  ", " django"])
        assert "python" in result
        assert "django" in result

    def test_deduplicates_tags(self, service):
        result = service._normalize_tags(["python", "python", "django"])
        assert result.count("python") == 1

    def test_removes_empty_tags(self, service):
        result = service._normalize_tags(["", "  ", "python"])
        assert "" not in result
        assert "python" in result

    def test_returns_sorted_list(self, service):
        result = service._normalize_tags(["zebra", "apple", "mango"])
        assert result == sorted(result)


# ---------------------------------------------------------------------------
# add_bookmark
# ---------------------------------------------------------------------------

class TestAddBookmark:
    def test_add_valid_bookmark(self, service, mock_repo, sample_bookmark):
        mock_repo.get_by_url.return_value = None
        mock_repo.create.return_value = sample_bookmark
        result = service.add_bookmark("https://example.com", tags=["python"])
        assert result.url == "https://example.com"
        mock_repo.create.assert_called_once()

    def test_raises_on_duplicate(self, service, mock_repo, sample_bookmark):
        mock_repo.get_by_url.return_value = sample_bookmark
        with pytest.raises(DuplicateBookmarkError):
            service.add_bookmark("https://example.com")

    def test_raises_on_invalid_url(self, service, mock_repo):
        with pytest.raises(InvalidURLError):
            service.add_bookmark("not-a-url-at-all-!!")


# ---------------------------------------------------------------------------
# delete_bookmark
# ---------------------------------------------------------------------------

class TestDeleteBookmark:
    def test_delete_existing(self, service, mock_repo, sample_bookmark):
        mock_repo.get_by_id.return_value = sample_bookmark
        service.delete_bookmark(1)
        mock_repo.delete.assert_called_once_with(1)

    def test_raises_when_not_found(self, service, mock_repo):
        mock_repo.get_by_id.return_value = None
        with pytest.raises(BookmarkNotFoundError):
            service.delete_bookmark(999)


# ---------------------------------------------------------------------------
# search / list
# ---------------------------------------------------------------------------

class TestSearchAndList:
    def test_list_all(self, service, mock_repo, sample_bookmark):
        mock_repo.list_all.return_value = [sample_bookmark]
        results = service.list_bookmarks()
        assert len(results) == 1

    def test_search_by_tag(self, service, mock_repo, sample_bookmark):
        mock_repo.find_by_tag.return_value = [sample_bookmark]
        results = service.search_by_tag("python")
        assert results[0].url == "https://example.com"
        mock_repo.find_by_tag.assert_called_once_with("python", limit=None)

    def test_search_returns_empty_list(self, service, mock_repo):
        mock_repo.find_by_tag.return_value = []
        results = service.search_by_tag("nonexistent")
        assert results == []
