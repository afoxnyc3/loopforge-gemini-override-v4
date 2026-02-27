"""Configuration constants for the CLI Bookmark Manager."""

from __future__ import annotations

import os
from pathlib import Path

# ---------------------------------------------------------------------------
# Database paths
# ---------------------------------------------------------------------------

#: Default directory for application data (respects XDG_DATA_HOME on Linux)
_XDG_DATA_HOME = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))

#: Application data directory
APP_DATA_DIR: Path = _XDG_DATA_HOME / "bookmark_manager"

#: Default SQLite database file path
DEFAULT_DB_PATH: Path = APP_DATA_DIR / "bookmarks.db"

#: Environment variable to override the database path
DB_PATH_ENV_VAR: str = "BOOKMARK_MANAGER_DB"

# ---------------------------------------------------------------------------
# SQL schema file
# ---------------------------------------------------------------------------

#: Path to the bundled SQL schema file
SCHEMA_FILE: Path = Path(__file__).parent.parent / "schemas" / "database.sql"

# ---------------------------------------------------------------------------
# URL normalization
# ---------------------------------------------------------------------------

#: Default scheme to add when a URL has no scheme
DEFAULT_SCHEME: str = "https"

#: Accepted URL schemes
ACCEPTED_SCHEMES: frozenset[str] = frozenset({"http", "https", "ftp", "ftps"})

# ---------------------------------------------------------------------------
# Listing / pagination
# ---------------------------------------------------------------------------

#: Default maximum number of bookmarks returned by list operations
DEFAULT_LIST_LIMIT: int = 50

#: Maximum allowed limit for list operations
MAX_LIST_LIMIT: int = 1000

# ---------------------------------------------------------------------------
# Tag constraints
# ---------------------------------------------------------------------------

#: Maximum length of a tag name
MAX_TAG_LENGTH: int = 64

#: Maximum number of tags per bookmark
MAX_TAGS_PER_BOOKMARK: int = 20

# ---------------------------------------------------------------------------
# Title constraints
# ---------------------------------------------------------------------------

#: Maximum length of a bookmark title
MAX_TITLE_LENGTH: int = 500

#: Maximum length of a bookmark description
MAX_DESCRIPTION_LENGTH: int = 2000

# ---------------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------------

#: Default export filename
DEFAULT_EXPORT_FILENAME: str = "bookmarks_export.html"
