"""Index mapping with a synonym token filter — needs its own index name since analyzers are
fixed at index-create time (can't be added to EXP12's existing index in place).
"""

INDEX_NAME = "styleseek_products_v2_synonyms"

# A small, hand-picked fashion synonym list — not exhaustive, just enough to test whether
# synonym expansion helps at all before investing in a bigger vocabulary.
SYNONYM_SETS = [
    "trainers, sneakers, shoes",
    "jeans, denim",
    "frock, dress",
    "purse, handbag, bag",
    "tee, tshirt, t-shirt",
    "trousers, pants",
    "jumper, sweater",
    "saree, sari",
]

INDEX_BODY = {
    "settings": {
        "number_of_shards": 1,
        "number_of_replicas": 0,
        "analysis": {
            "filter": {
                "fashion_synonyms": {
                    "type": "synonym",
                    "synonyms": SYNONYM_SETS,
                }
            },
            "analyzer": {
                "synonym_analyzer": {
                    "type": "custom",
                    "tokenizer": "standard",
                    "filter": ["lowercase", "fashion_synonyms"],
                }
            },
        },
    },
    "mappings": {
        "properties": {
            "product_id": {"type": "keyword"},
            "title": {"type": "text", "analyzer": "synonym_analyzer"},
            "brand": {"type": "text", "analyzer": "synonym_analyzer"},
            "category": {"type": "keyword"},
            "category_text": {"type": "text", "analyzer": "synonym_analyzer"},
            "colours": {"type": "keyword"},
            "colours_text": {"type": "text", "analyzer": "synonym_analyzer"},
            "occasion": {"type": "text", "analyzer": "synonym_analyzer"},
            "gender": {"type": "keyword"},
            "price": {"type": "float"},
            "sizes": {"type": "keyword"},
            "in_stock": {"type": "boolean"},
            "image_filename": {"type": "keyword", "index": False},
            "source_version": {"type": "long"},
        }
    },
}
