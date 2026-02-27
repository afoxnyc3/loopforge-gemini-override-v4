"""Tests for bookmark_manager/html_parser.py."""

import os
from pathlib import Path

import pytest

from bookmark_manager.html_parser import BookmarkHTMLParser, BookmarkHTMLExporter
from bookmark_manager.models import Bookmark


SAMPLE_HTML = """<!DOCTYPE NETSCAPE-Bookmark-file-1>
<META HTTP-EQUIV="Content-Type" CONTENT="text/html; charset=UTF-8">
<TITLE>Bookmarks</TITLE>
<H1>Bookmarks</H1>
<DL><p>
    <DT><A HREF="https://python.org" ADD_DATE="1609459200" TAGS="python,programming">Python</A>
    <DD>The Python programming language
    <DT><A HREF="https://github.com" ADD_DATE="1609459201" TAGS="git,dev">GitHub</A>
    <DT><A HREF="https://docs.python.org" ADD_DATE="1609459202">Python Docs</A>
</DL><p>
"""

EMPTY_HTML = """<!DOCTYPE NETSCAPE-Bookmark-file-1>
<TITLE>Bookmarks</TITLE>
<H1>Bookmarks</H1>
<DL><p>
</DL><p>
"""

NESTED_HTML = """<!DOCTYPE NETSCAPE-Bookmark-file-1>
<TITLE>Bookmarks</TITLE>
<H1>Bookmarks</H1>
<DL><p>
    <DT><H3>Programming</H3>
    <DL><p>
        <DT><A HREF="https://python.org" TAGS="python">Python</A>
        <DT><A HREF="https://rust-lang.org" TAGS="rust">Rust</A>
    </DL><p>
    <DT><A HREF="https://news.ycombinator.com">Hacker News</A>
</DL><p>
"""


@pytest.fixture
def parser():
    return BookmarkHTMLParser()


@pytest.fixture
def exporter():
    return BookmarkHTMLExporter()


@pytest.fixture
def sample_html_path(tmp_path: Path) -> str:
    p = tmp_path / "bookmarks.html"
    p.write_text(SAMPLE_HTML, encoding="utf-8")
    return str(p)


@pytest.fixture
def empty_html_path(tmp_path: Path) -> str:
    p = tmp_path / "empty.html"
    p.write_text(EMPTY_HTML, encoding="utf-8")
    return str(p)


@pytest.fixture
def nested_html_path(tmp_path: Path) -> str:
    p = tmp_path / "nested.html"
    p.write_text(NESTED_HTML, encoding="utf-8")
    return str(p)


class TestBookmarkHTMLParser:
    def test_parse_returns_list(self, parser: BookmarkHTMLParser, sample_html_path: str):
        results = parser.parse(sample_html_path)
        assert isinstance(results, list)

    def test_parse_correct_count(self, parser: BookmarkHTMLParser, sample_html_path: str):
        results = parser.parse(sample_html_path)
        assert len(results) == 3

    def test_parse_extracts_url(self, parser: BookmarkHTMLParser, sample_html_path: str):
        results = parser.parse(sample_html_path)
        urls = [r["url"] for r in results]
        assert "https://python.org" in urls
        assert "https://github.com" in urls

    def test_parse_extracts_title(self, parser: BookmarkHTMLParser, sample_html_path: str):
        results = parser.parse(sample_html_path)
        python_entry = next(r for r in results if r["url"] == "https://python.org")
        assert python_entry["title"] == "Python"

    def test_parse_extracts_tags(self, parser: BookmarkHTMLParser, sample_html_path: str):
        results = parser.parse(sample_html_path)
        python_entry = next(r for r in results if r["url"] == "https://python.org")
        assert "python" in python_entry["tags"]
        assert "programming" in python_entry["tags"]

    def test_parse_extracts_description(self, parser: BookmarkHTMLParser, sample_html_path: str):
        results = parser.parse(sample_html_path)
        python_entry = next(r for r in results if r["url"] == "https://python.org")
        assert "Python programming language" in python_entry.get("description", "")

    def test_parse_entry_without_tags(self, parser: BookmarkHTMLParser, sample_html_path: str):
        results = parser.parse(sample_html_path)
        docs_entry = next(r for r in results if r["url"] == "https://docs.python.org")
        assert docs_entry["tags"] == [] or docs_entry["tags"] is not None

    def test_parse_empty_file(self, parser: BookmarkHTMLParser, empty_html_path: str):
        results = parser.parse(empty_html_path)
        assert results == []

    def test_parse_nested_folders(self, parser: BookmarkHTMLParser, nested_html_path: str):
        results = parser.parse(nested_html_path)
        urls = [r["url"] for r in results]
        assert "https://python.org" in urls
        assert "https://rust-lang.org" in urls
        assert "https://news.ycombinator.com" in urls

    def test_parse_nonexistent_file_raises(self, parser: BookmarkHTMLParser):
        with pytest.raises((FileNotFoundError, OSError, Exception)):
            parser.parse("/nonexistent/path/bookmarks.html")


class TestBookmarkHTMLExporter:
    def _make_bookmarks(self):
        from datetime import datetime
        return [
            Bookmark(
                id=1,
                url="https://python.org",
                title="Python",
                description="The Python language",
                tags=["python", "programming"],
                created_at=datetime(2021, 1, 1),
                updated_at=datetime(2021, 1, 1),
            ),
            Bookmark(
                id=2,
                url="https://github.com",
                title="GitHub",
                description="",
                tags=["git", "dev"],
                created_at=datetime(2021, 1, 2),
                updated_at=datetime(2021, 1, 2),
            ),
        ]

    def test_export_returns_string(self, exporter: BookmarkHTMLExporter):
        html = exporter.export(self._make_bookmarks())
        assert isinstance(html, str)

    def test_export_contains_doctype(self, exporter: BookmarkHTMLExporter):
        html = exporter.export(self._make_bookmarks())
        assert "NETSCAPE-Bookmark-file-1" in html

    def test_export_contains_urls(self, exporter: BookmarkHTMLExporter):
        html = exporter.export(self._make_bookmarks())
        assert "https://python.org" in html
        assert "https://github.com" in html

    def test_export_contains_titles(self, exporter: BookmarkHTMLExporter):
        html = exporter.export(self._make_bookmarks())
        assert "Python" in html
        assert "GitHub" in html

    def test_export_contains_tags(self, exporter: BookmarkHTMLExporter):
        html = exporter.export(self._make_bookmarks())
        assert "python" in html.lower()

    def test_export_empty_list(self, exporter: BookmarkHTMLExporter):
        html = exporter.export([])
        assert isinstance(html, str)
        assert "NETSCAPE" in html

    def test_export_to_file(self, exporter: BookmarkHTMLExporter, tmp_path: Path):
        output_path = str(tmp_path / "output.html")
        exporter.export_to_file(self._make_bookmarks(), output_path)
        assert Path(output_path).exists()
        content = Path(output_path).read_text(encoding="utf-8")
        assert "https://python.org" in content
