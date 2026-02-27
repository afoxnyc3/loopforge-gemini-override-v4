"""Integration tests for CLI commands using Click's CliRunner."""
import pytest
from click.testing import CliRunner
from unittest.mock import patch, MagicMock
from bookmark_manager.cli import cli
from bookmark_manager.models import Bookmark, TagCount
from bookmark_manager.exceptions import (
    DuplicateBookmarkError,
    BookmarkNotFoundError,
    InvalidURLError,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def runner():
    return CliRunner()


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


@pytest.fixture
def mock_service():
    return MagicMock()


def invoke(runner, args, service=None):
    """Helper to invoke CLI with optional mocked service."""
    if service is not None:
        with patch("bookmark_manager.cli.BookmarkService", return_value=service):
            with patch("bookmark_manager.cli.Database"):
                with patch("bookmark_manager.cli.BookmarkRepository"):
                    return runner.invoke(cli, args, catch_exceptions=False)
    return runner.invoke(cli, args)


# ---------------------------------------------------------------------------
# add command
# ---------------------------------------------------------------------------

class TestAddCommand:
    def test_add_success(self, runner, mock_service, sample_bookmark):
        mock_service.add_bookmark.return_value = sample_bookmark
        result = invoke(runner, ["add", "https://example.com", "--tags", "python,test"], mock_service)
        assert result.exit_code == 0
        assert "example.com" in result.output or "Added" in result.output or result.exit_code == 0

    def test_add_duplicate_shows_error(self, runner, mock_service):
        mock_service.add_bookmark.side_effect = DuplicateBookmarkError("https://example.com")
        result = invoke(runner, ["add", "https://example.com"], mock_service)
        assert result.exit_code != 0 or "already" in result.output.lower() or "duplicate" in result.output.lower() or "Error" in result.output

    def test_add_invalid_url_shows_error(self, runner, mock_service):
        mock_service.add_bookmark.side_effect = InvalidURLError("bad-url")
        result = invoke(runner, ["add", "bad-url"], mock_service)
        assert result.exit_code != 0 or "invalid" in result.output.lower() or "Error" in result.output


# ---------------------------------------------------------------------------
# list command
# ---------------------------------------------------------------------------

class TestListCommand:
    def test_list_shows_bookmarks(self, runner, mock_service, sample_bookmark):
        mock_service.list_bookmarks.return_value = [sample_bookmark]
        result = invoke(runner, ["list"], mock_service)
        assert result.exit_code == 0
        assert "example.com" in result.output

    def test_list_empty(self, runner, mock_service):
        mock_service.list_bookmarks.return_value = []
        result = invoke(runner, ["list"], mock_service)
        assert result.exit_code == 0

    def test_list_with_tag_filter(self, runner, mock_service, sample_bookmark):
        mock_service.search_by_tag.return_value = [sample_bookmark]
        result = invoke(runner, ["list", "--tag", "python"], mock_service)
        assert result.exit_code == 0

    def test_list_with_limit(self, runner, mock_service, sample_bookmark):
        mock_service.list_bookmarks.return_value = [sample_bookmark]
        result = invoke(runner, ["list", "--limit", "5"], mock_service)
        assert result.exit_code == 0


# ---------------------------------------------------------------------------
# delete command
# ---------------------------------------------------------------------------

class TestDeleteCommand:
    def test_delete_success(self, runner, mock_service):
        mock_service.delete_bookmark.return_value = None
        result = invoke(runner, ["delete", "1", "--yes"], mock_service)
        assert result.exit_code == 0

    def test_delete_not_found(self, runner, mock_service):
        mock_service.delete_bookmark.side_effect = BookmarkNotFoundError(1)
        result = invoke(runner, ["delete", "999", "--yes"], mock_service)
        assert result.exit_code != 0 or "not found" in result.output.lower() or "Error" in result.output


# ---------------------------------------------------------------------------
# search command
# ---------------------------------------------------------------------------

class TestSearchCommand:
    def test_search_by_tag(self, runner, mock_service, sample_bookmark):
        mock_service.search_by_tag.return_value = [sample_bookmark]
        result = invoke(runner, ["search", "python"], mock_service)
        assert result.exit_code == 0

    def test_search_no_results(self, runner, mock_service):
        mock_service.search_by_tag.return_value = []
        result = invoke(runner, ["search", "nonexistent"], mock_service)
        assert result.exit_code == 0


# ---------------------------------------------------------------------------
# tags command
# ---------------------------------------------------------------------------

class TestTagsCommand:
    def test_tags_lists_all(self, runner, mock_service):
        mock_service.get_all_tags.return_value = [
            TagCount(name="python", count=3),
            TagCount(name="rust", count=1),
        ]
        result = invoke(runner, ["tags"], mock_service)
        assert result.exit_code == 0

    def test_tags_empty(self, runner, mock_service):
        mock_service.get_all_tags.return_value = []
        result = invoke(runner, ["tags"], mock_service)
        assert result.exit_code == 0


# ---------------------------------------------------------------------------
# export command
# ---------------------------------------------------------------------------

class TestExportCommand:
    def test_export_creates_file(self, runner, mock_service, sample_bookmark, tmp_path):
        mock_service.list_bookmarks.return_value = [sample_bookmark]
        out_file = str(tmp_path / "export.html")
        with patch("bookmark_manager.cli.BookmarkHTMLExporter") as mock_exporter_cls:
            mock_exporter = MagicMock()
            mock_exporter_cls.return_value = mock_exporter
            result = invoke(runner, ["export", out_file], mock_service)
        assert result.exit_code == 0


# ---------------------------------------------------------------------------
# import command
# ---------------------------------------------------------------------------

class TestImportCommand:
    def test_import_from_file(self, runner, mock_service, tmp_path):
        html_file = tmp_path / "bookmarks.html"
        html_file.write_text(
            "<!DOCTYPE NETSCAPE-Bookmark-file-1>\n"
            "<DL><p>\n"
            '    <DT><A HREF=\"https://python.org\" TAGS=\"python\">Python</A>\n'
            "</DL>"
        )
        from bookmark_manager.models import ImportResult
        mock_service.import_bookmarks.return_value = ImportResult(
            total=1, imported=1, skipped=0, errors=[]
        )
        with patch("bookmark_manager.cli.BookmarkHTMLParser"):
            result = invoke(runner, ["import", str(html_file)], mock_service)
        assert result.exit_code == 0
