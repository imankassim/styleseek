"""Shared candidate-retrieval helpers for the Stage 11 hybrid fusion experiments (EXP32/33/34) —
BM25 (EXP31/EXP14's config) and vector (EXP30/EXP22's config) search, each returning
(product_id, raw_score) pairs so callers can choose rank-based (RRF) or score-based
(normalised/weighted) fusion.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from embeddings import embed_query  # noqa: E402
from vector_mapping import INDEX_NAME as VECTOR_INDEX  # noqa: E402

# Matches experiments/EXP14_synonym_expansion/synonym_mapping.py and backend/app/opensearch.py —
# not imported from either to avoid search/ depending on experiments/ (the wrong direction) or
# on backend/ (a different layer); this is a stable constant, not logic worth sharing a module
# for.
BM25_INDEX = "styleseek_products_v2_synonyms"
BM25_BOOSTED_FIELDS = ["title^3", "category_text^2", "colours_text^2", "occasion^1", "brand^1"]


def bm25_candidates(client, query: str, limit: int = 50) -> list[tuple[str, float]]:
    resp = client.search(
        index=BM25_INDEX,
        body={
            "query": {
                "multi_match": {"query": query, "type": "cross_fields", "fields": BM25_BOOSTED_FIELDS}
            },
            "size": limit,
        },
    )
    return [(hit["_source"]["product_id"], hit["_score"]) for hit in resp["hits"]["hits"]]


def vector_candidates(
    client, query: str, field: str = "title_vector", limit: int = 50
) -> list[tuple[str, float]]:
    query_vector = embed_query(query)
    resp = client.search(
        index=VECTOR_INDEX,
        body={"query": {"knn": {field: {"vector": query_vector, "k": limit}}}, "size": limit},
    )
    return [(hit["_source"]["product_id"], hit["_score"]) for hit in resp["hits"]["hits"]]
