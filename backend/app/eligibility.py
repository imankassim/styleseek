"""Stage 12: eligibility and diversity (architecture logical pipeline step 6, "ELIGIBILITY AND
DIVERSITY: Stock, size, category, price, duplicate control"). Stock/colour/gender/price/size-
offered are handled as index-level hard filters (app/opensearch.py); this module handles the
two things that need the live database or post-fusion candidate list: confirming a *specific*
requested size is actually in stock right now, and removing near-duplicate results.
"""

from collections.abc import Callable, Hashable
from typing import TypeVar

from psycopg import Connection

T = TypeVar("T")


def products_with_size_in_stock(conn: Connection, product_ids: list[str], size: str) -> set[str]:
    """The search index only tracks aggregate stock and which sizes a product has ever offered
    (app/opensearch.py's build_filters coarse pre-filter) — not per-size stock levels. This is
    the precise check, run only against the (small) already-ranked candidate set, not the whole
    catalogue.
    """
    if not product_ids:
        return set()
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT product_id FROM product_variant
            WHERE product_id = ANY(%s) AND size = %s AND stock_quantity > 0
            """,
            (product_ids, size),
        )
        return {row[0] for row in cur.fetchall()}


def deduplicate(items: list[T], key_fn: Callable[[T], Hashable]) -> list[T]:
    """Keeps the first (highest-ranked) occurrence of each key, in order. A "transparent rule"
    (architecture logical pipeline step 5) — simple, explainable, no learned weights — unlike
    Stage 13's LightGBM ranker, which comes later and only after there's enough labelled data
    to justify it.
    """
    seen: set[Hashable] = set()
    result: list[T] = []
    for item in items:
        key = key_fn(item)
        if key in seen:
            continue
        seen.add(key)
        result.append(item)
    return result
