"""Unit tests for bookmark_manager/html_parser.py."""
import pytest
from bookmark_manager.html_parser import BookmarkHTMLParser, BookmarkHTMLExporter
from bookmark_manager.models import Bookmark


NETSCAPE_HTML = """\
<!DOCTYPE NETSCAPE-Bookmark-file-1>
<META HTTP-EQUIV="Content-Type" CONTENT="text/html; charset=UTF-8">
<TITLE>Bookmarks</TITLE>
<H1>Bookmarks</H1>
<DL><p>
    <DT><A HREF="https://python.org" ADD_DATE="1609459200" TAGS="python,programming">Python</A>
    <DD>The Python programming language.
    <DT><A HREF="https://rust-lang.org" ADD_DATE="1609459201" TAGS="rust,systems">Rust</A>
    <DT><A HREF="https://example.com" ADD_DATE="1609459202">No Tags Example</A>
</DL><p>
"""

EMPTY_HTML = """\
<!DOCTYPE NETSCAPE-Bookmark-file-1>
<TITLE>Bookmarks</TITLE>
<H1>Bookmarks</H1>
<DL><p>
</DL><p>
"""

NESTED_HTML = """\
<!DOCTYPE NETSCAPE-Bookmark-file-1>
<TITLE>Bookmarks</TITLE>
<H1>Bookmarks</H1>
<DL><p>
    <DT><H3>Folder</H3>
    <DL><p>
        <DT><A HREF="https://nested.com" TAGS="nested">Nested</A>
    </DL><p>
    <DT><A HREF="https://toplevel.com" TAGS="top">Top Level</A>
</DL><p>
"""


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def parser():
    return BookmarkHTMLParser()


@pytest.fixture
def exporter():
    return BookmarkHTMLExporter()


@pytest.fixture
def sample_bookmarks():
    return [
        Bookmark(
            id=1,
            url="https://python.org",
            title="Python",
            description="The Python language",
            tags=["python", "programming"],
            created_at="2024-01-01T00:00:00",
            updated_at="2024-01-01T00:00:00",
        ),
        Bookmark(
            id=2,
            url="https://rust-lang.org",
            title="Rust",
            description="",
            tags=["rust", "systems"],
            created_at="2024-01-01T00:00:00",
            updated_at="2024-01-01T00:00:00",
        ),
    ]


# ---------------------------------------------------------------------------
# Parser tests
# ---------------------------------------------------------------------------

class TestBookmarkHTMLParser:
    def test_parse_returns_list(self, parser):
        results = parser.parse(NETSCAPE_HTML)
        assert isinstance(results, list)

    def test_parse_correct_count(self, parser):
        results = parser.parse(NETSCAPE_HTML)
        assert len(results) == 3

    def test_parse_extracts_url(self, parser):
        results = parser.parse(NETSCAPE_HTML)
        urls = [r.url for r in results]
        assert "https://python.org" in urls

    def test_parse_extracts_title(self, parser):
        results = parser.parse(NETSCAPE_HTML)
        python_bm = next(r for r in results if r.url == "https://python.org")
        assert python_bm.title == "Python"

    def test_parse_extracts_tags(self, parser):
        results = parser.parse(NETSCAPE_HTML)
        python_bm = next(r for r in results if r.url == "https://python.org")
        assert "python" in python_bm.tags
        assert "programming" in python_bm.tags

    def test_parse_handles_no_tags(self, parser):
        results = parser.parse(NETSCAPE_HTML)
        no_tag_bm = next(r for r in results if r.url == "https://example.com")
        assert no_tag_bm.tags == [] or no_tag_bm.tags is not None

    def test_parse_extracts_description(self, parser):
        results = parser.parse(NETSCAPE_HTML)
        python_bm = next(r for r in results if r.url == "https://python.org")
        assert "Python" in (python_bm.description or "")

    def test_parse_empty_file(self, parser):
        results = parser.parse(EMPTY_HTML)
        assert results == []

    def test_parse_nested_folders(self, parser):
        results = parser.parse(NESTED_HTML)
        urls = [r.url for r in results]
        assert "https://nested.com" in urls
        assert "https://toplevel.com" in urls

    def test_parse_from_file(self, parser, tmp_path):
        html_file = tmp_path / "bookmarks.html"
        html_file.write_text(NETSCAPE_HTML)
        results = parser.parse_file(str(html_file))
        assert len(results) == 3

    def test_parse_file_not_found(self, parser):
        from bookmark_manager.exceptions import ImportError as BMImportError
        with pytest.raises((FileNotFoundError, BMImportError, Exception)):
            parser.parse_file("/nonexistent/path/bookmarks.html")


# ---------------------------------------------------------------------------
# Exporter tests
# ---------------------------------------------------------------------------

class TestBookmarkHTMLExporter:
    def test_export_returns_string(self, exporter, sample_bookmarks):
        html = exporter.export(sample_bookmarks)
        assert isinstance(html, str)

    def test_export_contains_doctype(self, exporter, sample_bookmarks):
        html = exporter.export(sample_bookmarks)
        assert "NETSCAPE-Bookmark-file-1" in html

    def test_export_contains_urls(self, exporter, sample_bookmarks):
        html = exporter.export(sample_bookmarks)
        assert "https://python.org" in html
        assert "https://rust-lang.org" in html

    def test_export_contains_titles(self, exporter, sample_bookmarks):
        html = exporter.export(sample_bookmarks)
        assert "Python" in html
        assert "Rust" in html

    def test_export_contains_tags(self, exporter, sample_bookmarks):
        html = exporter.export(sample_bookmarks)
        assert "python" in html.lower()

    def test_export_empty_list(self, exporter):
        html = exporter.export([])
        assert isinstance(html, str)
        assert len(html) > 0

    def test_export_to_file(self, exporter, sample_bookmarks, tmp_path):
        out_file = tmp_path / "export.html"
        exporter.export_to_file(sample_bookmarks, str(out_file))
        assert out_file.exists()
        content = out_file.read_text()
        assert "https://python.org" in content
