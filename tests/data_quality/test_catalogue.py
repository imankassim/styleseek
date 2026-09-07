"""Data quality gates for the ingested catalogue (architecture §8.3). Run against the live
database — not mocked — because these checks exist to catch bad *data*, not bad code.

Run: python -m pytest tests/data_quality/test_catalogue.py
Requires database/.env with DATABASE_URL set (see database/ingest.py).
"""

from pathlib import Path

import psycopg
import pytest


def load_database_url() -> str:
    env_path = Path(__file__).parent.parent.parent / "database" / ".env"
    for line in env_path.read_text().splitlines():
        if line.startswith("DATABASE_URL="):
            return line.split("=", 1)[1].strip()
    msg = "DATABASE_URL not found in database/.env"
    raise RuntimeError(msg)


@pytest.fixture(scope="module")
def conn():
    with psycopg.connect(load_database_url()) as connection:
        yield connection


def test_product_ids_unique_and_non_null(conn):
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*), COUNT(DISTINCT product_id) FROM product")
        total, distinct = cur.fetchone()
    assert total == distinct, "duplicate product_id values found"
    assert total > 0, "product table is empty"


def test_price_non_negative(conn):
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM product WHERE price < 0 OR price IS NULL")
        (bad,) = cur.fetchone()
    assert bad == 0, f"{bad} products have a negative or missing price"


def test_stock_non_negative(conn):
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM product_variant WHERE stock_quantity < 0")
        (bad,) = cur.fetchone()
    assert bad == 0, f"{bad} variants have negative stock"


def test_every_variant_references_a_real_product(conn):
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT COUNT(*) FROM product_variant v
            LEFT JOIN product p ON p.product_id = v.product_id
            WHERE p.product_id IS NULL
            """
        )
        (orphans,) = cur.fetchone()
    assert orphans == 0, f"{orphans} variants reference a non-existent product"


def test_every_product_has_at_least_one_variant(conn):
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT COUNT(*) FROM product p
            LEFT JOIN product_variant v ON v.product_id = p.product_id
            WHERE v.variant_id IS NULL
            """
        )
        (orphans,) = cur.fetchone()
    assert orphans == 0, f"{orphans} products have no variant at all"


def test_category_is_non_empty(conn):
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM product WHERE category IS NULL OR category = ''")
        (bad,) = cur.fetchone()
    assert bad == 0, f"{bad} products have an empty category"


def test_synthetic_fields_are_flagged(conn):
    """Every row currently in the catalogue came from synthetic price/variant generation
    (database/ingest.py) — the flags must say so, per the data sheet's labelling requirement."""
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM product WHERE is_synthetic_price IS NOT TRUE")
        (bad_products,) = cur.fetchone()
        cur.execute("SELECT COUNT(*) FROM product_variant WHERE is_synthetic_variant IS NOT TRUE")
        (bad_variants,) = cur.fetchone()
    assert bad_products == 0, f"{bad_products} products with synthetic price not flagged as such"
    assert bad_variants == 0, f"{bad_variants} variants with synthetic data not flagged as such"
