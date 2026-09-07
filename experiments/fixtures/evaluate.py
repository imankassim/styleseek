"""Shared, deliberately minimal evaluation helper for the Stage 3 primitive-search
experiments (EXP1, EXP2). Not the Stage 8 evaluation harness (NDCG@10, Recall@50) —
those require the frozen labelled query set from G4 and are built in evaluation/.
"""

import json
from pathlib import Path

FIXTURE_PATH = Path(__file__).parent / "primitive_search_fixture.json"


def load_fixture():
    with open(FIXTURE_PATH, encoding="utf-8") as f:
        data = json.load(f)
    return data["products"], data["queries"]


def evaluate(search_fn, top_k=10):
    """search_fn(query: str, products: list[dict]) -> list[str] of product_id, ranked.

    Returns a list of per-query result dicts and a summary by query type.
    """
    products, queries = load_fixture()
    rows = []
    for q in queries:
        ranked_ids = search_fn(q["query"], products)[:top_k]
        expected = set(q["expected_relevant"])
        any_hit = any(pid in expected for pid in ranked_ids)
        top1_hit = len(ranked_ids) > 0 and ranked_ids[0] in expected
        correct_empty = len(expected) == 0 and len(ranked_ids) == 0
        rows.append(
            {
                "query_id": q["query_id"],
                "query": q["query"],
                "type": q["type"],
                "expected_relevant": sorted(expected),
                "returned": ranked_ids,
                "any_hit": any_hit or correct_empty,
                "top1_hit": top1_hit or correct_empty,
            }
        )

    by_type = {}
    for row in rows:
        bucket = by_type.setdefault(row["type"], {"n": 0, "any_hit": 0, "top1_hit": 0})
        bucket["n"] += 1
        bucket["any_hit"] += int(row["any_hit"])
        bucket["top1_hit"] += int(row["top1_hit"])

    overall = {
        "n": len(rows),
        "any_hit_rate": sum(r["any_hit"] for r in rows) / len(rows),
        "top1_hit_rate": sum(r["top1_hit"] for r in rows) / len(rows),
    }

    return rows, by_type, overall


def print_report(name, rows, by_type, overall):
    print(f"\n=== {name} ===")
    for row in rows:
        status = "HIT" if row["any_hit"] else "MISS"
        print(
            f"[{status:4}] {row['query_id']:4} ({row['type']:10}) "
            f"'{row['query']}' -> {row['returned']} (expected {row['expected_relevant']})"
        )
    print("\nBy query type (any_hit_rate):")
    for qtype, stats in sorted(by_type.items()):
        print(f"  {qtype:10} {stats['any_hit']}/{stats['n']}")
    print(
        f"\nOverall: any_hit_rate={overall['any_hit_rate']:.2f} "
        f"top1_hit_rate={overall['top1_hit_rate']:.2f} (n={overall['n']})"
    )
