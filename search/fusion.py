"""Reciprocal Rank Fusion (architecture §14 EXP32, the rank-fusion baseline for Stage 11's
hybrid retrieval). Combines multiple independently-ranked candidate lists (e.g. lexical BM25 +
semantic vector) using only rank position, not raw scores — avoids the score-normalisation
problem of combining two systems whose scores live on totally different scales (BM25's
unbounded relevance score vs cosine similarity's [-1, 1]).

score(d) = sum over each ranked list L containing d of  1 / (k + rank_L(d))

rank is 0-indexed internally (the top result contributes 1/(k+0)); k=60 is the constant from the
original RRF paper (Cormack, Clarke & Buettcher 2009) and OpenSearch's own default — kept as the
default here rather than re-deriving it without evidence that a different value helps.
"""

DEFAULT_K = 60


def reciprocal_rank_fusion(
    ranked_lists: list[list[str]], k: int = DEFAULT_K
) -> list[str]:
    """ranked_lists: e.g. [bm25_result_ids, vector_result_ids] — each already ranked, best
    first. A document need not appear in every list. Returns a single fused ranking, best first.
    """
    scores: dict[str, float] = {}
    for ranked_list in ranked_lists:
        for rank, doc_id in enumerate(ranked_list):
            scores[doc_id] = scores.get(doc_id, 0.0) + 1.0 / (k + rank)

    return sorted(scores.keys(), key=lambda doc_id: scores[doc_id], reverse=True)
