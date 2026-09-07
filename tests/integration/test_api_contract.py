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


def test_search_nonsense_query_returns_no_results(client):
    resp = client.get("/search", params={"q": "zzzznonexistentqueryterm"})
    assert resp.status_code == 200
    assert resp.json()["results"] == []


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
