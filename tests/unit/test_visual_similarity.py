"""Unit tests for backend/app/visual_similarity.py's find_similar_products — mocks the
OpenSearch client (a real kNN query needs a real index; that's covered by
tests/integration instead) to test the honest-degradation logic: no image vector for this
product, and the client itself failing outright."""

import sys
from pathlib import Path
from unittest.mock import MagicMock

from opensearchpy.exceptions import OpenSearchException

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "backend"))

from app.visual_similarity import IMAGE_VECTOR_INDEX_NAME, find_similar_products  # noqa: E402


def test_returns_none_when_source_product_has_no_image_vector():
    client = MagicMock()
    client.get.return_value = {"found": False}
    assert find_similar_products(client, "no-image-product", limit=10) is None


def test_returns_none_when_get_raises():
    client = MagicMock()
    client.get.side_effect = OpenSearchException("simulated outage")
    assert find_similar_products(client, "any-product", limit=10) is None


def test_returns_none_when_search_raises():
    client = MagicMock()
    client.get.return_value = {"found": True, "_source": {"image_vector": [0.1, 0.2]}}
    client.search.side_effect = OpenSearchException("simulated outage")
    assert find_similar_products(client, "any-product", limit=10) is None


def test_excludes_the_source_product_from_its_own_results():
    client = MagicMock()
    client.get.return_value = {"found": True, "_source": {"image_vector": [0.1, 0.2]}}
    client.search.return_value = {
        "hits": {
            "hits": [
                {"_source": {"product_id": "source"}},
                {"_source": {"product_id": "a"}},
                {"_source": {"product_id": "b"}},
            ]
        }
    }
    result = find_similar_products(client, "source", limit=10)
    assert result == ["a", "b"]


def test_truncates_to_limit_after_excluding_self():
    client = MagicMock()
    client.get.return_value = {"found": True, "_source": {"image_vector": [0.1, 0.2]}}
    client.search.return_value = {
        "hits": {
            "hits": [
                {"_source": {"product_id": "source"}},
                {"_source": {"product_id": "a"}},
                {"_source": {"product_id": "b"}},
                {"_source": {"product_id": "c"}},
            ]
        }
    }
    result = find_similar_products(client, "source", limit=2)
    assert result == ["a", "b"]


def test_queries_the_image_vector_index():
    client = MagicMock()
    client.get.return_value = {"found": True, "_source": {"image_vector": [0.1, 0.2]}}
    client.search.return_value = {"hits": {"hits": []}}
    find_similar_products(client, "source", limit=5)
    assert client.get.call_args.kwargs["index"] == IMAGE_VECTOR_INDEX_NAME
    assert client.search.call_args.kwargs["index"] == IMAGE_VECTOR_INDEX_NAME
