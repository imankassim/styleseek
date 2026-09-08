"""Unit tests for ml/learning_to_rank/features.py's build_feature_row — architecture §15 names
"feature generation" explicitly as a unit-test example. Only the pure row-building function is
covered here; build_feature_matrix/build_query_candidate_features need a live database and
OpenSearch — those are exercised indirectly by actually running the EXP40/41/43 scripts, not by
a mocked unit test that wouldn't catch a real integration problem.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "ml" / "learning_to_rank"))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "backend"))

from features import FEATURE_NAMES, ProductMeta, build_feature_row  # noqa: E402
from app.query_understanding import parse_query  # noqa: E402

SAMPLE_META = ProductMeta(
    category="dress",
    colours=["Red"],
    occasion="Party",
    gender="Women",
    price=42.16,
    in_stock=True,
)


def test_feature_row_length_matches_feature_names():
    parsed = parse_query("red dress")
    row = build_feature_row(parsed, SAMPLE_META, bm25_score=10.0, vector_score=0.8)
    assert len(row) == len(FEATURE_NAMES)


def test_raw_scores_pass_through_unchanged():
    parsed = parse_query("red dress")
    row = build_feature_row(parsed, SAMPLE_META, bm25_score=12.34, vector_score=0.567)
    assert row[FEATURE_NAMES.index("bm25_score")] == 12.34
    assert row[FEATURE_NAMES.index("vector_score")] == 0.567


def test_colour_match_true_when_parsed_colour_in_product_colours():
    parsed = parse_query("red dress")
    row = build_feature_row(parsed, SAMPLE_META, 0.0, 0.0)
    assert row[FEATURE_NAMES.index("colour_match")] == 1.0


def test_colour_match_false_when_colour_differs():
    parsed = parse_query("blue dress")
    row = build_feature_row(parsed, SAMPLE_META, 0.0, 0.0)
    assert row[FEATURE_NAMES.index("colour_match")] == 0.0


def test_colour_match_false_when_no_colour_in_query():
    parsed = parse_query("dress")
    row = build_feature_row(parsed, SAMPLE_META, 0.0, 0.0)
    assert row[FEATURE_NAMES.index("colour_match")] == 0.0


def test_category_match():
    parsed = parse_query("red dress")
    row = build_feature_row(parsed, SAMPLE_META, 0.0, 0.0)
    assert row[FEATURE_NAMES.index("category_match")] == 1.0

    other = ProductMeta(category="shoes", colours=["Red"], occasion=None, gender=None, price=10.0, in_stock=True)
    row2 = build_feature_row(parsed, other, 0.0, 0.0)
    assert row2[FEATURE_NAMES.index("category_match")] == 0.0


def test_under_max_price_true_when_no_price_constraint():
    parsed = parse_query("red dress")
    row = build_feature_row(parsed, SAMPLE_META, 0.0, 0.0)
    assert row[FEATURE_NAMES.index("under_max_price")] == 1.0


def test_under_max_price_respects_constraint():
    cheap = ProductMeta(category="dress", colours=["Red"], occasion=None, gender=None, price=20.0, in_stock=True)
    expensive = ProductMeta(category="dress", colours=["Red"], occasion=None, gender=None, price=100.0, in_stock=True)
    parsed = parse_query("red dress under £50")

    row_cheap = build_feature_row(parsed, cheap, 0.0, 0.0)
    row_expensive = build_feature_row(parsed, expensive, 0.0, 0.0)
    assert row_cheap[FEATURE_NAMES.index("under_max_price")] == 1.0
    assert row_expensive[FEATURE_NAMES.index("under_max_price")] == 0.0


def test_in_stock_reflects_meta():
    parsed = parse_query("red dress")
    in_stock = build_feature_row(parsed, SAMPLE_META, 0.0, 0.0)
    out_of_stock_meta = ProductMeta(
        category="dress", colours=["Red"], occasion=None, gender=None, price=42.16, in_stock=False
    )
    out_of_stock = build_feature_row(parsed, out_of_stock_meta, 0.0, 0.0)
    assert in_stock[FEATURE_NAMES.index("in_stock")] == 1.0
    assert out_of_stock[FEATURE_NAMES.index("in_stock")] == 0.0


def test_occasion_text_match_is_case_insensitive_substring():
    parsed = parse_query("party dress")
    row = build_feature_row(parsed, SAMPLE_META, 0.0, 0.0)
    assert row[FEATURE_NAMES.index("occasion_text_match")] == 1.0
