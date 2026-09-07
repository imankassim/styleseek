"""OpenSearch client for the live /search endpoint. Serving config chosen by EXP14
(experiments/EXP14_synonym_expansion) — synonym-enabled index, cross_fields + boosted fields.
"""

from opensearchpy import OpenSearch

from app.config import get_opensearch_url

INDEX_NAME = "styleseek_products_v2_synonyms"
BOOSTED_FIELDS = ["title^3", "category_text^2", "colours_text^2", "occasion^1", "brand^1"]

_client: OpenSearch | None = None
_unavailable = False  # sticky within a process: don't retry a dead cluster on every request


def get_client() -> OpenSearch | None:
    global _client, _unavailable  # noqa: PLW0603
    if _unavailable:
        return None
    if _client is None:
        url = get_opensearch_url()
        if url is None:
            _unavailable = True
            return None
        _client = OpenSearch(hosts=[url], use_ssl=True, verify_certs=True, timeout=3)
    return _client


def mark_unavailable() -> None:
    global _unavailable  # noqa: PLW0603
    _unavailable = True


def search(client: OpenSearch, query: str, limit: int) -> list[dict]:
    resp = client.search(
        index=INDEX_NAME,
        body={
            "query": {
                "multi_match": {"query": query, "type": "cross_fields", "fields": BOOSTED_FIELDS}
            },
            "size": limit,
        },
        request_timeout=3,
    )
    return [hit["_source"] for hit in resp["hits"]["hits"]]
