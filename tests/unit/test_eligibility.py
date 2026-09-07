"""Unit tests for backend/app/eligibility.py's pure functions. products_with_size_in_stock
needs a real database connection — covered by tests/integration instead."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "backend"))

from app.eligibility import deduplicate  # noqa: E402


def test_deduplicate_keeps_first_occurrence_of_each_key():
    items = ["a", "b", "a", "c", "b"]
    assert deduplicate(items, key_fn=lambda x: x) == ["a", "b", "c"]


def test_deduplicate_preserves_order():
    items = [3, 1, 4, 1, 5, 9, 2, 6]
    assert deduplicate(items, key_fn=lambda x: x) == [3, 1, 4, 5, 9, 2, 6]


def test_deduplicate_with_composite_key():
    products = [
        {"id": "1", "title": "Nike Shoes", "colour": "Black"},
        {"id": "2", "title": "Nike Shoes", "colour": "Black"},  # same title+colour as #1
        {"id": "3", "title": "Nike Shoes", "colour": "White"},  # different colour, kept
    ]
    result = deduplicate(products, key_fn=lambda p: (p["title"], p["colour"]))
    assert [p["id"] for p in result] == ["1", "3"]


def test_deduplicate_empty_list():
    assert deduplicate([], key_fn=lambda x: x) == []


def test_deduplicate_no_duplicates_returns_all():
    items = ["a", "b", "c"]
    assert deduplicate(items, key_fn=lambda x: x) == items
