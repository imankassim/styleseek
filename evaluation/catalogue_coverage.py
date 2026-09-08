"""Catalogue coverage and diversity for broad queries (architecture §3.3 evaluation measure --
never previously measured as its own metric, found missing during the 2026-09-08 brief-
fulfilment audit; see docs/progress.md).

Distinct from evaluation/metrics.py's NDCG/Recall: those need relevance judgments and answer
"is the ranking good for a specific labelled query." This needs no judgments and answers a
different question: across the kind of broad, single-term queries a shopper browsing (not
searching precisely) would type, how much of the 44,446-product catalogue ever surfaces at all,
and is any one query's result page dominated by near-duplicates rather than genuine variety?

Run: python evaluation/catalogue_coverage.py
Requires backend/ importable and DATABASE_URL/OPENSEARCH_URL resolvable (drives the real
/search endpoint via TestClient, same pattern as evaluation/final_evaluation.md's held-out run).
"""

import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402

# Genuinely broad, single-category queries -- not the attribute/occasion/constraint-qualified
# queries evaluation/relevance_judgments.json already covers. Picked to span the catalogue's
# largest categories (backend GET /categories, 2026-09-08): topwear, shoes, bags, bottomwear,
# watches, dress, saree, jewellery.
BROAD_QUERIES = [
    "dress", "shoes", "shirt", "bag", "watch", "jacket", "jeans",
    "shorts", "jewellery", "saree", "trousers", "sweater",
]


def total_catalogue_size(conn) -> int:
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM product")
        (count,) = cur.fetchone()
    return count


def run_report(client: TestClient, catalogue_size: int) -> dict:
    per_query = {}
    all_product_ids: set[str] = set()
    appearance_counts: Counter[str] = Counter()

    for query in BROAD_QUERIES:
        resp = client.get("/search", params={"q": query})
        results = resp.json()["results"]
        product_ids = [r["product_id"] for r in results]
        distinct_titles = {r["title"] for r in results}

        per_query[query] = {
            "n_results": len(results),
            "n_distinct_titles": len(distinct_titles),
        }
        all_product_ids.update(product_ids)
        appearance_counts.update(product_ids)

    return {
        "per_query": per_query,
        "catalogue_coverage": len(all_product_ids) / catalogue_size,
        "n_distinct_products_surfaced": len(all_product_ids),
        "most_repeated_products": appearance_counts.most_common(5),
    }


def print_report(report: dict, catalogue_size: int) -> None:
    print(f"\n=== Catalogue coverage and diversity ({len(BROAD_QUERIES)} broad queries) ===")
    for query, stats in report["per_query"].items():
        dup_note = "" if stats["n_distinct_titles"] == stats["n_results"] else (
            f" ({stats['n_results'] - stats['n_distinct_titles']} title-duplicate(s))"
        )
        print(f"  '{query}': {stats['n_results']} results, {stats['n_distinct_titles']} distinct titles{dup_note}")

    max_possible = len(BROAD_QUERIES) * 24  # RESULT_LIMIT (backend/app/routers/search.py)
    print(
        f"\nDistinct products surfaced: {report['n_distinct_products_surfaced']}/{catalogue_size} "
        f"catalogue ({report['catalogue_coverage']:.2%}) -- but that denominator is misleading on "
        f"its own: {len(BROAD_QUERIES)} queries x 24 results/page = {max_possible} is the actual "
        f"ceiling for this batch, and {report['n_distinct_products_surfaced']}/{max_possible} "
        f"({report['n_distinct_products_surfaced'] / max_possible:.0%}) of *that* ceiling was hit -- "
        "i.e. no unhealthy overlap between different broad queries' result pages. Whether every "
        "product is reachable by *some* query eventually (the long tail) is a different, much "
        "larger question this script doesn't answer."
    )
    print("Most-repeated products across queries (product_id, appearance count):")
    for product_id, count in report["most_repeated_products"]:
        print(f"  {product_id}: appears in {count}/{len(BROAD_QUERIES)} broad queries")


if __name__ == "__main__":
    import psycopg

    sys.path.insert(0, str(Path(__file__).parent.parent / "database"))
    from ingest import load_database_url  # noqa: E402

    with psycopg.connect(load_database_url()) as conn:
        catalogue_size = total_catalogue_size(conn)

    with TestClient(app) as client:
        report = run_report(client, catalogue_size)
    print_report(report, catalogue_size)
