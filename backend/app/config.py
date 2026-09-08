"""Loads DATABASE_URL/OPENSEARCH_URL from (in order): the environment, backend/.env,
database/.env.

Falling back to database/.env means the same Neon/Bonsai credentials set up for ingestion
(database/ingest.py, search/index.py) don't need to be pasted a second time.
"""

import os
from pathlib import Path

BACKEND_DIR = Path(__file__).parent.parent
REPO_ROOT = BACKEND_DIR.parent


def _read_env_file(path: Path, prefix: str) -> str | None:
    if not path.exists():
        return None
    for line in path.read_text().splitlines():
        if line.startswith(prefix):
            value = line.split("=", 1)[1].strip()
            if value:
                return value
    return None


def get_database_url() -> str:
    if "DATABASE_URL" in os.environ and os.environ["DATABASE_URL"]:
        return os.environ["DATABASE_URL"]

    for candidate in (BACKEND_DIR / ".env", REPO_ROOT / "database" / ".env"):
        value = _read_env_file(candidate, "DATABASE_URL=")
        if value:
            return value

    msg = "DATABASE_URL not set (checked env, backend/.env, database/.env)"
    raise RuntimeError(msg)


def get_opensearch_url() -> str | None:
    """None (not raised) if unset — OpenSearch is allowed to be unavailable; callers fall back
    to the Postgres placeholder search (architecture §10, "OpenSearch unavailable")."""
    if "OPENSEARCH_URL" in os.environ and os.environ["OPENSEARCH_URL"]:
        return os.environ["OPENSEARCH_URL"]

    for candidate in (BACKEND_DIR / ".env", REPO_ROOT / "database" / ".env"):
        value = _read_env_file(candidate, "OPENSEARCH_URL=")
        if value:
            return value

    return None


DEFAULT_CORS_ORIGINS = ["http://localhost:3000"]


def get_cors_origins() -> list[str]:
    """Comma-separated CORS_ORIGINS env var (e.g. the deployed frontend's real origin);
    defaults to the local Next.js dev server so `python backend/run.py` keeps working
    unconfigured (architecture §15 containers/deployment — see app/main.py)."""
    raw = os.environ.get("CORS_ORIGINS", "").strip()
    if not raw:
        return DEFAULT_CORS_ORIGINS
    return [origin.strip() for origin in raw.split(",") if origin.strip()]
