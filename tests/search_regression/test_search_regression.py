"""Search regression tests (architecture §15: "Fixed exact, attribute, occasion, typo and
no-result queries. Known useful behaviour is protected."). Runs against the live /search
endpoint (real OpenSearch + real catalogue), using a fixed subset of the labelled query set —
not the full evaluation harness (that's evaluation/metrics.py and the experiments/ comparisons),
just a protective net so a future change can't silently break what already works.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "backend"))

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def top_titles(client, query, n=10):
    resp = client.get("/search", params={"q": query})
    assert resp.status_code == 200
    return [r["title"] for r in resp.json()["results"][:n]]


def test_exact_brand_query_returns_that_brand(client):
    titles = top_titles(client, "adidas trainers")
    assert any("adidas" in t.lower() for t in titles)
    assert any("shoe" in t.lower() for t in titles)


def test_attribute_query_respects_colour_and_category(client):
    titles = top_titles(client, "red dress")
    assert any("red" in t.lower() and "dress" in t.lower() for t in titles)


def test_occasion_query_returns_plausible_results(client):
    titles = top_titles(client, "smart casual blazer")
    assert any("blazer" in t.lower() for t in titles)


def test_synonym_vocabulary_gap_is_covered(client):
    """The catalogue's controlled category vocabulary never contains the word "trainers" (see
    database/ingest.py) — this is the exact case EXP14 (synonym expansion) was built for.
    Regression-protects that fix specifically, not just search in general."""
    titles = top_titles(client, "trainers")
    assert any("shoe" in t.lower() for t in titles)


def test_no_result_query_behaviour_is_a_known_gap_not_a_silent_regression(client):
    """Known, named gap (architecture §2.3 "no-result recovery" journey): plain BM25 has no
    concept of "nothing actually matches the full query" — it ranks by cumulative term
    evidence and always returns *something* with a non-trivial score (verified directly:
    "purple waterproof tuxedo" top hits score 14.7/13.8 from "waterproof"/"purple" alone, e.g.
    "Colorbar Precision Waterproof Eye Liner"). This differs from EXP1's naive whole-query
    substring baseline (Stage 3), which got true negatives "for free" by being maximally
    strict. This test documents current behaviour so a future change is a deliberate decision,
    not a silent regression discovered by accident — fixing it for real is Stage 9 (query
    understanding) / Stage 12 (eligibility) work, not Stage 8's."""
    resp = client.get("/search", params={"q": "purple waterproof tuxedo"})
    assert resp.status_code == 200
    assert len(resp.json()["results"]) > 0


def test_empty_query_returns_no_results_not_an_error(client):
    resp = client.get("/search", params={"q": ""})
    assert resp.status_code == 200
    assert resp.json()["results"] == []


def test_every_response_carries_a_traceable_version(client):
    """Every result response includes a search request ID and model/configuration version
    (FR-04) — checked as a regression, not just in the general contract test, because a
    future refactor of the fallback logic is exactly the kind of change that could silently
    drop this."""
    resp = client.get("/search", params={"q": "nike"})
    body = resp.json()
    assert body["search_request_id"].startswith("srch_")
    assert body["model_version"] in ("bm25_opensearch_synonyms_v1", "token_intersection_postgres_v0")
