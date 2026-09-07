"""Index mapping for semantic retrieval experiments (EXP22/23/24, EXP30). One index, three
candidate vector fields (title_vector / metadata_vector / structured_vector) so the
representation comparison doesn't need three separate indices — only the field embedded into
differs per representation, the mapping and non-vector fields are identical to the base index
(search/mapping.py).

knn must be enabled at index-creation time (architecture-imposed by OpenSearch itself — it can't
be turned on for an existing index), which is why this can't just extend
styleseek_products_v1/v2_synonyms in place.
"""

from embeddings import EMBEDDING_DIMENSIONS

INDEX_NAME = "styleseek_products_v3_vectors"

_VECTOR_FIELD = {
    "type": "knn_vector",
    "dimension": EMBEDDING_DIMENSIONS,
    "method": {
        # nmslib is deprecated as of OpenSearch 3.0 (can't create new indices with it) — lucene
        # is the built-in, no-extra-plugin engine.
        "name": "hnsw",
        "space_type": "cosinesimil",
        "engine": "lucene",
    },
}

INDEX_BODY = {
    "settings": {
        "number_of_shards": 1,
        "number_of_replicas": 0,
        "index.knn": True,
    },
    "mappings": {
        "properties": {
            "product_id": {"type": "keyword"},
            "title": {"type": "text"},
            "brand": {"type": "text"},
            "category": {"type": "keyword"},
            "colours": {"type": "keyword"},
            "occasion": {"type": "text"},
            "gender": {"type": "keyword"},
            "price": {"type": "float"},
            "sizes": {"type": "keyword"},
            "in_stock": {"type": "boolean"},
            "image_filename": {"type": "keyword", "index": False},
            "title_vector": _VECTOR_FIELD,
            "metadata_vector": _VECTOR_FIELD,
            "structured_vector": _VECTOR_FIELD,
        }
    },
}
