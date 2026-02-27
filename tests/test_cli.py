"""Integration tests for the CLI commands."""

import pytest
from pathlib import Path
from click.testing import CliRunner

from bookmark_manager.cli import cli


def make_args(tmp_db_path: Path, *args):
    """Prepend --db flag to CLI args."""
    return ["--db", str(tmp_db_path)] + list(args)


class TestAddCommand:
    def test_add_basic(self, runner: CliRunner, tmp_db_path: Path):
        result = runner.invoke(cli, make_args(tmp_db_path, "add", "https://example.com"))
        assert result.exit_code == 0
        assert "added" in result.output.lower()

    def test_add_with_title_and_tags(self, runner: CliRunner, tmp_db_path: Path):
        result = runner.invoke(
            cli,
            make_args(tmp_db_path, "add", "https://python.org", "--title", "Python", "--tags", "python,dev"),
        )
        assert result.exit_code == 0
        assert "added" in result.output.lower()

    def test_add_duplicate_fails(self, runner: CliRunner, tmp_db_path: Path):
        runner.invoke(cli, make_args(tmp_db_path, "add", "https://example.com"))
        result = runner.invoke(cli, make_args(tmp_db_path, "add", "https://example.com"))
        assert result.exit_code != 0

    def test_add_invalid_url_fails(self, runner: CliRunner, tmp_db_path: Path):
        result = runner.invoke(cli, make_args(tmp_db_path, "add", "not-a-valid-url-!!!"))
        assert result.exit_code != 0


class TestListCommand:
    def test_list_empty(self, runner: CliRunner, tmp_db_path: Path):
        result = runner.invoke(cli, make_args(tmp_db_path, "list"))
        assert result.exit_code == 0
        assert "no bookmarks" in result.output.lower()

    def test_list_shows_bookmarks(self, runner: CliRunner, tmp_db_path: Path):
        runner.invoke(cli, make_args(tmp_db_path, "add", "https://example.com", "--title", "Ex"))
        result = runner.invoke(cli, make_args(tmp_db_path, "list"))
        assert result.exit_code == 0
        assert "example.com" in result.output

    def test_list_filter_by_tag(self, runner: CliRunner, tmp_db_path: Path):
        runner.invoke(cli, make_args(tmp_db_path, "add", "https://python.org", "--tags", "python"))
        runner.invoke(cli, make_args(tmp_db_path, "add", "https://github.com", "--tags", "git"))
        result = runner.invoke(cli, make_args(tmp_db_path, "list", "--tag", "python"))
        assert result.exit_code == 0
        assert "python.org" in result.output
        assert "github.com" not in result.output


class TestSearchCommand:
    def test_search_finds_match(self, runner: CliRunner, tmp_db_path: Path):
        runner.invoke(cli, make_args(tmp_db_path, "add", "https://python.org", "--title", "Python"))
        result = runner.invoke(cli, make_args(tmp_db_path, "search", "python"))
        assert result.exit_code == 0
        assert "python" in result.output.lower()

    def test_search_no_results(self, runner: CliRunner, tmp_db_path: Path):
        result = runner.invoke(cli, make_args(tmp_db_path, "search", "xyznotfound"))
        assert result.exit_code == 0
        assert "no results" in result.output.lower()


class TestDeleteCommand:
    def test_delete_existing(self, runner: CliRunner, tmp_db_path: Path):
        runner.invoke(cli, make_args(tmp_db_path, "add", "https://example.com"))
        # Get the ID from list
        list_result = runner.invoke(cli, make_args(tmp_db_path, "list"))
        # Delete with --yes to skip confirmation
        result = runner.invoke(cli, make_args(tmp_db_path, "delete", "1", "--yes"))
        assert result.exit_code == 0
        assert "deleted" in result.output.lower()

    def test_delete_nonexistent(self, runner: CliRunner, tmp_db_path: Path):
        result = runner.invoke(cli, make_args(tmp_db_path, "delete", "99999", "--yes"))
        assert result.exit_code != 0


class TestTagsCommand:
    def test_tags_empty(self, runner: CliRunner, tmp_db_path: Path):
        result = runner.invoke(cli, make_args(tmp_db_path, "tags"))
        assert result.exit_code == 0
        assert "no tags" in result.output.lower()

    def test_tags_shows_counts(self, runner: CliRunner, tmp_db_path: Path):
        runner.invoke(cli, make_args(tmp_db_path, "add", "https://a.com", "--tags", "python"))
        runner.invoke(cli, make_args(tmp_db_path, "add", "https://b.com", "--tags", "python,dev"))
        result = runner.invoke(cli, make_args(tmp_db_path, "tags"))
        assert result.exit_code == 0
        assert "python" in result.output


class TestExportImportCommands:
    def test_export_creates_file(self, runner: CliRunner, tmp_db_path: Path, tmp_path: Path):
        runner.invoke(cli, make_args(tmp_db_path, "add", "https://example.com", "--title", "Ex"))
        export_path = str(tmp_path / "exported.html")
        result = runner.invoke(cli, make_args(tmp_db_path, "export", export_path))
        assert result.exit_code == 0
        assert Path(export_path).exists()

    def test_import_from_html(self, runner: CliRunner, tmp_db_path: Path, sample_html_file: Path):
        result = runner.invoke(cli, make_args(tmp_db_path, "import", str(sample_html_file)))
        assert result.exit_code == 0
        assert "imported" in result.output.lower()

    def test_import_missing_file(self, runner: CliRunner, tmp_db_path: Path):
        result = runner.invoke(cli, make_args(tmp_db_path, "import", "/nonexistent/path/file.html"))
        assert result.exit_code != 0
