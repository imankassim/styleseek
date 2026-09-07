"""NDCG@10 and Recall@50 (architecture §3.3), computed against the labelled query set
(relevance_judgments.json). Deliberately small and dependency-free — no ranking-metrics library,
since these two formulas are simple enough to implement directly and verify by hand.
"""

import json
import math
from pathlib import Path

JUDGMENTS_PATH = Path(__file__).parent / "relevance_judgments.json"

RECALL_RELEVANCE_THRESHOLD = 2  # grade >= this counts as "relevant" for Recall (rubric: 2 = Relevant)


def load_judgments(splits: list[str] | None = None) -> list[dict]:
    data = json.loads(JUDGMENTS_PATH.read_text(encoding="utf-8"))
    queries = data["queries"]
    if splits is not None:
        queries = [q for q in queries if q["split"] in splits]
    return queries


def dcg_at_k(grades: list[int], k: int) -> float:
    return sum(grade / math.log2(i + 2) for i, grade in enumerate(grades[:k]))


def ndcg_at_k(ranked_product_ids: list[str], graded_products: list[dict], k: int = 10) -> float:
    """graded_products: [{"product_id": ..., "grade": 0-3}, ...]. Ungraded products in the
    ranking are treated as grade 0 (not excluded) — an unlabelled result is not assumed
    relevant just because it wasn't in the judgment set.
    """
    grade_by_id = {p["product_id"]: p["grade"] for p in graded_products}
    achieved_grades = [grade_by_id.get(pid, 0) for pid in ranked_product_ids[:k]]
    dcg = dcg_at_k(achieved_grades, k)

    ideal_grades = sorted((p["grade"] for p in graded_products), reverse=True)
    idcg = dcg_at_k(ideal_grades, k)

    if idcg == 0:
        # No relevant products exist for this query (e.g. a no-result query) — a perfect
        # result is an empty/irrelevant ranking, which trivially has ndcg 1.0 by convention.
        return 1.0 if dcg == 0 else 0.0

    return dcg / idcg


def recall_at_k(ranked_product_ids: list[str], graded_products: list[dict], k: int = 50) -> float:
    relevant_ids = {p["product_id"] for p in graded_products if p["grade"] >= RECALL_RELEVANCE_THRESHOLD}
    if not relevant_ids:
        # No relevant products exist (no-result query) — recall is trivially 1.0 if nothing
        # irrelevant-but-labelled-relevant was missed (there was nothing to find).
        return 1.0

    retrieved_top_k = set(ranked_product_ids[:k])
    return len(relevant_ids & retrieved_top_k) / len(relevant_ids)


def evaluate(search_fn, splits: list[str] | None = None, k_ndcg: int = 10, k_recall: int = 50):
    """search_fn(query: str) -> list[str] of product_id, ranked.

    Returns (rows, summary) where rows is one dict per query and summary aggregates by split
    and by query type.
    """
    queries = load_judgments(splits)
    rows = []

    for q in queries:
        ranked_ids = search_fn(q["query"])
        ndcg = ndcg_at_k(ranked_ids, q["graded_products"], k=k_ndcg)
        recall = recall_at_k(ranked_ids, q["graded_products"], k=k_recall)
        rows.append(
            {
                "query_id": q["query_id"],
                "query": q["query"],
                "type": q["type"],
                "split": q["split"],
                "ndcg": ndcg,
                "recall": recall,
                "n_ranked": len(ranked_ids),
            }
        )

    def summarise(key):
        buckets: dict[str, list[dict]] = {}
        for row in rows:
            buckets.setdefault(row[key], []).append(row)
        return {
            bucket: {
                "n": len(bucket_rows),
                "mean_ndcg": sum(r["ndcg"] for r in bucket_rows) / len(bucket_rows),
                "mean_recall": sum(r["recall"] for r in bucket_rows) / len(bucket_rows),
            }
            for bucket, bucket_rows in buckets.items()
        }

    summary = {
        "overall": {
            "n": len(rows),
            "mean_ndcg": sum(r["ndcg"] for r in rows) / len(rows) if rows else 0.0,
            "mean_recall": sum(r["recall"] for r in rows) / len(rows) if rows else 0.0,
        },
        "by_type": summarise("type"),
        "by_split": summarise("split"),
    }

    return rows, summary


def print_report(name: str, rows: list[dict], summary: dict) -> None:
    print(f"\n=== {name} ===")
    for row in rows:
        print(
            f"  {row['query_id']:5} ({row['type']:10} {row['split']:5}) ndcg={row['ndcg']:.2f} "
            f"recall={row['recall']:.2f}  '{row['query']}'"
        )
    print("\nBy type:")
    for qtype, stats in sorted(summary["by_type"].items()):
        print(f"  {qtype:10} n={stats['n']:2}  ndcg={stats['mean_ndcg']:.3f}  recall={stats['mean_recall']:.3f}")
    overall = summary["overall"]
    print(
        f"\nOverall: ndcg@10={overall['mean_ndcg']:.3f}  recall@50={overall['mean_recall']:.3f}  (n={overall['n']})"
    )
