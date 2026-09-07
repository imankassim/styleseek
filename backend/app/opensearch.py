"""OpenSearch client for the live /search endpoint. Serving config chosen by EXP14
(experiments/EXP14_synonym_expansion) — synonym-enabled BM25 index, cross_fields + boosted
fields — combined with semantic vector search (app/semantic.py) via weighted score fusion
(EXP34, Stage 11).
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
        _client = OpenSearch(hosts=[url], use_ssl=True, verify_certs=True, timeout=5)
    return _client


def mark_unavailable() -> None:
    global _unavailable  # noqa: PLW0603
    _unavailable = True


def build_filters(parsed) -> list[dict]:
    """parsed: app.query_understanding.ParsedQuery. Hard constraints (architecture "hard
    constraints before soft preference") — these gate the candidate set, they don't affect
    relevance scoring, which still runs on the full original query text. Shared by both the
    BM25 query (app/opensearch.py) and the vector query (app/semantic.py) — a hard constraint
    must hold regardless of which retrieval method is finding the candidate.

    Only colour, gender and price are applied as hard filters. Measured directly (Stage 9,
    against the full train+val judgment set) that they're the only extracted attributes that
    are genuinely unambiguous — a colour or a price cap means exactly one thing regardless of
    context. category and occasion were both tried and both measurably hurt overall ndcg@10
    (category: 0.759 -> 0.660; the category word in a query is often used loosely rather than as
    a strict product-category constraint — e.g. "nike running shoes" also validly matches Nike
    running *apparel* in this catalogue's own graded judgments, and "wedding guest **dress**"
    excluded every graded-relevant wedding sari once hard-filtered to category=dress). occasion
    was rejected for a similar but even sharper reason: every real "blazer" product is tagged
    occasion=Formal or Casual, never literally "Smart Casual", so filtering "smart casual
    blazer" on occasion excluded every genuine blazer result outright. Both remain in the
    response's `interpretation` for transparency and still reach ranking as free text (occasion
    is one of the boosted multi_match fields) — just never as a filter. Real category/occasion
    understanding is exactly what Stage 10's semantic retrieval exists to add without this
    literal-word brittleness.
    """
    filters: list[dict] = []
    if parsed.colour:
        filters.append({"term": {"colours": parsed.colour}})
    if parsed.gender:
        filters.append({"term": {"gender": parsed.gender}})
    if parsed.max_price is not None:
        filters.append({"range": {"price": {"lte": parsed.max_price}}})
    return filters


def search_with_scores(client: OpenSearch, query: str, limit: int, parsed=None) -> list[dict]:
    """Like search(), but each returned dict also carries `_bm25_score` — needed for fusion
    (app/routers/search.py), not just plain display."""
    bool_query: dict = {
        "must": [{"multi_match": {"query": query, "type": "cross_fields", "fields": BOOSTED_FIELDS}}]
    }
    if parsed is not None:
        filters = build_filters(parsed)
        if filters:
            bool_query["filter"] = filters

    resp = client.search(
        index=INDEX_NAME,
        body={"query": {"bool": bool_query}, "size": limit},
        request_timeout=5,
    )
    results = []
    for hit in resp["hits"]["hits"]:
        doc = dict(hit["_source"])
        doc["_bm25_score"] = hit["_score"]
        results.append(doc)
    return results


def search(client: OpenSearch, query: str, limit: int, parsed=None) -> list[dict]:
    return search_with_scores(client, query, limit, parsed)
