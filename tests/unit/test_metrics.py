"""Unit tests for evaluation/metrics.py — verified against hand-computed NDCG/Recall values,
not just internal consistency, since these numbers will be used to justify real decisions
(architecture §17 gate G5/G6/G7 all depend on them being correct)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "evaluation"))
from metrics import dcg_at_k, ndcg_at_k, recall_at_k  # noqa: E402


def test_dcg_at_k_hand_computed():
    # DCG = 3/log2(2) + 2/log2(3) + 0/log2(4) = 3.0 + 1.2618... = 4.2618...
    grades = [3, 2, 0]
    assert abs(dcg_at_k(grades, k=3) - 4.2618595071429145) < 1e-9


def test_dcg_at_k_truncates_at_k():
    assert dcg_at_k([3, 3, 3, 3], k=2) == dcg_at_k([3, 3], k=2)


def test_ndcg_perfect_ranking_is_one():
    graded = [{"product_id": "a", "grade": 3}, {"product_id": "b", "grade": 2}, {"product_id": "c", "grade": 1}]
    assert ndcg_at_k(["a", "b", "c"], graded, k=10) == 1.0


def test_ndcg_reversed_ranking_is_less_than_one():
    graded = [{"product_id": "a", "grade": 3}, {"product_id": "b", "grade": 2}, {"product_id": "c", "grade": 1}]
    score = ndcg_at_k(["c", "b", "a"], graded, k=10)
    assert 0 < score < 1.0


def test_ndcg_unranked_products_treated_as_grade_zero():
    graded = [{"product_id": "a", "grade": 3}]
    # "a" never appears in the ranking at all -> dcg 0 -> ndcg 0
    assert ndcg_at_k(["z", "y", "x"], graded, k=10) == 0.0


def test_ndcg_no_result_query_with_empty_ranking_is_perfect():
    assert ndcg_at_k([], [], k=10) == 1.0


def test_ndcg_no_result_query_stays_perfect_even_if_system_returns_junk():
    # Standard NDCG convention: with no graded-relevant products at all, both DCG and IDCG are
    # 0 by construction, and this is treated as trivially perfect (1.0) regardless of what was
    # actually returned — NDCG only scores the ranking of *graded* items, it doesn't penalise
    # showing ungraded ones. Catching "the system returned junk for a no-result query" is what
    # the separate no-result-rate metric (architecture §3.3) is for, not NDCG.
    assert ndcg_at_k(["z", "y"], [], k=10) == 1.0


def test_recall_finds_all_relevant_in_top_k():
    graded = [
        {"product_id": "a", "grade": 3},
        {"product_id": "b", "grade": 2},
        {"product_id": "c", "grade": 0},  # below relevance threshold, doesn't count
    ]
    assert recall_at_k(["a", "b", "x", "y"], graded, k=50) == 1.0


def test_recall_partial():
    graded = [{"product_id": "a", "grade": 3}, {"product_id": "b", "grade": 3}]
    # only "a" retrieved, "b" missed
    assert recall_at_k(["a", "x", "y"], graded, k=50) == 0.5


def test_recall_respects_k_cutoff():
    graded = [{"product_id": "a", "grade": 3}]
    # "a" is relevant but ranked beyond k=2
    assert recall_at_k(["x", "y", "a"], graded, k=2) == 0.0


def test_recall_no_relevant_products_is_trivially_one():
    assert recall_at_k(["x", "y"], [], k=50) == 1.0
