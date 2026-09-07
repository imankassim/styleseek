"""EXP11: BM25, equal field weights.

Lexical baseline (architecture §14): a plain OpenSearch `multi_match` across title, category,
colour and occasion with no per-field boosting — deliberately not tuned, so EXP12's boosted
version can be measured as an explicit improvement over this rather than assumed better.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "evaluation"))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "search"))
from metrics import evaluate, print_report  # noqa: E402
from mapping import INDEX_NAME  # noqa: E402
from opensearch_client import get_client  # noqa: E402

FIELDS = ["title", "category_text", "colours_text", "occasion", "brand"]
RESULT_LIMIT = 50


def make_search_fn(client, fields=FIELDS, fuzziness=None):
    def search(query: str) -> list[str]:
        multi_match: dict = {"query": query, "fields": fields}
        if fuzziness is not None:
            multi_match["fuzziness"] = fuzziness

        resp = client.search(
            index=INDEX_NAME,
            body={"query": {"multi_match": multi_match}, "size": RESULT_LIMIT},
        )
        return [hit["_source"]["product_id"] for hit in resp["hits"]["hits"]]

    return search


if __name__ == "__main__":
    client = get_client()
    rows, summary = evaluate(make_search_fn(client), splits=["train", "val"])
    print_report("EXP11 BM25 equal field weights (train+val)", rows, summary)
