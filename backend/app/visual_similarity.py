"""Visual similarity search (architecture §12 journey 16, "optional extensions... visual
similarity" — explicitly separate and optional, never rolled into the frozen core plan; see
ADR-3, docs/decisions/3-freeze-serving-configuration.md, which this doesn't touch).

Given a product_id, finds other products whose catalogue photo looks similar, using CLIP image
embeddings built offline (search/index_image_vectors.py) into their own OpenSearch index. No
embedding happens at request time — there's no user-supplied image, just a kNN lookup against an
already-stored vector for an existing product — so this module (unlike app/semantic.py) needs no
ML runtime dependency at all, just an OpenSearch query.

Self-contained from search/ tooling (duplicates the index name/field), same reasoning as
app/opensearch.py and app/semantic.py's own docstrings.
"""

from opensearchpy import OpenSearch
from opensearchpy.exceptions import OpenSearchException

IMAGE_VECTOR_INDEX_NAME = "styleseek_products_v5_image_vectors"
IMAGE_VECTOR_FIELD = "image_vector"


def find_similar_products(client: OpenSearch, product_id: str, limit: int) -> list[str] | None:
    """Ranked list of similar product_ids (excludes product_id itself), or None if similarity
    isn't available for this product right now -- no image vector was ever indexed for it (never
    had a catalogue photo, or the index build hasn't reached it), or the index/OpenSearch itself
    is unreachable. The caller should treat None the same as "no similar products available",
    the same honest-degradation pattern as app/semantic.py's embed_query returning None."""
    try:
        doc = client.get(index=IMAGE_VECTOR_INDEX_NAME, id=product_id, ignore=[404])
    except OpenSearchException:
        return None
    if not doc.get("found"):
        return None

    vector = doc["_source"][IMAGE_VECTOR_FIELD]
    try:
        resp = client.search(
            index=IMAGE_VECTOR_INDEX_NAME,
            body={
                "query": {"knn": {IMAGE_VECTOR_FIELD: {"vector": vector, "k": limit + 1}}},
                "size": limit + 1,
            },
        )
    except OpenSearchException:
        return None

    return [
        hit["_source"]["product_id"]
        for hit in resp["hits"]["hits"]
        if hit["_source"]["product_id"] != product_id
    ][:limit]
