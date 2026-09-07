"""EXP13: BM25 fuzziness.

Boosted fields as in EXP12 (the best result so far: ndcg@10 0.624 vs EXP10's 0.322 and EXP11's
0.510), plus `fuzziness: "AUTO"`. Motivated directly by EXP10/11/12 all scoring ndcg=0.00 on the
one typo query (rj17, "blu jeens") — every prior lexical configuration failed it identically.

OpenSearch rejects `fuzziness` on `type: "cross_fields"` (EXP12's type) outright — "Fuzziness
not allowed for type [cross_fields]". Using `most_fields` instead: like cross_fields it sums
evidence across matching fields (rewarding a document that matches several attributes) rather
than best_fields' take-the-single-best-field behaviour, and it does support fuzziness.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "evaluation"))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "search"))
from metrics import evaluate, print_report  # noqa: E402
from mapping import INDEX_NAME  # noqa: E402
from opensearch_client import get_client  # noqa: E402

BOOSTED_FIELDS = ["title^3", "category_text^2", "colours_text^2", "occasion^1", "brand^1"]
RESULT_LIMIT = 50


def make_search_fn(client):
    def search(query: str) -> list[str]:
        resp = client.search(
            index=INDEX_NAME,
            body={
                "query": {
                    "multi_match": {
                        "query": query,
                        "type": "most_fields",
                        "fields": BOOSTED_FIELDS,
                        "fuzziness": "AUTO",
                    }
                },
                "size": RESULT_LIMIT,
            },
        )
        return [hit["_source"]["product_id"] for hit in resp["hits"]["hits"]]

    return search


if __name__ == "__main__":
    client = get_client()
    rows, summary = evaluate(make_search_fn(client), splits=["train", "val"])
    print_report("EXP13 BM25 boosted + fuzziness AUTO (train+val)", rows, summary)
