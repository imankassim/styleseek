"""EXP14: synonym expansion.

Motivated by architecture §2.3's own example vocabulary — "trainers" is used throughout the
target journeys, but the catalogue's controlled category vocabulary (database/ingest.py) uses
"shoes"/"sandal"/"flip flops", never the word "trainers" at all. A shopper searching "trainers"
gets zero category-field matches no matter how well-tuned the boosting is. Same story for
"jeans" vs "denim", "purse" vs "handbag", etc.

Builds a *separate* index (`styleseek_products_v2_synonyms`) with an equivalence synonym filter
applied at both index and query time, using EXP12's winning query shape (cross_fields + boosted
fields) so this experiment isolates the synonym effect rather than mixing in a second change.

Note: an early run of this experiment used `mapping` as this file's own local module name,
which collided with `search/index.py`'s internal `from mapping import ...` (Python caches
imported modules by name, not by which directory they came from) — it silently rebuilt the
*production* index with the wrong settings instead of the synonym one. Renamed to
`synonym_mapping.py` to avoid the collision; see EXP14's README "A build bug worth recording".
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "evaluation"))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "search"))
from metrics import evaluate, print_report  # noqa: E402
from opensearch_client import get_client  # noqa: E402
from index import build_index  # noqa: E402

# Deliberately NOT named `mapping` — search/index.py itself does `from mapping import ...`
# internally, and Python caches modules by name in sys.modules regardless of sys.path order.
# An identically-named local module here would silently resolve to whichever one got imported
# first (this bit us once: EXP14 initially rebuilt the *production* index with the wrong
# mapping because of exactly this collision — see the "Findings" section below).
from synonym_mapping import INDEX_BODY, INDEX_NAME  # noqa: E402

BOOSTED_FIELDS = ["title^3", "category_text^2", "colours_text^2", "occasion^1", "brand^1"]
RESULT_LIMIT = 50


def make_search_fn(client):
    def search(query: str) -> list[str]:
        resp = client.search(
            index=INDEX_NAME,
            body={
                "query": {
                    "multi_match": {"query": query, "type": "cross_fields", "fields": BOOSTED_FIELDS}
                },
                "size": RESULT_LIMIT,
            },
        )
        return [hit["_source"]["product_id"] for hit in resp["hits"]["hits"]]

    return search


if __name__ == "__main__":
    print(f"Building synonym-enabled index '{INDEX_NAME}'...")
    count = build_index(index_name=INDEX_NAME, index_body=INDEX_BODY)
    print(f"Indexed {count} documents.\n")

    client = get_client()
    rows, summary = evaluate(make_search_fn(client), splits=["train", "val"])
    print_report("EXP14 BM25 boosted + synonym expansion (train+val)", rows, summary)
