"""Loads DATABASE_URL from (in order): the environment, backend/.env, database/.env.

Falling back to database/.env means the same Neon connection string set up for ingestion
(database/ingest.py) doesn't need to be pasted a second time — both point at the same catalogue.
"""

import os
from pathlib import Path

BACKEND_DIR = Path(__file__).parent.parent
REPO_ROOT = BACKEND_DIR.parent


def _read_env_file(path: Path) -> str | None:
    if not path.exists():
        return None
    for line in path.read_text().splitlines():
        if line.startswith("DATABASE_URL="):
            value = line.split("=", 1)[1].strip()
            if value:
                return value
    return None


def get_database_url() -> str:
    if "DATABASE_URL" in os.environ and os.environ["DATABASE_URL"]:
        return os.environ["DATABASE_URL"]

    for candidate in (BACKEND_DIR / ".env", REPO_ROOT / "database" / ".env"):
        value = _read_env_file(candidate)
        if value:
            return value

    msg = "DATABASE_URL not set (checked env, backend/.env, database/.env)"
    raise RuntimeError(msg)
