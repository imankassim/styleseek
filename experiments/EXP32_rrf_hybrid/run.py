"""EXP32: RRF hybrid retrieval.

Rank-fusion baseline (architecture §14) — combines EXP31 (BM25/EXP14) and EXP30 (vector,
title-only embeddings) candidate lists via Reciprocal Rank Fusion (search/fusion.py), the
architecture's stated starting point for hybrid retrieval (ADR-1). Chosen over a raw score sum
specifically because BM25's unbounded score and cosine similarity's bounded [-1, 1] score live on
incomparable scales — RRF sidesteps that by using rank position only.
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "evaluation"))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "search"))
from metrics import evaluate, print_report  # noqa: E402
from opensearch_client import get_client  # noqa: E402
from hybrid_candidates import bm25_candidates, vector_candidates  # noqa: E402
from fusion import reciprocal_rank_fusion  # noqa: E402

CANDIDATE_LIMIT = 50


def make_search_fn(client):
    def search(query: str) -> list[str]:
        bm25_ids = [pid for pid, _score in bm25_candidates(client, query, CANDIDATE_LIMIT)]
        vector_ids = [pid for pid, _score in vector_candidates(client, query, "title_vector", CANDIDATE_LIMIT)]
        return reciprocal_rank_fusion([bm25_ids, vector_ids])

    return search


def measure_latency(client, queries: list[str]) -> dict:
    latencies_ms = []
    for query in queries:
        started = time.perf_counter()
        make_search_fn(client)(query)
        latencies_ms.append((time.perf_counter() - started) * 1000)
    latencies_ms.sort()
    n = len(latencies_ms)
    return {
        "median_ms": latencies_ms[n // 2],
        "p95_ms": latencies_ms[min(n - 1, int(n * 0.95))],
    }


if __name__ == "__main__":
    client = get_client()
    search_fn = make_search_fn(client)
    rows, summary = evaluate(search_fn, splits=["train", "val"])
    print_report("EXP32 RRF hybrid (BM25 + title vector, train+val)", rows, summary)

    sample_queries = ["black nike shoes", "red dress", "green saree", "smart casual blazer", "sports watch"]
    latency = measure_latency(client, sample_queries)
    print(f"\nLatency over {len(sample_queries)} sample queries: "
          f"median={latency['median_ms']:.0f}ms p95={latency['p95_ms']:.0f}ms "
          f"(architecture §17 G7: 'without unacceptable latency')")
