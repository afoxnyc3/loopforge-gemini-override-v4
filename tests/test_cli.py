"""Tests for bookmark_manager CLI commands using Click's CliRunner."""
from __future__ import annotations

from pathlib import Path

import pytest
from click.testing import CliRunner

from bookmark_manager.cli import cli


@pytest.fixture
def runner_with_db(tmp_path: Path):
    """Return a CliRunner and a temp DB path tuple."""
    db_path = str(tmp_path / "cli_test.db")
    runner = CliRunner()
    return runner, db_path


def invoke(runner: CliRunner, db_path: str, args: list):
    """Helper: invoke CLI with the DB path environment variable set."""
    return runner.invoke(cli, args, env={"BOOKMARK_DB_PATH": db_path}, catch_exceptions=False)


class TestCLIAdd:
    def test_add_basic(self, runner_with_db):
        runner, db_path = runner_with_db
        result = invoke(runner, db_path, ["add", "https://example.com"])
        assert result.exit_code == 0

    def test_add_with_title(self, runner_with_db):
        runner, db_path = runner_with_db
        result = invoke(runner, db_path, ["add", "https://example.com", "--title", "Example"])
        assert result.exit_code == 0

    def test_add_with_tags(self, runner_with_db):
        runner, db_path = runner_with_db
        result = invoke(runner, db_path, ["add", "https://example.com", "--tags", "python,web"])
        assert result.exit_code == 0

    def test_add_duplicate_fails(self, runner_with_db):
        runner, db_path = runner_with_db
        invoke(runner, db_path, ["add", "https://example.com"])
        result = runner.invoke(cli, ["add", "https://example.com"],
                               env={"BOOKMARK_DB_PATH": db_path})
        # Should exit non-zero or show an error message
        assert result.exit_code != 0 or "duplicate" in result.output.lower() or "already" in result.output.lower()

    def test_add_with_description(self, runner_with_db):
        runner, db_path = runner_with_db
        result = invoke(runner, db_path, [
            "add", "https://example.com",
            "--description", "A test site"
        ])
        assert result.exit_code == 0


class TestCLIList:
    def test_list_empty(self, runner_with_db):
        runner, db_path = runner_with_db
        result = invoke(runner, db_path, ["list"])
        assert result.exit_code == 0

    def test_list_shows_added_bookmark(self, runner_with_db):
        runner, db_path = runner_with_db
        invoke(runner, db_path, ["add", "https://example.com", "--title", "Example"])
        result = invoke(runner, db_path, ["list"])
        assert result.exit_code == 0
        assert "example.com" in result.output

    def test_list_with_tag_filter(self, runner_with_db):
        runner, db_path = runner_with_db
        invoke(runner, db_path, ["add", "https://python.org", "--tags", "python"])
        invoke(runner, db_path, ["add", "https://java.com", "--tags", "java"])
        result = invoke(runner, db_path, ["list", "--tag", "python"])
        assert result.exit_code == 0
        assert "python.org" in result.output
        assert "java.com" not in result.output

    def test_list_with_limit(self, runner_with_db):
        runner, db_path = runner_with_db
        for i in range(5):
            invoke(runner, db_path, ["add", f"https://example{i}.com"])
        result = invoke(runner, db_path, ["list", "--limit", "2"])
        assert result.exit_code == 0


class TestCLISearch:
    def test_search_finds_bookmark(self, runner_with_db):
        runner, db_path = runner_with_db
        invoke(runner, db_path, ["add", "https://python.org", "--title", "Python"])
        result = invoke(runner, db_path, ["search", "python"])
        assert result.exit_code == 0
        assert "python" in result.output.lower()

    def test_search_no_results(self, runner_with_db):
        runner, db_path = runner_with_db
        result = invoke(runner, db_path, ["search", "zzznomatch"])
        assert result.exit_code == 0


class TestCLIDelete:
    def test_delete_existing(self, runner_with_db):
        runner, db_path = runner_with_db
        invoke(runner, db_path, ["add", "https://example.com"])
        # Get the ID from list output
        list_result = invoke(runner, db_path, ["list"])
        # Delete by ID=1 (first inserted)
        result = invoke(runner, db_path, ["delete", "1"])
        assert result.exit_code == 0

    def test_delete_nonexistent(self, runner_with_db):
        runner, db_path = runner_with_db
        result = runner.invoke(cli, ["delete", "99999"],
                               env={"BOOKMARK_DB_PATH": db_path})
        # Should exit non-zero or show error
        assert result.exit_code != 0 or "not found" in result.output.lower()


class TestCLITags:
    def test_tags_empty(self, runner_with_db):
        runner, db_path = runner_with_db
        result = invoke(runner, db_path, ["tags"])
        assert result.exit_code == 0

    def test_tags_shows_used_tags(self, runner_with_db):
        runner, db_path = runner_with_db
        invoke(runner, db_path, ["add", "https://example.com", "--tags", "python,web"])
        result = invoke(runner, db_path, ["tags"])
        assert result.exit_code == 0
        assert "python" in result.output


class TestCLIImportExport:
    def test_export_creates_file(self, runner_with_db, tmp_path: Path):
        runner, db_path = runner_with_db
        invoke(runner, db_path, ["add", "https://example.com", "--title", "Example"])
        export_path = str(tmp_path / "export.html")
        result = invoke(runner, db_path, ["export", export_path])
        assert result.exit_code == 0
        assert Path(export_path).exists()

    def test_import_from_html(self, runner_with_db, tmp_path: Path, sample_html: str):
        runner, db_path = runner_with_db
        html_path = tmp_path / "bookmarks.html"
        html_path.write_text(sample_html, encoding="utf-8")
        result = invoke(runner, db_path, ["import", str(html_path)])
        assert result.exit_code == 0

    def test_import_then_list(self, runner_with_db, tmp_path: Path, sample_html: str):
        runner, db_path = runner_with_db
        html_path = tmp_path / "bookmarks.html"
        html_path.write_text(sample_html, encoding="utf-8")
        invoke(runner, db_path, ["import", str(html_path)])
        result = invoke(runner, db_path, ["list"])
        assert result.exit_code == 0
        assert "python.org" in result.output
