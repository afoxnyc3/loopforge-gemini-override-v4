"""Custom exception hierarchy for the CLI Bookmark Manager."""

from __future__ import annotations

from typing import Optional


class BookmarkManagerError(Exception):
    """Base exception for all bookmark manager errors."""

    def __init__(self, message: str, details: Optional[str] = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details

    def __str__(self) -> str:
        if self.details:
            return f"{self.message}: {self.details}"
        return self.message


class BookmarkNotFoundError(BookmarkManagerError):
    """Raised when a bookmark cannot be found by ID or URL."""

    def __init__(self, identifier: str | int) -> None:
        super().__init__(f"Bookmark not found", details=str(identifier))
        self.identifier = identifier


class DuplicateBookmarkError(BookmarkManagerError):
    """Raised when attempting to add a bookmark with a URL that already exists."""

    def __init__(self, url: str) -> None:
        super().__init__("Bookmark already exists", details=url)
        self.url = url


class InvalidURLError(BookmarkManagerError):
    """Raised when a URL fails validation."""

    def __init__(self, url: str, reason: Optional[str] = None) -> None:
        super().__init__("Invalid URL", details=f"{url}" + (f" — {reason}" if reason else ""))
        self.url = url
        self.reason = reason


class TagNotFoundError(BookmarkManagerError):
    """Raised when a tag cannot be found by name."""

    def __init__(self, tag_name: str) -> None:
        super().__init__("Tag not found", details=tag_name)
        self.tag_name = tag_name


class DatabaseError(BookmarkManagerError):
    """Raised when a database operation fails unexpectedly."""

    def __init__(self, operation: str, details: Optional[str] = None) -> None:
        super().__init__(f"Database error during '{operation}'", details=details)
        self.operation = operation


class ImportError(BookmarkManagerError):  # noqa: A001 — intentional shadow of builtin
    """Raised when an import operation fails at the file/parse level."""

    def __init__(self, filepath: str, reason: Optional[str] = None) -> None:
        super().__init__(f"Import failed for '{filepath}'", details=reason)
        self.filepath = filepath
        self.reason = reason


class ExportError(BookmarkManagerError):
    """Raised when an export operation fails."""

    def __init__(self, filepath: str, reason: Optional[str] = None) -> None:
        super().__init__(f"Export failed for '{filepath}'", details=reason)
        self.filepath = filepath
        self.reason = reason
