"""Configuration constants for the bookmark manager."""

from pathlib import Path

# Application metadata
APP_NAME = "bookmark_manager"
APP_VERSION = "1.0.0"

# Database configuration
# Uses user's home directory — no hardcoded absolute paths
DEFAULT_DB_DIR = Path.home() / ".bookmark_manager"
DEFAULT_DB_NAME = "bookmarks.db"
DB_PATH = DEFAULT_DB_DIR / DEFAULT_DB_NAME

# URL validation
VALID_SCHEMES = {"http", "https", "ftp", "ftps"}
DEFAULT_SCHEME = "https"
MAX_URL_LENGTH = 2048
MAX_TITLE_LENGTH = 500
MAX_DESCRIPTION_LENGTH = 2000

# Tag configuration
MAX_TAG_LENGTH = 50
MAX_TAGS_PER_BOOKMARK = 20
TAG_SEPARATOR = ","

# Search/list configuration
DEFAULT_LIST_LIMIT = 50
MAX_LIST_LIMIT = 1000

# Import/export configuration
NETSCAPE_HEADER = """<!DOCTYPE NETSCAPE-Bookmark-file-1>
<!-- This is an automatically generated file.
     It will be read and overwritten.
     DO NOT EDIT! -->
<META HTTP-EQUIV="Content-Type" CONTENT="text/html; charset=UTF-8">
<TITLE>Bookmarks</TITLE>
<H1>Bookmarks</H1>
"""

SUPPORTED_IMPORT_FORMATS = [".html", ".htm"]
SUPPORTED_EXPORT_FORMATS = [".html", ".htm"]

# Rich console styling
STYLE_SUCCESS = "green"
STYLE_ERROR = "red"
STYLE_WARNING = "yellow"
STYLE_INFO = "cyan"
STYLE_URL = "blue underline"
STYLE_TAG = "magenta"
STYLE_TITLE = "bold"
STYLE_DIM = "dim"
