"""Data models for the CLI Bookmark Manager.

All models are frozen dataclasses to ensure immutability after creation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional


@dataclass(frozen=True)
class Tag:
    """Represents a bookmark tag."""

    id: int
    name: str
    created_at: datetime = field(default_factory=datetime.utcnow)

    def __str__(self) -> str:
        return self.name


@dataclass(frozen=True)
class Bookmark:
    """Represents a stored bookmark."""

    id: int
    url: str
    title: str
    description: str
    created_at: datetime
    updated_at: datetime
    tags: List[str] = field(default_factory=list)

    def __str__(self) -> str:
        tag_str = ", ".join(self.tags) if self.tags else "(no tags)"
        return f"[{self.id}] {self.title}\n    {self.url}\n    Tags: {tag_str}"


@dataclass(frozen=True)
class TagCount:
    """Represents a tag with its usage count."""

    name: str
    count: int

    def __str__(self) -> str:
        return f"{self.name} ({self.count})"


@dataclass
class ImportResult:
    """Result of a bookmark import operation."""

    total: int = 0
    imported: int = 0
    skipped: int = 0
    errors: List[str] = field(default_factory=list)

    def add_error(self, message: str) -> None:
        """Record an import error."""
        self.errors.append(message)
        self.total += 1

    def add_success(self) -> None:
        """Record a successful import."""
        self.total += 1
        self.imported += 1

    def add_skip(self) -> None:
        """Record a skipped bookmark (e.g. duplicate)."""
        self.total += 1
        self.skipped += 1

    def __str__(self) -> str:
        return (
            f"Import complete: {self.imported} imported, "
            f"{self.skipped} skipped, "
            f"{len(self.errors)} errors "
            f"(total processed: {self.total})"
        )
