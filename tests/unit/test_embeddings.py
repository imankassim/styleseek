"""Unit tests for the text-representation functions in search/embeddings.py (architecture §15
unit-test examples include "feature generation" — these are the input features for the
embedding model, and are pure functions worth testing in isolation from the (slow, network-
dependent) actual embedding call).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "search"))

from embeddings import all_metadata_text, labelled_structured_text, title_only_text  # noqa: E402

SAMPLE_PRODUCT = {
    "product_id": "12691",
    "title": "Nike Men Dual Fusion Grey Sports Shoes",
    "brand": None,
    "category": "shoes",
    "colours": ["Grey"],
    "occasion": "Sports",
    "gender": "Men",
}


def test_title_only_text_returns_just_the_title():
    assert title_only_text(SAMPLE_PRODUCT) == "Nike Men Dual Fusion Grey Sports Shoes"


def test_all_metadata_text_includes_every_present_field():
    text = all_metadata_text(SAMPLE_PRODUCT)
    assert "Nike Men Dual Fusion Grey Sports Shoes" in text
    assert "shoes" in text
    assert "Grey" in text
    assert "Sports" in text
    assert "Men" in text


def test_all_metadata_text_skips_missing_brand_without_leaving_gaps():
    text = all_metadata_text(SAMPLE_PRODUCT)
    # brand is None — must not render as the literal string "None" or leave a double space.
    assert "None" not in text
    assert "  " not in text


def test_all_metadata_text_handles_multiple_colours():
    product = {**SAMPLE_PRODUCT, "colours": ["Grey", "Black"]}
    text = all_metadata_text(product)
    assert "Grey" in text
    assert "Black" in text


def test_labelled_structured_text_has_field_labels():
    text = labelled_structured_text(SAMPLE_PRODUCT)
    assert "Title: Nike Men Dual Fusion Grey Sports Shoes" in text
    assert "Category: shoes" in text
    assert "Colour: Grey" in text
    assert "Occasion: Sports" in text
    assert "Gender: Men" in text


def test_labelled_structured_text_omits_missing_fields_entirely():
    text = labelled_structured_text(SAMPLE_PRODUCT)
    assert "Brand:" not in text  # brand is None for this product


def test_labelled_structured_text_joins_multiple_colours_in_one_field():
    product = {**SAMPLE_PRODUCT, "colours": ["Grey", "Black"]}
    text = labelled_structured_text(product)
    assert "Colour: Grey, Black" in text


def test_all_representations_are_nonempty_for_a_minimal_product():
    minimal = {
        "title": "Basic Item",
        "brand": None,
        "category": "accessories",
        "colours": [],
        "occasion": None,
        "gender": None,
    }
    assert title_only_text(minimal) == "Basic Item"
    assert len(all_metadata_text(minimal)) > 0
    assert len(labelled_structured_text(minimal)) > 0
