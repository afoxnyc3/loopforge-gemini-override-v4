# Bookmark Manager

A command-line bookmark manager that stores URLs with tags in a local SQLite database. Supports add, search, list, delete, and import/export from browser HTML bookmark files.

## Installation

```bash
# Clone the repo
git clone https://github.com/afoxnyc3/loopforge-gemini-override-v4.git
cd loopforge-gemini-override-v4

# Create a virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install (editable mode recommended for development)
pip install -e .[dev]
```

After installation the `bookmark-manager` command is available on your PATH.

## Usage

### Add a bookmark
```bash
bookmark-manager add https://example.com -T "Example Site" -t python -t reference
bookmark-manager add https://docs.python.org --title "Python Docs" --tag python --tag docs
```

### List bookmarks
```bash
bookmark-manager list                  # all bookmarks (up to 50)
bookmark-manager list -t python        # filter by tag
bookmark-manager list -t python -t docs  # filter by multiple tags (AND)
bookmark-manager list --limit 100 --offset 0
```

### Search bookmarks
```bash
bookmark-manager search python         # keyword search in URL/title/description
bookmark-manager search "machine learning" --limit 20
```

### Show a single bookmark
```bash
bookmark-manager show 42
```

### Update a bookmark
```bash
bookmark-manager update 42 --title "New Title"
bookmark-manager update 42 --tag python --tag updated   # replaces all tags
bookmark-manager update 42 --description "A great resource"
```

### Delete a bookmark
```bash
bookmark-manager delete 42          # prompts for confirmation
bookmark-manager delete 42 --yes    # skip confirmation
```

### List tags
```bash
bookmark-manager tags
bookmark-manager tags --limit 20
```

### Import from browser HTML
```bash
bookmark-manager import-html ~/Downloads/bookmarks.html
```
Supports Chrome, Firefox, and Safari bookmark export formats.

### Export to browser HTML
```bash
bookmark-manager export-html ~/Desktop/my_bookmarks.html
bookmark-manager export-html ~/Desktop/python_bookmarks.html --tag python
```

## Database

The SQLite database is stored at `~/.bookmark_manager/bookmarks.db` by default. Override with the `BOOKMARK_MANAGER_DB_PATH` environment variable.

## Development

```bash
# Run tests
pytest

# Lint
ruff check .

# Type check
mypy bookmark_manager
```

## License

MIT
