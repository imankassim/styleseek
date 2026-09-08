"""Unit tests for backend/app/personalization.py's apply_session_colour_boost — the pure,
testable-without-a-database part of Stage 14. get_session_preferred_colour needs a real
database connection, covered by tests/integration instead.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "backend"))

from app.personalization import apply_session_colour_boost  # noqa: E402


def _docs(colours_by_id: dict[str, list[str]]) -> dict:
    return {pid: {"colours": colours} for pid, colours in colours_by_id.items()}


def test_no_preference_is_a_no_op():
    ranked = ["a", "b", "c"]
    result = apply_session_colour_boost(ranked, _docs({"a": ["Red"], "b": ["Blue"], "c": ["Green"]}), None)
    assert result == ranked


def test_cold_start_no_signal_is_a_no_op():
    # None is exactly what get_session_preferred_colour returns for a brand-new session.
    ranked = ["a", "b", "c"]
    result = apply_session_colour_boost(ranked, _docs({"a": [], "b": [], "c": []}), None)
    assert result == ranked


def test_matching_colour_moves_to_front_of_window():
    ranked = ["a", "b", "c", "d"]
    docs = _docs({"a": ["Red"], "b": ["Blue"], "c": ["Beige"], "d": ["Green"]})
    result = apply_session_colour_boost(ranked, docs, "Beige", window=10)
    assert result[0] == "c"


def test_relative_order_preserved_within_each_group():
    ranked = ["a", "b", "c", "d"]
    docs = _docs({"a": ["Beige"], "b": ["Blue"], "c": ["Beige"], "d": ["Green"]})
    result = apply_session_colour_boost(ranked, docs, "Beige", window=10)
    # Both "a" and "c" match, in their original relative order, ahead of the non-matches.
    assert result == ["a", "c", "b", "d"]


def test_never_touches_items_beyond_the_window():
    ranked = [str(i) for i in range(15)]
    docs = _docs({str(i): (["Beige"] if i == 12 else ["Blue"]) for i in range(15)})
    result = apply_session_colour_boost(ranked, docs, "Beige", window=10)
    # The match is at index 12, outside the window (0-9) — must stay exactly where it was.
    assert result == ranked


def test_never_introduces_or_drops_a_candidate():
    ranked = ["a", "b", "c", "d", "e"]
    docs = _docs({"a": ["Red"], "b": ["Beige"], "c": ["Blue"], "d": ["Beige"], "e": ["Green"]})
    result = apply_session_colour_boost(ranked, docs, "Beige", window=10)
    assert sorted(result) == sorted(ranked)
    assert len(result) == len(ranked)


def test_no_matches_in_window_leaves_ranking_unchanged():
    ranked = ["a", "b", "c"]
    docs = _docs({"a": ["Red"], "b": ["Blue"], "c": ["Green"]})
    result = apply_session_colour_boost(ranked, docs, "Purple", window=10)
    assert result == ranked
