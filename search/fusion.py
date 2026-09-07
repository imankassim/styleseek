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


def min_max_normalise(scored: dict[str, float]) -> dict[str, float]:
    """Rescales raw scores from one retrieval method into [0, 1] so they're comparable across
    methods whose raw scales differ wildly (BM25: unbounded, typically single digits to tens;
    cosine similarity: bounded [-1, 1]) — the prerequisite for EXP33 (normalised score fusion)
    and EXP34 (weighted score fusion), neither of which is safe to do on raw scores directly.
    """
    if not scored:
        return {}
    values = list(scored.values())
    lo, hi = min(values), max(values)
    if hi == lo:
        # Every document scored identically (including the single-document case) — there's no
        # relative signal to preserve, so treat them as equally, maximally relevant rather than
        # dividing by zero.
        return dict.fromkeys(scored, 1.0)
    return {doc_id: (score - lo) / (hi - lo) for doc_id, score in scored.items()}


def normalised_score_fusion(scored_lists: list[dict[str, float]]) -> list[str]:
    """EXP33: min-max normalise each list's scores independently, then sum. A document absent
    from a list contributes 0 for that list, not a penalty beyond that."""
    combined: dict[str, float] = {}
    for scored in scored_lists:
        normalised = min_max_normalise(scored)
        for doc_id, score in normalised.items():
            combined[doc_id] = combined.get(doc_id, 0.0) + score
    return sorted(combined.keys(), key=lambda doc_id: combined[doc_id], reverse=True)


def weighted_score_fusion(scored_lists: list[dict[str, float]], weights: list[float]) -> list[str]:
    """EXP34: like normalised_score_fusion, but each list's normalised score is scaled by an
    explicit weight before summing — e.g. weighting lexical evidence above semantic, or vice
    versa, rather than trusting them equally by default."""
    if len(scored_lists) != len(weights):
        msg = "scored_lists and weights must be the same length"
        raise ValueError(msg)

    combined: dict[str, float] = {}
    for scored, weight in zip(scored_lists, weights, strict=True):
        normalised = min_max_normalise(scored)
        for doc_id, score in normalised.items():
            combined[doc_id] = combined.get(doc_id, 0.0) + weight * score
    return sorted(combined.keys(), key=lambda doc_id: combined[doc_id], reverse=True)
