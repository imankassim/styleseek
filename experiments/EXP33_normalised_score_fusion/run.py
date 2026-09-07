"""EXP33: normalised score fusion.

Fusion alternative (architecture §14) — min-max normalise BM25's and vector search's raw
scores independently into [0, 1], then sum (search/fusion.py:normalised_score_fusion), instead
of RRF's rank-only combination (EXP32). Motivated directly by EXP32's result: equal-weight rank
fusion improved recall@50 (0.707 vs BM25 alone 0.693) but regressed ndcg@10 badly (0.549 vs
0.755) — does preserving relative score *magnitude* (not just rank order) fix that, or is the
problem more fundamental (a much weaker semantic ranker dragging down a much stronger lexical
one, regardless of how they're combined)?
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "evaluation"))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "search"))
from metrics import evaluate, print_report  # noqa: E402
from opensearch_client import get_client  # noqa: E402
from hybrid_candidates import bm25_candidates, vector_candidates  # noqa: E402
from fusion import normalised_score_fusion  # noqa: E402

CANDIDATE_LIMIT = 50


def make_search_fn(client):
    def search(query: str) -> list[str]:
        bm25_scored = dict(bm25_candidates(client, query, CANDIDATE_LIMIT))
        vector_scored = dict(vector_candidates(client, query, "title_vector", CANDIDATE_LIMIT))
        return normalised_score_fusion([bm25_scored, vector_scored])

    return search


if __name__ == "__main__":
    client = get_client()
    search_fn = make_search_fn(client)
    rows, summary = evaluate(search_fn, splits=["train", "val"])
    print_report("EXP33 normalised score fusion (BM25 + title vector, train+val)", rows, summary)
