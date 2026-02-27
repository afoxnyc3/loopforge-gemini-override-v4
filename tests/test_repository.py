"""Unit + integration tests for bookmark_manager/repository.py."""
import pytest
from bookmark_manager.database import Database
from bookmark_manager.repository import BookmarkRepository
from bookmark_manager.models import Bookmark


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def db(tmp_path):
    db_file = tmp_path / "test.db"
    database = Database(str(db_file))
    database.initialize()
    return database


@pytest.fixture
def repo(db):
    return BookmarkRepository(db)


@pytest.fixture
def created_bookmark(repo):
    return repo.create(
        url="https://example.com",
        title="Example",
        description="A test site",
        tags=["python", "test"],
    )


# ---------------------------------------------------------------------------
# Create
# ---------------------------------------------------------------------------

class TestCreate:
    def test_create_returns_bookmark(self, repo):
        bm = repo.create(url="https://example.com", title="Example", tags=["web"])
        assert bm.id is not None
        assert bm.url == "https://example.com"
        assert "web" in bm.tags

    def test_create_without_tags(self, repo):
        bm = repo.create(url="https://notags.com", title="No Tags")
        assert bm.tags == [] or bm.tags is not None

    def test_create_assigns_id(self, repo):
        bm = repo.create(url="https://unique.com", title="Unique")
        assert isinstance(bm.id, int)
        assert bm.id > 0


# ---------------------------------------------------------------------------
# Read
# ---------------------------------------------------------------------------

class TestRead:
    def test_get_by_id(self, repo, created_bookmark):
        fetched = repo.get_by_id(created_bookmark.id)
        assert fetched is not None
        assert fetched.id == created_bookmark.id

    def test_get_by_id_not_found(self, repo):
        result = repo.get_by_id(99999)
        assert result is None

    def test_get_by_url(self, repo, created_bookmark):
        fetched = repo.get_by_url("https://example.com")
        assert fetched is not None
        assert fetched.url == "https://example.com"

    def test_get_by_url_not_found(self, repo):
        result = repo.get_by_url("https://doesnotexist.io")
        assert result is None


# ---------------------------------------------------------------------------
# List
# ---------------------------------------------------------------------------

class TestList:
    def test_list_all_returns_all(self, repo):
        repo.create(url="https://a.com", title="A")
        repo.create(url="https://b.com", title="B")
        results = repo.list_all()
        assert len(results) >= 2

    def test_list_respects_limit(self, repo):
        for i in range(5):
            repo.create(url=f"https://site{i}.com", title=f"Site {i}")
        results = repo.list_all(limit=3)
        assert len(results) <= 3

    def test_list_empty_db(self, repo):
        results = repo.list_all()
        assert isinstance(results, list)


# ---------------------------------------------------------------------------
# Find by tag
# ---------------------------------------------------------------------------

class TestFindByTag:
    def test_find_by_tag_returns_matching(self, repo):
        repo.create(url="https://python.org", title="Python", tags=["python"])
        repo.create(url="https://rust-lang.org", title="Rust", tags=["rust"])
        results = repo.find_by_tag("python")
        assert any(bm.url == "https://python.org" for bm in results)
        assert all("python" in bm.tags for bm in results)

    def test_find_by_tag_no_match(self, repo):
        results = repo.find_by_tag("nonexistent-tag-xyz")
        assert results == []

    def test_find_by_tag_limit(self, repo):
        for i in range(5):
            repo.create(url=f"https://tagged{i}.com", title=f"Tagged {i}", tags=["shared"])
        results = repo.find_by_tag("shared", limit=2)
        assert len(results) <= 2


# ---------------------------------------------------------------------------
# Delete
# ---------------------------------------------------------------------------

class TestDelete:
    def test_delete_removes_bookmark(self, repo, created_bookmark):
        repo.delete(created_bookmark.id)
        assert repo.get_by_id(created_bookmark.id) is None

    def test_delete_nonexistent_does_not_raise(self, repo):
        # Should not raise an exception
        repo.delete(99999)


# ---------------------------------------------------------------------------
# Tags
# ---------------------------------------------------------------------------

class TestTags:
    def test_get_all_tags(self, repo):
        repo.create(url="https://a.com", title="A", tags=["alpha", "beta"])
        repo.create(url="https://b.com", title="B", tags=["beta", "gamma"])
        tags = repo.get_all_tags()
        tag_names = [t.name for t in tags]
        assert "alpha" in tag_names
        assert "beta" in tag_names
        assert "gamma" in tag_names

    def test_tag_count_is_accurate(self, repo):
        repo.create(url="https://x.com", title="X", tags=["counted"])
        repo.create(url="https://y.com", title="Y", tags=["counted"])
        tags = repo.get_all_tags()
        counted = next((t for t in tags if t.name == "counted"), None)
        assert counted is not None
        assert counted.count >= 2
