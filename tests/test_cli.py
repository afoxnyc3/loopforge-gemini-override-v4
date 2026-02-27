"""Tests for bookmark_manager/cli.py Click commands."""
import pytest
from click.testing import CliRunner

from bookmark_manager.cli import cli


@pytest.fixture
def runner(tmp_db_path, monkeypatch):
    """Create a CliRunner with a temp database path."""
    monkeypatch.setenv("BOOKMARK_DB_PATH", tmp_db_path)
    return CliRunner()


class TestCLIAdd:
    """Tests for the 'add' command."""

    def test_add_bookmark(self, runner):
        result = runner.invoke(cli, ["add", "https://example.com", "--title", "Example"])
        assert result.exit_code == 0
        assert "example.com" in result.output.lower() or "added" in result.output.lower()

    def test_add_bookmark_with_tags(self, runner):
        result = runner.invoke(
            cli, ["add", "https://example.com", "--title", "Example", "--tags", "python,web"]
        )
        assert result.exit_code == 0

    def test_add_duplicate_shows_error(self, runner):
        runner.invoke(cli, ["add", "https://dup.com", "--title", "First"])
        result = runner.invoke(cli, ["add", "https://dup.com", "--title", "Second"])
        # Should indicate duplicate/error
        assert result.exit_code != 0 or "already" in result.output.lower() or "duplicate" in result.output.lower() or "error" in result.output.lower()

    def test_add_invalid_url_shows_error(self, runner):
        result = runner.invoke(cli, ["add", "", "--title", "Empty"])
        assert result.exit_code != 0 or "error" in result.output.lower() or "invalid" in result.output.lower()


class TestCLIList:
    """Tests for the 'list' command."""

    def test_list_empty(self, runner):
        result = runner.invoke(cli, ["list"])
        assert result.exit_code == 0

    def test_list_with_bookmarks(self, runner):
        runner.invoke(cli, ["add", "https://example.com", "--title", "Example"])
        result = runner.invoke(cli, ["list"])
        assert result.exit_code == 0
        assert "example.com" in result.output.lower()

    def test_list_with_limit(self, runner):
        runner.invoke(cli, ["add", "https://a.com", "--title", "A"])
        runner.invoke(cli, ["add", "https://b.com", "--title", "B"])
        runner.invoke(cli, ["add", "https://c.com", "--title", "C"])
        result = runner.invoke(cli, ["list", "--limit", "2"])
        assert result.exit_code == 0

    def test_list_with_tag_filter(self, runner):
        runner.invoke(cli, ["add", "https://py.com", "--title", "Python", "--tags", "python"])
        runner.invoke(cli, ["add", "https://js.com", "--title", "JS", "--tags", "javascript"])
        result = runner.invoke(cli, ["list", "--tag", "python"])
        assert result.exit_code == 0


class TestCLISearch:
    """Tests for the 'search' command."""

    def test_search_by_tag(self, runner):
        runner.invoke(cli, ["add", "https://py.com", "--title", "Python", "--tags", "python"])
        result = runner.invoke(cli, ["search", "python"])
        assert result.exit_code == 0

    def test_search_no_results(self, runner):
        result = runner.invoke(cli, ["search", "nonexistent"])
        assert result.exit_code == 0


class TestCLIDelete:
    """Tests for the 'delete' command."""

    def test_delete_bookmark(self, runner):
        runner.invoke(cli, ["add", "https://delete.com", "--title", "Delete"])
        # Get the ID from list output
        list_result = runner.invoke(cli, ["list"])
        # Try deleting with ID 1 (first bookmark)
        result = runner.invoke(cli, ["delete", "1"], input="y\n")
        assert result.exit_code == 0

    def test_delete_nonexistent(self, runner):
        result = runner.invoke(cli, ["delete", "99999"], input="y\n")
        assert result.exit_code != 0 or "not found" in result.output.lower() or "error" in result.output.lower()


class TestCLITags:
    """Tests for the 'tags' command."""

    def test_tags_empty(self, runner):
        result = runner.invoke(cli, ["tags"])
        assert result.exit_code == 0

    def test_tags_with_data(self, runner):
        runner.invoke(cli, ["add", "https://a.com", "--title", "A", "--tags", "alpha,beta"])
        result = runner.invoke(cli, ["tags"])
        assert result.exit_code == 0
        assert "alpha" in result.output.lower() or "beta" in result.output.lower()


class TestCLIExport:
    """Tests for the 'export' command."""

    def test_export_empty_db(self, runner, tmp_path):
        outfile = str(tmp_path / "export.html")
        result = runner.invoke(cli, ["export", outfile])
        assert result.exit_code == 0

    def test_export_with_bookmarks(self, runner, tmp_path):
        runner.invoke(cli, ["add", "https://example.com", "--title", "Example", "--tags", "test"])
        outfile = str(tmp_path / "export.html")
        result = runner.invoke(cli, ["export", outfile])
        assert result.exit_code == 0
        with open(outfile, "r", encoding="utf-8") as f:
            content = f.read()
        assert "example.com" in content.lower()


class TestCLIImport:
    """Tests for the 'import' command."""

    def test_import_html_file(self, runner, html_file):
        result = runner.invoke(cli, ["import", html_file])
        assert result.exit_code == 0
        # Verify bookmarks were imported
        list_result = runner.invoke(cli, ["list"])
        assert "python.org" in list_result.output.lower() or "github.com" in list_result.output.lower()

    def test_import_nonexistent_file(self, runner):
        result = runner.invoke(cli, ["import", "/nonexistent/path.html"])
        assert result.exit_code != 0 or "error" in result.output.lower() or "not found" in result.output.lower()
