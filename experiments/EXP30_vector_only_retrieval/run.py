"""EXP30: vector-only retrieval — the semantic baseline (architecture §14).

Uses EXP22's winning representation (title-only embeddings). This script exists to answer the
actual G6 gate question (architecture §17): "Does vector retrieval add useful candidates? Wins
and failures are measured by query type." — not "is vector-only a better ranker than BM25 alone"
(EXP22's README already shows it isn't, and that's expected, not a failure). Compares, per
query, whether vector search surfaces any graded-relevant (grade >= 2) product that EXP31's BM25
(EXP14's config) misses entirely from its own top-50.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "evaluation"))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "search"))
sys.path.insert(0, str(Path(__file__).parent.parent / "EXP14_synonym_expansion"))
from metrics import evaluate, load_judgments, print_report  # noqa: E402
from opensearch_client import get_client  # noqa: E402
from vector_search import make_vector_search_fn  # noqa: E402
from synonym_mapping import INDEX_NAME as BM25_INDEX  # noqa: E402

BM25_BOOSTED_FIELDS = ["title^3", "category_text^2", "colours_text^2", "occasion^1", "brand^1"]
RELEVANCE_THRESHOLD = 2


def make_bm25_search_fn(client, limit: int = 50):
    def search(query: str) -> list[str]:
        resp = client.search(
            index=BM25_INDEX,
            body={
                "query": {
                    "multi_match": {"query": query, "type": "cross_fields", "fields": BM25_BOOSTED_FIELDS}
                },
                "size": limit,
            },
        )
        return [hit["_source"]["product_id"] for hit in resp["hits"]["hits"]]

    return search


def complementary_candidates_report(client) -> None:
    vector_search = make_vector_search_fn(client, "title_vector")
    bm25_search = make_bm25_search_fn(client)

    queries = load_judgments(splits=["train", "val"])
    total_found = 0
    queries_with_wins = 0

    print("\n=== G6 evidence: does vector retrieval add candidates BM25 (EXP14/31) misses? ===")
    for q in queries:
        relevant = {p["product_id"] for p in q["graded_products"] if p["grade"] >= RELEVANCE_THRESHOLD}
        if not relevant:
            continue

        bm25_ids = set(bm25_search(q["query"]))
        vector_ids = set(vector_search(q["query"]))
        vector_only_wins = relevant & vector_ids - bm25_ids

        if vector_only_wins:
            queries_with_wins += 1
            total_found += len(vector_only_wins)
            print(
                f"  {q['query_id']:5} '{q['query']}': vector found "
                f"{len(vector_only_wins)} relevant doc(s) BM25's top-50 missed entirely: "
                f"{sorted(vector_only_wins)}"
            )

    print(
        f"\n{queries_with_wins}/{len(queries)} queries had at least one relevant candidate "
        f"only vector search found; {total_found} such candidates total."
    )


if __name__ == "__main__":
    client = get_client()

    search_fn = make_vector_search_fn(client, "title_vector")
    rows, summary = evaluate(search_fn, splits=["train", "val"])
    print_report("EXP30 vector-only retrieval (title embeddings, train+val)", rows, summary)

    complementary_candidates_report(client)
