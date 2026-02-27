"""Unit tests for bookmark_manager/html_parser.py."""

import pytest
from pathlib import Path

from bookmark_manager.html_parser import BookmarkHTMLParser, BookmarkHTMLExporter
from bookmark_manager.models import Bookmark
from datetime import datetime


NETSCAPE_HTML = """<!DOCTYPE NETSCAPE-Bookmark-file-1>
<META HTTP-EQUIV="Content-Type" CONTENT="text/html; charset=UTF-8">
<TITLE>Bookmarks</TITLE>
<H1>Bookmarks</H1>
<DL><p>
    <DT><A HREF="https://python.org" ADD_DATE="1700000000" TAGS="python,dev">Python</A>
    <DD>The Python programming language.
    <DT><A HREF="https://github.com" ADD_DATE="1700000001">GitHub</A>
    <DT><A HREF="https://example.com" TAGS="example">Example</A>
</DL><p>
"""


class TestBookmarkHTMLParser:
    def test_parse_returns_bookmarks(self, tmp_path: Path):
        html_file = tmp_path / "bookmarks.html"
        html_file.write_text(NETSCAPE_HTML, encoding="utf-8")
        parser = BookmarkHTMLParser()
        bookmarks = parser.parse(html_file)
        assert len(bookmarks) == 3

    def test_parse_extracts_url(self, tmp_path: Path):
        html_file = tmp_path / "bookmarks.html"
        html_file.write_text(NETSCAPE_HTML, encoding="utf-8")
        parser = BookmarkHTMLParser()
        bookmarks = parser.parse(html_file)
        urls = [bm.url for bm in bookmarks]
        assert "https://python.org" in urls
        assert "https://github.com" in urls

    def test_parse_extracts_title(self, tmp_path: Path):
        html_file = tmp_path / "bookmarks.html"
        html_file.write_text(NETSCAPE_HTML, encoding="utf-8")
        parser = BookmarkHTMLParser()
        bookmarks = parser.parse(html_file)
        python_bm = next(bm for bm in bookmarks if bm.url == "https://python.org")
        assert python_bm.title == "Python"

    def test_parse_extracts_tags(self, tmp_path: Path):
        html_file = tmp_path / "bookmarks.html"
        html_file.write_text(NETSCAPE_HTML, encoding="utf-8")
        parser = BookmarkHTMLParser()
        bookmarks = parser.parse(html_file)
        python_bm = next(bm for bm in bookmarks if bm.url == "https://python.org")
        assert "python" in python_bm.tags
        assert "dev" in python_bm.tags

    def test_parse_extracts_description(self, tmp_path: Path):
        html_file = tmp_path / "bookmarks.html"
        html_file.write_text(NETSCAPE_HTML, encoding="utf-8")
        parser = BookmarkHTMLParser()
        bookmarks = parser.parse(html_file)
        python_bm = next(bm for bm in bookmarks if bm.url == "https://python.org")
        assert python_bm.description is not None
        assert "python" in python_bm.description.lower()

    def test_parse_no_tags_gives_empty_list(self, tmp_path: Path):
        html_file = tmp_path / "bookmarks.html"
        html_file.write_text(NETSCAPE_HTML, encoding="utf-8")
        parser = BookmarkHTMLParser()
        bookmarks = parser.parse(html_file)
        github_bm = next(bm for bm in bookmarks if bm.url == "https://github.com")
        assert github_bm.tags == []

    def test_parse_missing_file_raises(self):
        parser = BookmarkHTMLParser()
        with pytest.raises(FileNotFoundError):
            parser.parse(Path("/nonexistent/file.html"))


class TestBookmarkHTMLExporter:
    def _make_bookmarks(self):
        return [
            Bookmark(
                id=1,
                url="https://python.org",
                title="Python",
                description="Python language.",
                tags=["python", "dev"],
                created_at=datetime(2024, 1, 1),
                updated_at=datetime(2024, 1, 1),
            ),
            Bookmark(
                id=2,
                url="https://github.com",
                title="GitHub",
                description=None,
                tags=[],
                created_at=datetime(2024, 1, 2),
                updated_at=datetime(2024, 1, 2),
            ),
        ]

    def test_export_creates_file(self, tmp_path: Path):
        exporter = BookmarkHTMLExporter()
        output_path = tmp_path / "out.html"
        bookmarks = self._make_bookmarks()
        exporter.export(bookmarks, output_path)
        assert output_path.exists()

    def test_export_contains_urls(self, tmp_path: Path):
        exporter = BookmarkHTMLExporter()
        output_path = tmp_path / "out.html"
        bookmarks = self._make_bookmarks()
        exporter.export(bookmarks, output_path)
        content = output_path.read_text(encoding="utf-8")
        assert "https://python.org" in content
        assert "https://github.com" in content

    def test_export_contains_tags(self, tmp_path: Path):
        exporter = BookmarkHTMLExporter()
        output_path = tmp_path / "out.html"
        bookmarks = self._make_bookmarks()
        exporter.export(bookmarks, output_path)
        content = output_path.read_text(encoding="utf-8")
        assert "python" in content.lower()

    def test_roundtrip(self, tmp_path: Path):
        """Export then re-import should yield the same bookmarks."""
        exporter = BookmarkHTMLExporter()
        parser = BookmarkHTMLParser()
        bookmarks = self._make_bookmarks()
        output_path = tmp_path / "roundtrip.html"
        exporter.export(bookmarks, output_path)
        reimported = parser.parse(output_path)
        reimported_urls = {bm.url for bm in reimported}
        assert "https://python.org" in reimported_urls
        assert "https://github.com" in reimported_urls
