"""Semantic (vector) retrieval for the live /search endpoint. Representation and index chosen
by EXP22 (title-only embeddings) and EXP30 (vector-only baseline); combined with BM25 via
weighted score fusion chosen by EXP34 (Stage 11).

Imports fastembed/the model directly (not via search/embeddings.py) to keep backend/'s runtime
dependencies self-contained from the experiments/search tooling — mirrors how
app/opensearch.py already duplicates the BM25 index name/fields rather than importing them.
"""

from fastembed import TextEmbedding
from opensearchpy import OpenSearch
from opensearchpy.exceptions import OpenSearchException

from app.opensearch import build_filters

EMBEDDING_MODEL_NAME = "BAAI/bge-small-en-v1.5"
VECTOR_INDEX_NAME = "styleseek_products_v3_vectors"
VECTOR_FIELD = "title_vector"
QUERY_INSTRUCTION_PREFIX = "Represent this sentence for searching relevant passages: "

_model: TextEmbedding | None = None
_model_unavailable = False


def preload_model() -> None:
    """Called once at FastAPI startup (app/main.py) so the first real search request doesn't
    pay the model-load cost — mirrors preloading the DB/OpenSearch connections."""
    global _model, _model_unavailable  # noqa: PLW0603
    try:
        _model = TextEmbedding(model_name=EMBEDDING_MODEL_NAME, threads=1)
    except Exception:  # noqa: BLE001 -- genuinely any failure here means "no semantic today"
        _model_unavailable = True


def embed_query(text: str) -> list[float] | None:
    if _model_unavailable or _model is None:
        return None
    vec = next(_model.embed([f"{QUERY_INSTRUCTION_PREFIX}{text}"]))
    return vec.tolist()


def search_with_scores(client: OpenSearch, query: str, limit: int, parsed=None) -> list[dict] | None:
    """Returns None (not an exception) if semantic search can't run right now — the caller
    falls back to BM25-only (architecture §10, "Vector index unavailable: run lexical
    retrieval and omit semantic contribution")."""
    query_vector = embed_query(query)
    if query_vector is None:
        return None

    knn_clause: dict = {"vector": query_vector, "k": limit}
    if parsed is not None:
        filters = build_filters(parsed)
        if filters:
            knn_clause["filter"] = {"bool": {"filter": filters}}

    try:
        resp = client.search(
            index=VECTOR_INDEX_NAME,
            body={"query": {"knn": {VECTOR_FIELD: knn_clause}}, "size": limit},
            request_timeout=5,
        )
    except OpenSearchException:
        return None

    results = []
    for hit in resp["hits"]["hits"]:
        doc = dict(hit["_source"])
        doc["_vector_score"] = hit["_score"]
        results.append(doc)
    return results
