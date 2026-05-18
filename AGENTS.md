# AGENTS.md

## Setup & Run

```bash
uv sync                          # install deps, create .venv (not venv/)
uv run python main.py            # run the worker
uv run python -m scripts.ai_test      # test DeepSeek connection
uv run python -m scripts.ai_test --email  # test extraction with sample email
uv run python -m scripts.gmail_test     # test IMAP connection
uv run ruff check .              # lint
uv run ruff format .             # format
```

**Never** use `pip install` or `python3 -m venv`. Everything goes through `uv`.

## Environment

`.env` is **required** at the project root. Copy `.env.example` and fill in:
- `DATABASE_URL` — Neon PostgreSQL connection string (no local DB)
- `DEEPSEEK_API_KEY`, `DEEPSEEK_BASE_URL`, `DEEPSEEK_MODEL`
- `IMAP_SERVER`, `EMAIL_USER`, `EMAIL_PASSWORD`
- `SEARCH_QUERIES` — comma-separated email filters
- `FETCH_DAYS_LIMIT` (default 30), `TIMEZONE_OFFSET` (default -6 for El Salvador)

## Architecture

```
main.py          # entry point: creates tables, seeds categories, syncs emails
src/
├── database.py  # SQLAlchemy engine + Base (declarative_base, 1.x style)
├── models.py    # Category + Expense models, DEFAULT_CATEGORIES, seed_categories()
├── ai_service.py # calls DeepSeek (OpenAI-compatible) API
├── email_service.py # IMAP fetch, dedup via $Processed flag + email_id unique
└── utils.py     # prompt builder, HTML cleaner, pre-flight checks
scripts/         # test/utility scripts (is a Python package, has __init__.py)
```

## Database

- **Neon PostgreSQL** only — no local fallback
- Tables auto-created on startup via `Base.metadata.create_all(bind=engine)` in `main.py`
- No migration framework (Alembic, etc.). Schema changes go as raw SQL on Neon
- `categories` table has `is_active` for soft delete; `seed_categories()` runs once on first startup
- `categories` table has `is_editable` for protecting default categories from deletion

### Database Migrations

For schema changes, write a one-off Python script to `/tmp/` and run it:

```bash
# 1. Write the migration script
cat > /tmp/migrate_<name>.py << 'EOF'
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))
with engine.connect() as conn:
    conn.execute(text("ALTER TABLE ..."))
    conn.commit()
EOF

# 2. Run it (needs DATABASE_URL from .env)
DATABASE_URL="$(grep DATABASE_URL .env | cut -d= -f2-)" uv run python /tmp/migrate_<name>.py
```

- Always use `IF NOT EXISTS` / `IF EXISTS` to keep scripts idempotent
- Script goes to `/tmp/` — ephemeral, no need to track in version control
- Pass `DATABASE_URL` explicitly via env to avoid dotenv path issues

## Category Flow

1. `DEFAULT_CATEGORIES` in `models.py` is the source of truth for seed values
2. On startup `seed_categories()` inserts defaults if table is empty (sets `is_editable=False`)
3. On each sync, active categories (`is_active = true`) are fetched and passed to the LLM prompt as a constrained list
4. LLM must return one of these strings. On mismatch → falls back to `"Other"` category
5. Category resolution is case-insensitive, done via `func.lower()` in `main.py`
6. `is_editable=False` marks default categories the admin panel should not allow deleting

## Ruff config

Lint rules are under `[tool.ruff.lint]` (not the deprecated top-level keys). Settings:
- select: E, F, I, B — line-length: 88 — double quotes, spaces
- Auto-fix: `uv run ruff check --fix .`

## Scripts

All scripts in `scripts/` are run as modules:
```bash
uv run python -m scripts.<name> [args]
```
They load `.env` via `dotenv`, so must be run from the project root.
