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
    # check=check_connection validates a connection is actually alive before handing it out,
    # discarding and replacing it otherwise -- found necessary in practice (2026-09-08): Neon's
    # serverless Postgres can drop an idle pooled connection server-side faster than this pool's
    # own max_idle housekeeping notices, which without this check surfaced as an unhandled
    # psycopg.OperationalError deep inside a request handler (see the docstring on
    # _apply_eligibility_and_diversity's rollback try/except in routers/search.py, added at the
    # same time as defence in depth for the narrower race this doesn't close).
    pool = ConnectionPool(
        conninfo=get_database_url(),
        open=True,
        min_size=1,
        max_size=5,
        check=ConnectionPool.check_connection,
    )


def close_pool() -> None:
    if pool is not None:
        pool.close()


def get_connection() -> Iterator:
    if pool is None:
        msg = "Connection pool not initialised — call open_pool() at startup."
        raise RuntimeError(msg)
    with pool.connection() as conn:
        yield conn
