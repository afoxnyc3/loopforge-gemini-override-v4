"""Tests for bookmark_manager/html_parser.py import/export."""
import os

import pytest

from bookmark_manager.html_parser import parse_bookmarks_html, export_bookmarks_html
from bookmark_manager.models import Bookmark
from datetime import datetime, timezone


class TestParseBookmarksHTML:
    """Tests for parsing Netscape bookmark HTML files."""

    def test_parse_sample_html(self, sample_html_bookmarks):
        """Parse the sample HTML and verify extracted bookmarks."""
        bookmarks = parse_bookmarks_html(sample_html_bookmarks)
        assert len(bookmarks) >= 2
        urls = [bm.url for bm in bookmarks]
        assert "https://python.org" in urls
        assert "https://github.com" in urls
        assert "https://example.com" in urls

    def test_parse_extracts_titles(self, sample_html_bookmarks):
        bookmarks = parse_bookmarks_html(sample_html_bookmarks)
        titles = [bm.title for bm in bookmarks]
        assert "Python" in titles
        assert "GitHub" in titles

    def test_parse_extracts_tags(self, sample_html_bookmarks):
        bookmarks = parse_bookmarks_html(sample_html_bookmarks)
        python_bm = [bm for bm in bookmarks if bm.url == "https://python.org"][0]
        assert "python" in python_bm.tags or "programming" in python_bm.tags

    def test_parse_extracts_description(self, sample_html_bookmarks):
        bookmarks = parse_bookmarks_html(sample_html_bookmarks)
        python_bm = [bm for bm in bookmarks if bm.url == "https://python.org"][0]
        assert python_bm.description is not None
        assert "python" in python_bm.description.lower()

    def test_parse_empty_html(self):
        bookmarks = parse_bookmarks_html("")
        assert bookmarks == []

    def test_parse_html_no_bookmarks(self):
        html = "<html><body><p>No bookmarks here</p></body></html>"
        bookmarks = parse_bookmarks_html(html)
        assert bookmarks == []

    def test_parse_from_file(self, html_file):
        with open(html_file, "r", encoding="utf-8") as f:
            content = f.read()
        bookmarks = parse_bookmarks_html(content)
        assert len(bookmarks) >= 2


class TestExportBookmarksHTML:
    """Tests for exporting bookmarks to Netscape HTML format."""

    def test_export_produces_valid_html(self):
        now = datetime.now(timezone.utc)
        bookmarks = [
            Bookmark(
                id=1,
                url="https://example.com",
                title="Example",
                description="An example",
                tags=["test"],
                created_at=now,
                updated_at=now,
            )
        ]
        html = export_bookmarks_html(bookmarks)
        assert "<!DOCTYPE NETSCAPE-Bookmark-file-1>" in html
        assert "https://example.com" in html
        assert "Example" in html

    def test_export_includes_tags(self):
        now = datetime.now(timezone.utc)
        bookmarks = [
            Bookmark(
                id=1,
                url="https://example.com",
                title="Example",
                tags=["python", "web"],
                created_at=now,
                updated_at=now,
            )
        ]
        html = export_bookmarks_html(bookmarks)
        assert "TAGS=" in html
        assert "python" in html

    def test_export_empty_list(self):
        html = export_bookmarks_html([])
        assert "<!DOCTYPE NETSCAPE-Bookmark-file-1>" in html

    def test_export_roundtrip(self):
        """Export and re-import should preserve bookmark data."""
        now = datetime.now(timezone.utc)
        original = [
            Bookmark(
                id=1,
                url="https://roundtrip.com",
                title="Roundtrip Test",
                description="Testing roundtrip",
                tags=["test", "roundtrip"],
                created_at=now,
                updated_at=now,
            )
        ]
        html = export_bookmarks_html(original)
        parsed = parse_bookmarks_html(html)
        assert len(parsed) == 1
        assert parsed[0].url == "https://roundtrip.com"
        assert parsed[0].title == "Roundtrip Test"

    def test_export_to_file(self, tmp_path):
        now = datetime.now(timezone.utc)
        bookmarks = [
            Bookmark(
                id=1,
                url="https://file-test.com",
                title="File Test",
                tags=["file"],
                created_at=now,
                updated_at=now,
            )
        ]
        html = export_bookmarks_html(bookmarks)
        outfile = tmp_path / "export.html"
        outfile.write_text(html, encoding="utf-8")
        assert outfile.exists()
        content = outfile.read_text(encoding="utf-8")
        assert "https://file-test.com" in content
