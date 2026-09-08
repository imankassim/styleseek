"""Index mapping for visual similarity search (architecture §12 journey 16, "optional
extensions... visual similarity" — an explicitly separate, optional investigation, never rolled
into the frozen core plan, ADR-3). One field, one representation (CLIP image embedding of the
catalogue photo) — no representation comparison here, unlike search/vector_mapping.py's three
text representations, since there's only one image per product to embed.

Same hnsw/cosinesimil/lucene convention as search/vector_mapping.py, for the same reason
(nmslib deprecated as of OpenSearch 3.0).
"""

IMAGE_EMBEDDING_DIMENSION = 512  # Qdrant/clip-ViT-B-32-vision

INDEX_NAME = "styleseek_products_v5_image_vectors"

INDEX_BODY = {
    "settings": {
        "number_of_shards": 1,
        "number_of_replicas": 0,
        "index.knn": True,
    },
    "mappings": {
        "properties": {
            "product_id": {"type": "keyword"},
            "image_vector": {
                "type": "knn_vector",
                "dimension": IMAGE_EMBEDDING_DIMENSION,
                "method": {"name": "hnsw", "space_type": "cosinesimil", "engine": "lucene"},
            },
        }
    },
}
