"""Unit tests for search/fusion.py — RRF calculation is explicitly named as a unit-test
example in architecture §15, verified against hand-computed values, not just internal
consistency (same standard as tests/unit/test_metrics.py)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "search"))

from fusion import reciprocal_rank_fusion  # noqa: E402


def test_single_list_preserves_original_order():
    result = reciprocal_rank_fusion([["a", "b", "c"]])
    assert result == ["a", "b", "c"]


def test_hand_computed_two_list_fusion():
    # k=10 for readability. list1: a=1st(rank0), b=2nd(rank1). list2: b=1st(rank0), a=2nd(rank1).
    # score(a) = 1/(10+0) + 1/(10+1) = 0.1 + 0.090909... = 0.190909...
    # score(b) = 1/(10+1) + 1/(10+0) = same = 0.190909...  -> tie
    result = reciprocal_rank_fusion([["a", "b"], ["b", "a"]], k=10)
    assert set(result) == {"a", "b"}  # tie — order between them is not asserted


def test_document_ranked_first_in_both_lists_wins():
    # a is 1st in both lists; b is 2nd in both. a's score must exceed b's.
    result = reciprocal_rank_fusion([["a", "b"], ["a", "b"]], k=60)
    assert result == ["a", "b"]


def test_document_only_in_one_list_still_included():
    result = reciprocal_rank_fusion([["a", "b"], ["c"]])
    assert set(result) == {"a", "b", "c"}


def test_document_in_both_lists_outranks_document_in_only_one():
    # "shared" appears (lower) in both lists; "solo" is 1st in only one list.
    # score(shared) = 1/(60+1) + 1/(60+1) = 2/61 ≈ 0.0328
    # score(solo)   = 1/(60+0)            = 1/60  ≈ 0.0167
    result = reciprocal_rank_fusion([["solo", "shared"], ["x", "shared"]], k=60)
    assert result[0] == "shared"


def test_empty_lists_produce_empty_result():
    assert reciprocal_rank_fusion([[], []]) == []


def test_default_k_matches_rrf_paper_and_opensearch_default():
    from fusion import DEFAULT_K

    assert DEFAULT_K == 60
