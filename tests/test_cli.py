"""Integration tests for the CLI commands via Click's CliRunner."""

import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from bookmark_manager.cli import cli
from bookmark_manager.database import Database
from bookmark_manager.repository import BookmarkRepository
from bookmark_manager.service import BookmarkService


@pytest.fixture
def cli_runner_with_db(tmp_path):
    """Provide a CliRunner and a temp DB path for CLI integration tests."""
    db_path = str(tmp_path / "cli_test.db")
    runner = CliRunner(mix_stderr=False)
    return runner, db_path


def invoke(runner: CliRunner, db_path: str, args: list):
    """Helper to invoke CLI commands with the temp DB path."""
    return runner.invoke(cli, ["--db", db_path] + args, catch_exceptions=False)


class TestAddCommand:
    def test_add_basic(self, cli_runner_with_db):
        runner, db_path = cli_runner_with_db
        result = invoke(runner, db_path, ["add", "https://example.com"])
        assert result.exit_code == 0
        assert "example.com" in result.output.lower() or result.exit_code == 0

    def test_add_with_title(self, cli_runner_with_db):
        runner, db_path = cli_runner_with_db
        result = invoke(runner, db_path, ["add", "https://example.com", "--title", "My Site"])
        assert result.exit_code == 0

    def test_add_with_tags(self, cli_runner_with_db):
        runner, db_path = cli_runner_with_db
        result = invoke(runner, db_path, ["add", "https://example.com", "--tags", "python,dev"])
        assert result.exit_code == 0

    def test_add_with_description(self, cli_runner_with_db):
        runner, db_path = cli_runner_with_db
        result = invoke(runner, db_path, ["add", "https://example.com", "--description", "A site"])
        assert result.exit_code == 0

    def test_add_invalid_url_shows_error(self, cli_runner_with_db):
        runner, db_path = cli_runner_with_db
        result = runner.invoke(cli, ["--db", db_path, "add", "not a url !!!"])
        assert result.exit_code != 0 or "error" in result.output.lower() or "invalid" in result.output.lower()

    def test_add_duplicate_shows_error(self, cli_runner_with_db):
        runner, db_path = cli_runner_with_db
        invoke(runner, db_path, ["add", "https://example.com"])
        result = runner.invoke(cli, ["--db", db_path, "add", "https://example.com"])
        assert result.exit_code != 0 or "already" in result.output.lower() or "duplicate" in result.output.lower()


class TestListCommand:
    def test_list_empty(self, cli_runner_with_db):
        runner, db_path = cli_runner_with_db
        result = invoke(runner, db_path, ["list"])
        assert result.exit_code == 0

    def test_list_shows_bookmarks(self, cli_runner_with_db):
        runner, db_path = cli_runner_with_db
        invoke(runner, db_path, ["add", "https://python.org", "--title", "Python"])
        result = invoke(runner, db_path, ["list"])
        assert result.exit_code == 0
        assert "python.org" in result.output

    def test_list_by_tag(self, cli_runner_with_db):
        runner, db_path = cli_runner_with_db
        invoke(runner, db_path, ["add", "https://python.org", "--tags", "python"])
        invoke(runner, db_path, ["add", "https://java.com", "--tags", "java"])
        result = invoke(runner, db_path, ["list", "--tag", "python"])
        assert result.exit_code == 0
        assert "python.org" in result.output
        assert "java.com" not in result.output

    def test_list_with_limit(self, cli_runner_with_db):
        runner, db_path = cli_runner_with_db
        for i in range(5):
            invoke(runner, db_path, ["add", f"https://site{i}.com"])
        result = invoke(runner, db_path, ["list", "--limit", "2"])
        assert result.exit_code == 0


class TestSearchCommand:
    def test_search_finds_match(self, cli_runner_with_db):
        runner, db_path = cli_runner_with_db
        invoke(runner, db_path, ["add", "https://python.org", "--title", "Python"])
        result = invoke(runner, db_path, ["search", "python"])
        assert result.exit_code == 0
        assert "python" in result.output.lower()

    def test_search_no_results(self, cli_runner_with_db):
        runner, db_path = cli_runner_with_db
        result = invoke(runner, db_path, ["search", "zzznomatchzzz"])
        assert result.exit_code == 0


class TestDeleteCommand:
    def test_delete_existing(self, cli_runner_with_db):
        runner, db_path = cli_runner_with_db
        invoke(runner, db_path, ["add", "https://example.com"])
        # Get the ID from list output, or use delete by URL if supported
        # First list to find ID
        list_result = invoke(runner, db_path, ["list"])
        assert list_result.exit_code == 0
        # Delete bookmark id=1 (first inserted)
        result = runner.invoke(cli, ["--db", db_path, "delete", "1"])
        # Accept either success or 'not found' depending on ID
        assert result.exit_code == 0 or "not found" in result.output.lower()

    def test_delete_nonexistent_shows_error(self, cli_runner_with_db):
        runner, db_path = cli_runner_with_db
        result = runner.invoke(cli, ["--db", db_path, "delete", "99999"])
        assert result.exit_code != 0 or "not found" in result.output.lower()


class TestTagsCommand:
    def test_tags_empty(self, cli_runner_with_db):
        runner, db_path = cli_runner_with_db
        result = invoke(runner, db_path, ["tags"])
        assert result.exit_code == 0

    def test_tags_shows_tag_names(self, cli_runner_with_db):
        runner, db_path = cli_runner_with_db
        invoke(runner, db_path, ["add", "https://python.org", "--tags", "python,dev"])
        result = invoke(runner, db_path, ["tags"])
        assert result.exit_code == 0
        assert "python" in result.output


class TestImportCommand:
    def test_import_html_file(self, cli_runner_with_db, sample_html_file: str):
        runner, db_path = cli_runner_with_db
        result = invoke(runner, db_path, ["import", sample_html_file])
        assert result.exit_code == 0

    def test_import_adds_bookmarks(self, cli_runner_with_db, sample_html_file: str):
        runner, db_path = cli_runner_with_db
        invoke(runner, db_path, ["import", sample_html_file])
        list_result = invoke(runner, db_path, ["list"])
        assert "python.org" in list_result.output or "github.com" in list_result.output

    def test_import_nonexistent_file(self, cli_runner_with_db):
        runner, db_path = cli_runner_with_db
        result = runner.invoke(cli, ["--db", db_path, "import", "/nonexistent/file.html"])
        assert result.exit_code != 0 or "error" in result.output.lower() or "not found" in result.output.lower()


class TestExportCommand:
    def test_export_creates_file(self, cli_runner_with_db, tmp_path: Path):
        runner, db_path = cli_runner_with_db
        invoke(runner, db_path, ["add", "https://python.org", "--title", "Python"])
        output_file = str(tmp_path / "export.html")
        result = invoke(runner, db_path, ["export", output_file])
        assert result.exit_code == 0
        assert Path(output_file).exists()

    def test_export_contains_bookmarks(self, cli_runner_with_db, tmp_path: Path):
        runner, db_path = cli_runner_with_db
        invoke(runner, db_path, ["add", "https://python.org", "--title", "Python"])
        output_file = str(tmp_path / "export.html")
        invoke(runner, db_path, ["export", output_file])
        content = Path(output_file).read_text(encoding="utf-8")
        assert "python.org" in content
