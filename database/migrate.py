"""Minimal migration runner: applies database/migrations/*.sql in numeric order, tracking
what's already been applied in a schema_migrations table. No framework — the schema is small
and changes rarely enough at this stage that Alembic/SQLAlchemy migrations aren't justified yet
(architecture principle: baseline first, add complexity when evidence calls for it).
"""

import os
import re
import sys
from pathlib import Path

import psycopg

MIGRATIONS_DIR = Path(__file__).parent / "migrations"


def load_database_url() -> str:
    env_path = Path(__file__).parent / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            if line.startswith("DATABASE_URL="):
                return line.split("=", 1)[1].strip()
    url = os.environ.get("DATABASE_URL")
    if not url:
        msg = "DATABASE_URL not found in database/.env or the environment."
        raise RuntimeError(msg)
    return url


def migration_files() -> list[Path]:
    files = sorted(
        MIGRATIONS_DIR.glob("*.sql"),
        key=lambda p: int(re.match(r"(\d+)_", p.name).group(1)),
    )
    return files


def main() -> None:
    database_url = load_database_url()
    with psycopg.connect(database_url, autocommit=True) as conn, conn.cursor() as cur:
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS schema_migrations (
                filename    TEXT PRIMARY KEY,
                applied_at  TIMESTAMPTZ NOT NULL DEFAULT now()
            )
            """
        )
        cur.execute("SELECT filename FROM schema_migrations")
        applied = {row[0] for row in cur.fetchall()}

        for path in migration_files():
            if path.name in applied:
                print(f"skip  {path.name} (already applied)")
                continue
            print(f"apply {path.name}")
            sql = path.read_text(encoding="utf-8")
            cur.execute(sql)
            cur.execute("INSERT INTO schema_migrations (filename) VALUES (%s)", (path.name,))

    print("Migrations up to date.")


if __name__ == "__main__":
    sys.exit(main())
