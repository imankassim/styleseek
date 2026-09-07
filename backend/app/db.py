"""Connection pool to PostgreSQL. No ORM yet (architecture: baseline first) — plain SQL via
psycopg, same as database/ingest.py, so the schema has one source of truth (the migrations)
rather than a second one implied by ORM models.

Sync pool, not async: uvicorn forces WindowsProactorEventLoopPolicy on Windows regardless of any
policy set before `uvicorn.run()`, and psycopg's async mode requires a selector-based loop —
there's no clean way to reconcile the two for local Windows dev. A sync pool sidesteps it
entirely; FastAPI runs sync (`def`, not `async def`) route handlers in a thread pool
automatically, so this doesn't block the event loop.
"""

from collections.abc import Iterator

from psycopg_pool import ConnectionPool

from app.config import get_database_url

pool: ConnectionPool | None = None


def open_pool() -> None:
    global pool  # noqa: PLW0603
    pool = ConnectionPool(conninfo=get_database_url(), open=True, min_size=1, max_size=5)


def close_pool() -> None:
    if pool is not None:
        pool.close()


def get_connection() -> Iterator:
    if pool is None:
        msg = "Connection pool not initialised — call open_pool() at startup."
        raise RuntimeError(msg)
    with pool.connection() as conn:
        yield conn
