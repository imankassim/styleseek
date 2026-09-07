"""Weighted score fusion — the winning config from EXP34 (search/fusion.py, Stage 11).
Duplicated here (not imported from search/) to keep backend/'s runtime self-contained, same
reasoning as app/opensearch.py duplicating the BM25 index config rather than importing it.
Algorithm and behaviour must stay identical to search/fusion.py — tests/unit/test_fusion.py
covers the algorithm itself; tests/integration/test_api_contract.py covers this copy through
the live endpoint.
"""

LEXICAL_WEIGHT = 0.9
SEMANTIC_WEIGHT = 0.1


def _min_max_normalise(scored: dict[str, float]) -> dict[str, float]:
    if not scored:
        return {}
    values = list(scored.values())
    lo, hi = min(values), max(values)
    if hi == lo:
        return dict.fromkeys(scored, 1.0)
    return {doc_id: (score - lo) / (hi - lo) for doc_id, score in scored.items()}


def weighted_score_fusion(
    lexical_scores: dict[str, float],
    semantic_scores: dict[str, float],
    lexical_weight: float = LEXICAL_WEIGHT,
    semantic_weight: float = SEMANTIC_WEIGHT,
) -> list[str]:
    combined: dict[str, float] = {}
    for doc_id, score in _min_max_normalise(lexical_scores).items():
        combined[doc_id] = combined.get(doc_id, 0.0) + lexical_weight * score
    for doc_id, score in _min_max_normalise(semantic_scores).items():
        combined[doc_id] = combined.get(doc_id, 0.0) + semantic_weight * score
    return sorted(combined.keys(), key=lambda doc_id: combined[doc_id], reverse=True)
