"""Integration / API contract tests (architecture §15) — run against the real database, using
FastAPI's TestClient (no separate server process needed).

Run from repo root: python -m pytest tests/integration/test_api_contract.py
Requires backend/ and database/ dependencies installed, and DATABASE_URL resolvable
(backend/.env or database/.env).
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


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_search_response_contract(client):
    """Every field from the documented response contract (architecture §7) must be present,
    with the right type, regardless of query content."""
    resp = client.get("/search", params={"q": "black"})
    assert resp.status_code == 200
    body = resp.json()

    assert isinstance(body["search_request_id"], str) and body["search_request_id"]
    assert body["query"] == "black"
    assert "interpretation" in body
    assert isinstance(body["model_version"], str) and body["model_version"]
    assert isinstance(body["fallback_used"], bool)
    assert isinstance(body["results"], list)

    for product in body["results"]:
        for field in ("product_id", "title", "category", "colour", "price", "sizes", "in_stock"):
            assert field in product


def test_search_empty_query_returns_no_results(client):
    resp = client.get("/search", params={"q": ""})
    assert resp.status_code == 200
    assert resp.json()["results"] == []


def test_search_finds_known_exact_match(client):
    resp = client.get("/search", params={"q": "nike"})
    assert resp.status_code == 200
    results = resp.json()["results"]
    assert len(results) > 0
    assert any("nike" in r["title"].lower() for r in results)


def test_search_nonsense_query_returns_something_not_an_error(client):
    """As of Stage 11 (hybrid fusion), a pure-gibberish query can never return truly empty
    results: vector kNN always returns its k nearest neighbours regardless of how irrelevant
    they are (there's no "no match" concept in kNN the way BM25 can genuinely score zero hits).
    This test only checks the request itself succeeds — see
    tests/search_regression/test_search_regression.py for the honest, named tracking of this
    behaviour as a known gap, not silently asserted away here."""
    resp = client.get("/search", params={"q": "zzzznonexistentqueryterm"})
    assert resp.status_code == 200
    assert isinstance(resp.json()["results"], list)


def test_product_list_pagination(client):
    resp = client.get("/products", params={"limit": 5, "offset": 0})
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] > 0
    assert len(body["results"]) == 5


def test_product_list_category_filter(client):
    resp = client.get("/products", params={"category": "dress", "limit": 10})
    body = resp.json()
    assert body["total"] > 0
    assert all(r["category"] == "dress" for r in body["results"])


def test_product_list_price_filter(client):
    resp = client.get("/products", params={"min_price": 20, "max_price": 60, "limit": 20})
    body = resp.json()
    assert len(body["results"]) > 0
    assert all(20 <= r["price"] <= 60 for r in body["results"])


def test_product_list_sort_price_desc(client):
    resp = client.get("/products", params={"sort": "price_desc", "limit": 20})
    prices = [r["price"] for r in resp.json()["results"]]
    assert prices == sorted(prices, reverse=True)


def test_product_list_sort_price_asc(client):
    resp = client.get("/products", params={"sort": "price_asc", "limit": 20})
    prices = [r["price"] for r in resp.json()["results"]]
    assert prices == sorted(prices)


def test_product_list_in_stock_only_total_is_consistent(client):
    """Regression check: `total` must reflect the same filter as `results`, not just the
    unfiltered product count — this broke once with a HAVING-based filter."""
    resp = client.get("/products", params={"in_stock_only": True, "limit": 100})
    body = resp.json()
    unfiltered_total = client.get("/products", params={"limit": 1}).json()["total"]
    assert 0 < body["total"] <= unfiltered_total


def test_categories_endpoint(client):
    resp = client.get("/categories")
    assert resp.status_code == 200
    categories = resp.json()["categories"]
    assert len(categories) > 0
    assert all("category" in c and "product_count" in c for c in categories)


def test_product_detail_found(client):
    list_resp = client.get("/products", params={"limit": 1})
    product_id = list_resp.json()["results"][0]["product_id"]

    resp = client.get(f"/products/{product_id}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["product_id"] == product_id
    assert len(body["variants"]) > 0


def test_product_detail_not_found(client):
    resp = client.get("/products/does-not-exist-xyz")
    assert resp.status_code == 404


def test_search_sets_session_cookie(client):
    # Clear the shared client's jar rather than opening a second TestClient — the connection
    # pool is a module-level singleton in app.db, and a second `with TestClient(app)` would
    # close it out from under this module-scoped fixture on exit.
    client.cookies.clear()
    resp = client.get("/search", params={"q": "nike"})
    assert "styleseek_session" in resp.cookies


def test_search_reuses_existing_session_cookie(client):
    client.cookies.clear()
    first = client.get("/search", params={"q": "nike"})
    session_id = first.cookies["styleseek_session"]

    second = client.get("/search", params={"q": "black"})
    assert "styleseek_session" not in second.cookies  # not re-set, already had it
    assert client.cookies["styleseek_session"] == session_id


def test_events_batch_recorded(client):
    search_resp = client.get("/search", params={"q": "nike"})
    search_request_id = search_resp.json()["search_request_id"]
    product_id = search_resp.json()["results"][0]["product_id"]

    resp = client.post(
        "/events",
        json={
            "events": [
                {
                    "event_type": "impression",
                    "search_request_id": search_request_id,
                    "product_id": product_id,
                    "position": 0,
                },
                {
                    "event_type": "click",
                    "search_request_id": search_request_id,
                    "product_id": product_id,
                    "position": 0,
                },
            ]
        },
    )
    assert resp.status_code == 200
    assert resp.json() == {"recorded": 2}


def test_events_batch_skips_invalid_rows_without_failing_valid_ones(client):
    search_resp = client.get("/search", params={"q": "nike"})
    search_request_id = search_resp.json()["search_request_id"]
    product_id = search_resp.json()["results"][0]["product_id"]

    resp = client.post(
        "/events",
        json={
            "events": [
                {
                    "event_type": "impression",
                    "search_request_id": search_request_id,
                    "product_id": product_id,
                    "position": 0,
                },
                {
                    "event_type": "impression",
                    "search_request_id": search_request_id,
                    "product_id": "does-not-exist-xyz",
                    "position": 1,
                },
            ]
        },
    )
    assert resp.status_code == 200
    assert resp.json() == {"recorded": 1}


def test_events_batch_all_invalid_returns_422(client):
    resp = client.post(
        "/events",
        json={
            "events": [
                {"event_type": "impression", "product_id": "does-not-exist-xyz", "position": 0},
            ]
        },
    )
    assert resp.status_code == 422


def test_search_falls_back_to_postgres_when_opensearch_unavailable(client, monkeypatch):
    """Failure injection (architecture §15, §10 'OpenSearch unavailable') — the shopper still
    gets real results, just from the documented fallback path, not an error."""
    import app.opensearch as opensearch_module

    monkeypatch.setattr(opensearch_module, "get_client", lambda: None)

    resp = client.get("/search", params={"q": "nike"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["fallback_used"] is True
    assert body["model_version"] == "token_intersection_postgres_v0"
    assert len(body["results"]) > 0  # still genuinely useful, not empty


def test_search_falls_back_to_bm25_only_when_vector_search_unavailable(client, monkeypatch):
    """Failure injection (architecture §15, §10 'Vector index unavailable: run lexical
    retrieval and omit semantic contribution') — BM25 alone still serves real results, not the
    full Postgres fallback, when only the semantic path is down."""
    import app.semantic as semantic_module

    monkeypatch.setattr(semantic_module, "search_with_scores", lambda *args, **kwargs: None)

    resp = client.get("/search", params={"q": "nike"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["fallback_used"] is True
    assert body["model_version"] == "bm25_opensearch_synonyms_qu_v1"
    assert len(body["results"]) > 0


def test_search_uses_hybrid_fusion_by_default(client):
    resp = client.get("/search", params={"q": "black nike shoes"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["model_version"] == "hybrid_weighted_fusion_v1"
    assert body["fallback_used"] is False
    assert len(body["results"]) > 0
