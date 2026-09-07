"""Unit tests for search/fusion.py — RRF calculation is explicitly named as a unit-test
example in architecture §15, verified against hand-computed values, not just internal
consistency (same standard as tests/unit/test_metrics.py)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "search"))

from fusion import (  # noqa: E402
    min_max_normalise,
    normalised_score_fusion,
    reciprocal_rank_fusion,
    weighted_score_fusion,
)


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


def test_min_max_normalise_hand_computed():
    # a=10 -> (10-0)/(20-0) = 0.5; b=0 -> 0.0; c=20 -> 1.0
    result = min_max_normalise({"a": 10.0, "b": 0.0, "c": 20.0})
    assert result == {"a": 0.5, "b": 0.0, "c": 1.0}


def test_min_max_normalise_empty_input():
    assert min_max_normalise({}) == {}


def test_min_max_normalise_all_equal_scores_become_one_not_nan():
    # Would divide by zero (hi == lo) without the guard.
    result = min_max_normalise({"a": 5.0, "b": 5.0})
    assert result == {"a": 1.0, "b": 1.0}


def test_min_max_normalise_single_document():
    assert min_max_normalise({"a": 3.7}) == {"a": 1.0}


def test_normalised_score_fusion_favours_doc_strong_in_both_lists():
    list1 = {"a": 10.0, "b": 1.0}  # normalised: a=1.0, b=0.0
    list2 = {"a": 8.0, "b": 1.0}  # normalised: a=1.0, b=0.0
    result = normalised_score_fusion([list1, list2])
    assert result[0] == "a"


def test_normalised_score_fusion_absent_document_contributes_zero_not_penalty():
    list1 = {"a": 10.0, "b": 5.0}
    list2 = {"a": 1.0}  # b absent here — contributes 0, not negative
    result = normalised_score_fusion([list1, list2])
    assert "b" in result


def test_weighted_score_fusion_hand_computed():
    # list1 normalised: a=1.0, b=0.0. list2 normalised: a=0.0, b=1.0.
    # weights [0.8, 0.2]: score(a) = 0.8*1.0 + 0.2*0.0 = 0.8; score(b) = 0.8*0.0 + 0.2*1.0 = 0.2
    list1 = {"a": 10.0, "b": 0.0}
    list2 = {"a": 0.0, "b": 10.0}
    result = weighted_score_fusion([list1, list2], weights=[0.8, 0.2])
    assert result == ["a", "b"]


def test_weighted_score_fusion_flips_winner_when_weights_flip():
    list1 = {"a": 10.0, "b": 0.0}
    list2 = {"a": 0.0, "b": 10.0}
    result = weighted_score_fusion([list1, list2], weights=[0.2, 0.8])
    assert result == ["b", "a"]


def test_weighted_score_fusion_rejects_mismatched_lengths():
    import pytest

    with pytest.raises(ValueError, match="same length"):
        weighted_score_fusion([{"a": 1.0}], weights=[0.5, 0.5])
