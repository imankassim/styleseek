"""Unit tests for backend/app/query_understanding.py — architecture §15 names "price
extraction, colour mapping" explicitly as unit test examples."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "backend"))

from app.query_understanding import parse_query  # noqa: E402


def test_price_extraction_under():
    assert parse_query("red dress under £50").max_price == 50.0


def test_price_extraction_no_currency_symbol():
    assert parse_query("red dress under 50").max_price == 50.0


def test_price_extraction_below():
    assert parse_query("shoes below £75").max_price == 75.0


def test_price_extraction_decimal():
    assert parse_query("top under £29.99").max_price == 29.99


def test_price_extraction_max_keyword():
    assert parse_query("jeans max £40").max_price == 40.0


def test_no_price_constraint_leaves_max_price_none():
    assert parse_query("black nike shoes").max_price is None


def test_colour_mapping_simple():
    assert parse_query("red dress").colour == "Red"


def test_colour_mapping_prefers_multiword_colour_over_substring():
    # Must not match plain "Blue" inside "Navy Blue".
    assert parse_query("navy blue jacket").colour == "Navy Blue"


def test_colour_mapping_falls_back_to_single_word_when_no_multiword_present():
    assert parse_query("blue jeans").colour == "Blue"


def test_colour_mapping_no_match_is_none():
    assert parse_query("smart casual blazer").colour is None


def test_occasion_extraction():
    assert parse_query("smart casual blazer").occasion == "Smart Casual"


def test_occasion_not_in_controlled_vocabulary_is_none():
    # "wedding guest" is not a real `usage` value in this catalogue (Casual/Ethnic/Formal/Home/
    # Party/Smart Casual/Sports/Travel) — the parser must not fabricate one it can't validate.
    assert parse_query("wedding guest dress").occasion is None


def test_gender_extraction():
    assert parse_query("nike men shoes").gender == "Men"


def test_category_alias_trainers_maps_to_shoes():
    assert parse_query("adidas trainers").category == "shoes"


def test_category_alias_sneakers_maps_to_shoes():
    assert parse_query("white sneakers").category == "shoes"


def test_no_category_alias_present_is_none():
    assert parse_query("smart casual blazer").category is None


def test_category_direct_match():
    assert parse_query("red dress").category == "dress"


def test_category_direct_match_preferred_over_alias():
    # "shoes" itself is a direct controlled-category match; alias lookup shouldn't even run.
    assert parse_query("black nike shoes").category == "shoes"


def test_ambiguous_personal_care_words_never_auto_filter_category():
    # "skin", "hair", "lips", "eyes", "nails", "home" are real category values in this dataset
    # but common English words untethered from shopping intent — must not be auto-matched.
    assert parse_query("true to skin tone red dress").category == "dress"
    assert parse_query("home run baseball cap").category is None


def test_combined_query_extracts_all_present_attributes():
    parsed = parse_query("red dress under £50")
    assert parsed.colour == "Red"
    assert parsed.max_price == 50.0
    assert parsed.category == "dress"
    assert parsed.occasion is None


def test_is_empty_true_when_nothing_extracted():
    assert parse_query("xyz nonsense query").is_empty() is True


def test_is_empty_false_when_something_extracted():
    assert parse_query("red dress").is_empty() is False
