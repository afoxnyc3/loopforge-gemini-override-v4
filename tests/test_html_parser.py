"""Tests for bookmark_manager/html_parser.py import/export."""
from __future__ import annotations

from pathlib import Path

import pytest

from bookmark_manager.html_parser import BookmarkHTMLParser
from bookmark_manager.models import Bookmark


@pytest.fixture
def parser() -> BookmarkHTMLParser:
    return BookmarkHTMLParser()


@pytest.fixture
def html_file(tmp_path: Path, sample_html: str) -> Path:
    path = tmp_path / "bookmarks.html"
    path.write_text(sample_html, encoding="utf-8")
    return path


class TestHTMLParserImport:
    def test_parse_returns_list(self, parser: BookmarkHTMLParser, html_file: Path):
        bookmarks = parser.parse(str(html_file))
        assert isinstance(bookmarks, list)

    def test_parse_correct_count(self, parser: BookmarkHTMLParser, html_file: Path):
        bookmarks = parser.parse(str(html_file))
        assert len(bookmarks) == 3

    def test_parse_extracts_urls(self, parser: BookmarkHTMLParser, html_file: Path):
        bookmarks = parser.parse(str(html_file))
        urls = [bm.url for bm in bookmarks]
        assert "https://python.org" in urls
        assert "https://pytest.org" in urls
        assert "https://github.com" in urls

    def test_parse_extracts_titles(self, parser: BookmarkHTMLParser, html_file: Path):
        bookmarks = parser.parse(str(html_file))
        titles = [bm.title for bm in bookmarks]
        assert "Python" in titles
        assert "pytest" in titles

    def test_parse_extracts_tags(self, parser: BookmarkHTMLParser, html_file: Path):
        bookmarks = parser.parse(str(html_file))
        python_bm = next(bm for bm in bookmarks if bm.url == "https://python.org")
        assert "python" in python_bm.tags
        assert "programming" in python_bm.tags

    def test_parse_extracts_description(self, parser: BookmarkHTMLParser, html_file: Path):
        bookmarks = parser.parse(str(html_file))
        python_bm = next(bm for bm in bookmarks if bm.url == "https://python.org")
        assert python_bm.description is not None
        assert "Python" in python_bm.description

    def test_parse_bookmark_without_tags(self, parser: BookmarkHTMLParser, html_file: Path):
        bookmarks = parser.parse(str(html_file))
        github_bm = next(bm for bm in bookmarks if bm.url == "https://github.com")
        assert isinstance(github_bm.tags, list)

    def test_parse_nonexistent_file_raises(self, parser: BookmarkHTMLParser):
        with pytest.raises((FileNotFoundError, OSError, Exception)):
            parser.parse("/nonexistent/path/bookmarks.html")


class TestHTMLParserExport:
    def test_export_produces_html_string(self, parser: BookmarkHTMLParser,
                                          sample_bookmarks: list):
        html = parser.export(sample_bookmarks)
        assert isinstance(html, str)
        assert len(html) > 0

    def test_export_contains_urls(self, parser: BookmarkHTMLParser, sample_bookmarks: list):
        html = parser.export(sample_bookmarks)
        for bm in sample_bookmarks:
            assert bm.url in html

    def test_export_contains_titles(self, parser: BookmarkHTMLParser, sample_bookmarks: list):
        html = parser.export(sample_bookmarks)
        for bm in sample_bookmarks:
            if bm.title:
                assert bm.title in html

    def test_export_contains_doctype(self, parser: BookmarkHTMLParser, sample_bookmarks: list):
        html = parser.export(sample_bookmarks)
        assert "NETSCAPE-Bookmark-file-1" in html

    def test_export_empty_list(self, parser: BookmarkHTMLParser):
        html = parser.export([])
        assert isinstance(html, str)
        assert "NETSCAPE-Bookmark-file-1" in html


class TestHTMLParserRoundTrip:
    def test_roundtrip_preserves_urls(self, parser: BookmarkHTMLParser,
                                       sample_bookmarks: list, tmp_path: Path):
        """Export bookmarks to HTML then re-import and verify URLs are preserved."""
        html = parser.export(sample_bookmarks)
        export_path = tmp_path / "exported.html"
        export_path.write_text(html, encoding="utf-8")

        reimported = parser.parse(str(export_path))
        exported_urls = {bm.url for bm in sample_bookmarks}
        reimported_urls = {bm.url for bm in reimported}
        assert exported_urls == reimported_urls

    def test_roundtrip_preserves_titles(self, parser: BookmarkHTMLParser,
                                         sample_bookmarks: list, tmp_path: Path):
        html = parser.export(sample_bookmarks)
        export_path = tmp_path / "exported.html"
        export_path.write_text(html, encoding="utf-8")

        reimported = parser.parse(str(export_path))
        exported_titles = {bm.title for bm in sample_bookmarks if bm.title}
        reimported_titles = {bm.title for bm in reimported if bm.title}
        assert exported_titles == reimported_titles
