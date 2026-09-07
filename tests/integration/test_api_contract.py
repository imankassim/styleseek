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
