"""EXP34: weighted score fusion.

Fusion alternative (architecture §14) — like EXP33, but BM25's normalised score is weighted
above vector's before summing (search/fusion.py:weighted_score_fusion), rather than trusting
both equally. Motivated by EXP32/33: BM25 alone (EXP14, ndcg@10 0.755) is a much stronger
overall ranker than vector alone (EXP30, 0.293), so treating them as equally-weighted evidence
(EXP33: 0.673) demonstrably drags the fused ranking down from what BM25 achieves by itself.
Sweeps a few lexical/semantic weight splits to find where recall improves over BM25-alone
without giving back its ndcg advantage.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "evaluation"))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "search"))
from metrics import evaluate, print_report  # noqa: E402
from opensearch_client import get_client  # noqa: E402
from hybrid_candidates import bm25_candidates, vector_candidates  # noqa: E402
from fusion import weighted_score_fusion  # noqa: E402

CANDIDATE_LIMIT = 50
WEIGHT_SPLITS = [(0.9, 0.1), (0.8, 0.2), (0.7, 0.3)]


def make_search_fn(client, lexical_weight: float, semantic_weight: float):
    def search(query: str) -> list[str]:
        bm25_scored = dict(bm25_candidates(client, query, CANDIDATE_LIMIT))
        vector_scored = dict(vector_candidates(client, query, "title_vector", CANDIDATE_LIMIT))
        return weighted_score_fusion([bm25_scored, vector_scored], weights=[lexical_weight, semantic_weight])

    return search


if __name__ == "__main__":
    client = get_client()
    for lexical_weight, semantic_weight in WEIGHT_SPLITS:
        search_fn = make_search_fn(client, lexical_weight, semantic_weight)
        rows, summary = evaluate(search_fn, splits=["train", "val"])
        print_report(
            f"EXP34 weighted fusion lexical={lexical_weight} semantic={semantic_weight} (train+val)",
            rows,
            summary,
        )
