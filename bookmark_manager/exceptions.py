"""Custom exception hierarchy for the bookmark manager."""


class BookmarkManagerError(Exception):
    """Base exception for all bookmark manager errors."""

    def __init__(self, message: str = "An error occurred in the bookmark manager.") -> None:
        super().__init__(message)
        self.message = message

    def __str__(self) -> str:
        return self.message


# --- URL / Bookmark Errors ---

class InvalidURLError(BookmarkManagerError):
    """Raised when a URL fails validation."""

    def __init__(self, url: str, reason: str = "Invalid URL format.") -> None:
        super().__init__(f"Invalid URL '{url}': {reason}")
        self.url = url
        self.reason = reason


class DuplicateBookmarkError(BookmarkManagerError):
    """Raised when attempting to add a URL that already exists."""

    def __init__(self, url: str) -> None:
        super().__init__(f"Bookmark already exists for URL: '{url}'")
        self.url = url


class BookmarkNotFoundError(BookmarkManagerError):
    """Raised when a bookmark cannot be found by ID or URL."""

    def __init__(self, identifier: str | int) -> None:
        super().__init__(f"Bookmark not found: '{identifier}'")
        self.identifier = identifier


# --- Tag Errors ---

class TagNotFoundError(BookmarkManagerError):
    """Raised when a tag does not exist."""

    def __init__(self, tag: str) -> None:
        super().__init__(f"Tag not found: '{tag}'")
        self.tag = tag


class InvalidTagError(BookmarkManagerError):
    """Raised when a tag name is invalid (too long, bad chars, etc.)."""

    def __init__(self, tag: str, reason: str = "Invalid tag.") -> None:
        super().__init__(f"Invalid tag '{tag}': {reason}")
        self.tag = tag
        self.reason = reason


# --- Import / Export Errors ---

class BookmarkImportError(BookmarkManagerError):
    """Raised when a bookmark import operation fails."""

    def __init__(self, filepath: str, reason: str = "Import failed.") -> None:
        super().__init__(f"Failed to import from '{filepath}': {reason}")
        self.filepath = filepath
        self.reason = reason


class BookmarkExportError(BookmarkManagerError):
    """Raised when a bookmark export operation fails."""

    def __init__(self, filepath: str, reason: str = "Export failed.") -> None:
        super().__init__(f"Failed to export to '{filepath}': {reason}")
        self.filepath = filepath
        self.reason = reason


# --- Database Errors ---

class DatabaseError(BookmarkManagerError):
    """Raised when a database operation fails."""

    def __init__(self, operation: str = "unknown", reason: str = "Database error.") -> None:
        super().__init__(f"Database error during '{operation}': {reason}")
        self.operation = operation
        self.reason = reason


class DatabaseInitError(DatabaseError):
    """Raised when the database cannot be initialized."""

    def __init__(self, reason: str = "Could not initialize database.") -> None:
        super().__init__(operation="init", reason=reason)
