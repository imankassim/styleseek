"""Index settings/mapping for the base BM25 index (no synonyms — see EXP14 for the
synonym-enabled variant, which needs its own index since analyzers are set at index-create time).
"""

INDEX_NAME = "styleseek_products_v1"

INDEX_BODY = {
    "settings": {
        "number_of_shards": 1,
        "number_of_replicas": 0,
    },
    "mappings": {
        "properties": {
            "product_id": {"type": "keyword"},
            "title": {"type": "text"},
            "brand": {"type": "text"},
            "category": {"type": "keyword"},
            "category_text": {"type": "text"},
            "colours": {"type": "keyword"},
            "colours_text": {"type": "text"},
            "occasion": {"type": "text"},
            "gender": {"type": "keyword"},
            "price": {"type": "float"},
            "sizes": {"type": "keyword"},
            "in_stock": {"type": "boolean"},
            "image_filename": {"type": "keyword", "index": False},
            "source_version": {"type": "long"},
        }
    },
}
