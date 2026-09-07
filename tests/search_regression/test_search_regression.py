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
    """Known, named gap (architecture §2.3 "no-result recovery" journey), and worse as of
    Stage 11 than it was at Stage 8: BM25 alone at least has *some* concept of "no term
    overlap" (a maximally strict query can score zero); vector kNN has none at all — it always
    returns its k nearest neighbours no matter how irrelevant they are, so a fused hybrid result
    can never come back truly empty even for pure gibberish (see
    tests/integration/test_api_contract.py::test_search_nonsense_query_returns_something_not_an_error).
    "purple waterproof tuxedo" top hits still score high on "waterproof"/"purple" alone, e.g.
    "Colorbar Precision Waterproof Eye Liner". This test documents current behaviour so a
    future change is a deliberate decision, not a silent regression discovered by accident —
    fixing it for real is Stage 12 (eligibility: a minimum-relevance cutoff) work, not Stage
    8/11's."""
    resp = client.get("/search", params={"q": "purple waterproof tuxedo"})
    assert resp.status_code == 200
    assert len(resp.json()["results"]) > 0


def test_empty_query_returns_no_results_not_an_error(client):
    resp = client.get("/search", params={"q": ""})
    assert resp.status_code == 200
    assert resp.json()["results"] == []


def test_price_constraint_is_enforced(client):
    resp = client.get("/search", params={"q": "red dress under £50"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["interpretation"]["colour"] == "Red"
    assert body["interpretation"]["max_price"] == 50.0
    assert len(body["results"]) > 0
    assert all(r["price"] <= 50.0 for r in body["results"])
    assert all(r["colour"] == "Red" for r in body["results"])


def test_category_is_not_hard_filtered(client):
    """Regression-protects a specific, measured Stage 9 finding: hard-filtering on the
    extracted category word regressed overall ndcg@10 from 0.766 to 0.660 on the judgment set
    (e.g. it excluded every graded-relevant wedding saree for "wedding guest dress", because
    the catalogue only tags those as category=saree, not category=dress). category is still
    extracted and shown in `interpretation`, just never used as a filter."""
    resp = client.get("/search", params={"q": "wedding guest dress"})
    body = resp.json()
    assert body["interpretation"]["category"] == "dress"
    titles = [r["title"] for r in body["results"][:10]]
    assert any("wedding" in t.lower() for t in titles)


def test_results_have_no_duplicate_titles(client):
    """Regression-protects Stage 12's duplicate control: before it, "black nike shoes"
    returned several identical "Nike Men Black Shoes" cards (different product_ids, same
    display) — real, visible, screenshotted evidence of the problem this fixed."""
    resp = client.get("/search", params={"q": "black nike shoes"})
    titles = [r["title"] for r in resp.json()["results"]]
    assert len(titles) == len(set(titles))


def test_out_of_stock_products_are_excluded_by_default(client):
    resp = client.get("/search", params={"q": "nike"})
    assert all(r["in_stock"] for r in resp.json()["results"])


def test_size_eligibility_only_returns_products_with_that_size(client):
    resp = client.get("/search", params={"q": "red dress size M"})
    body = resp.json()
    assert body["interpretation"]["size"] == "M"
    assert len(body["results"]) > 0
    assert all("M" in r["sizes"] for r in body["results"])


def test_every_response_carries_a_traceable_version(client):
    """Every result response includes a search request ID and model/configuration version
    (FR-04) — checked as a regression, not just in the general contract test, because a
    future refactor of the fallback logic is exactly the kind of change that could silently
    drop this."""
    resp = client.get("/search", params={"q": "nike"})
    body = resp.json()
    assert body["search_request_id"].startswith("srch_")
    assert body["model_version"] in (
        "hybrid_weighted_fusion_v1",
        "bm25_opensearch_synonyms_qu_v1",
        "token_intersection_postgres_v0",
    )
