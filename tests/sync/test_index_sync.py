"""Sync tests (architecture §15 "Search regression"/"Data quality" spirit, risk register
"Index staleness" — open until this stage): confirms the OpenSearch indices actually reflect
the current Postgres source of truth, rather than assuming a past `python search/index.py` run
is still accurate.

These catch a class of bug none of the other suites do: everything (schema, code, API contract)
can be correct and the *served* index can still be stale, because index.py/index_vectors.py are
separate manual scripts, not triggered automatically by a catalogue write. There is no live sync
pipeline yet (that's still an open item, not something this test can fix) -- this test's job is
to make staleness *visible* rather than silent.

Run: python -m pytest tests/sync/test_index_sync.py
Requires database/.env with DATABASE_URL and OPENSEARCH_URL set.
"""

import sys
from pathlib import Path

import psycopg
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "search"))
from opensearch_client import get_client  # noqa: E402

REPO_ROOT = Path(__file__).parent.parent.parent
BM25_INDEX = "styleseek_products_v2_synonyms"  # backend/app/opensearch.py INDEX_NAME
VECTOR_INDEX = "styleseek_products_v3_vectors"  # backend/app/semantic.py VECTOR_INDEX_NAME


def load_database_url() -> str:
    env_path = REPO_ROOT / "database" / ".env"
    for line in env_path.read_text().splitlines():
        if line.startswith("DATABASE_URL="):
            return line.split("=", 1)[1].strip()
    msg = "DATABASE_URL not found in database/.env"
    raise RuntimeError(msg)


@pytest.fixture(scope="module")
def conn():
    with psycopg.connect(load_database_url()) as connection:
        yield connection


@pytest.fixture(scope="module")
def client():
    return get_client()


def _postgres_product_count(conn) -> int:
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM product")
        (count,) = cur.fetchone()
    return count


def test_bm25_index_document_count_matches_postgres(conn, client):
    pg_count = _postgres_product_count(conn)
    client.indices.refresh(index=BM25_INDEX)
    os_count = client.count(index=BM25_INDEX)["count"]
    assert os_count == pg_count, (
        f"{BM25_INDEX} has {os_count} documents but Postgres has {pg_count} products — "
        "the live index is stale. Rebuild with `python search/index.py` then "
        "`python experiments/EXP14_synonym_expansion/run.py`."
    )


def test_vector_index_document_count_matches_postgres(conn, client):
    pg_count = _postgres_product_count(conn)
    client.indices.refresh(index=VECTOR_INDEX)
    os_count = client.count(index=VECTOR_INDEX)["count"]
    assert os_count == pg_count, (
        f"{VECTOR_INDEX} has {os_count} documents but Postgres has {pg_count} products — "
        "the live vector index is stale. Rebuild with `python search/index_vectors.py` "
        "(budget ~80 minutes for the full catalogue)."
    )


def test_bm25_index_reflects_current_product_data(conn, client):
    """Spot-checks a random sample: even if the *count* matches, an individual product's
    row could have been edited (price, stock, colours) since the index was last built.
    search/index.py stamps every document with `source_version` (the product's
    updated_at, as an epoch) for exactly this check -- a mismatch means that document is stale,
    not missing."""
    with conn.cursor() as cur:
        cur.execute(
            "SELECT product_id, extract(epoch from updated_at)::bigint FROM product ORDER BY random() LIMIT 25"
        )
        sample = cur.fetchall()

    stale = []
    for product_id, current_version in sample:
        doc = client.get(index=BM25_INDEX, id=product_id, ignore=[404])
        if not doc.get("found"):
            stale.append((product_id, "missing from index"))
            continue
        indexed_version = doc["_source"].get("source_version")
        if indexed_version != current_version:
            stale.append((product_id, f"indexed version {indexed_version} != current {current_version}"))

    assert not stale, f"{len(stale)}/{len(sample)} sampled products are stale in {BM25_INDEX}: {stale}"
