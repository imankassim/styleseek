"""Drift test (architecture §15 "Offline evaluation": "configuration choices are evidence-led")
— guards against a *silent* regression in the live `/search` endpoint's actual relevance quality,
the kind no other suite would catch: API contract tests check response shape, not whether the
results are any good; search regression tests check a handful of fixed queries land roughly
right, not an aggregate score. This runs the real, currently-shipped pipeline (through FastAPI's
TestClient, the same route a shopper hits) against the frozen held-out val+test judgment splits
(never used to tune EXP14/EXP34's config) and fails if the aggregate score drops meaningfully.

Thresholds are set well below the measured current baseline (ndcg@10 0.672, recall@50 0.657 on
val+test, 2026-09-08) -- enough margin to absorb ordinary noise (e.g. the OpenSearch score-tie
ordering variance noted in docs/risk_register.md) without absorbing a regression of the size this
project has actually shipped-and-caught before: the category/occasion hard-filter regression
(Stage 9, 0.766 -> 0.660) and the RRF/equal-weight fusion regressions (Stage 11, 0.755 -> 0.549
and 0.673). A drop past these thresholds means something worth investigating, not necessarily a
bug -- re-run `evaluation/metrics.py`'s full report before assuming which.

The two "typo" queries score 0 here by design, not as a new finding -- EXP13 (fuzzy matching)
was measured and rejected in Stage 8 because it regressed every other query type more than it
fixed typos. Their 0s are already baked into the thresholds below, not a surprise this test
exists to catch.

Run: python -m pytest tests/drift/test_metric_drift.py
Requires backend/ importable and DATABASE_URL/OPENSEARCH_URL resolvable (same as the integration
suite) -- this drives the real API, not a mock.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "backend"))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "evaluation"))

import pytest
from fastapi.testclient import TestClient

from app.main import app
from metrics import evaluate  # noqa: E402

NDCG_FLOOR = 0.55
RECALL_FLOOR = 0.55


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def _live_search_fn(client):
    def search(query: str) -> list[str]:
        resp = client.get("/search", params={"q": query})
        return [r["product_id"] for r in resp.json()["results"]]

    return search


def test_live_search_ndcg_has_not_drifted_below_floor(client):
    _, summary = evaluate(_live_search_fn(client), splits=["val", "test"])
    ndcg = summary["overall"]["mean_ndcg"]
    assert ndcg >= NDCG_FLOOR, (
        f"live /search ndcg@10 on val+test dropped to {ndcg:.3f} (floor {NDCG_FLOOR}) — "
        "call evaluate() with print_report() (evaluation/metrics.py) against this same search_fn "
        "to see which query type regressed before assuming a specific cause."
    )


def test_live_search_recall_has_not_drifted_below_floor(client):
    _, summary = evaluate(_live_search_fn(client), splits=["val", "test"])
    recall = summary["overall"]["mean_recall"]
    assert recall >= RECALL_FLOOR, (
        f"live /search recall@50 on val+test dropped to {recall:.3f} (floor {RECALL_FLOOR}) — "
        "call evaluate() with print_report() (evaluation/metrics.py) against this same search_fn "
        "to see which query type regressed before assuming a specific cause."
    )
