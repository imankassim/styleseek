"""EXP12: BM25, boosted structured fields.

Two changes from EXP11, both motivated by EXP11's own results (ndcg@10 0.091, worse than
EXP10's PostgreSQL baseline of 0.159):

  1. `type: "cross_fields"` instead of the default `best_fields` — best_fields scores each field
     independently and takes the single best match, which punishes queries like "black nike
     shoes" where "black" (colour), "nike" (title/brand) and "shoes" (category) each live in a
     *different* field. cross_fields treats the fields as one combined field, rewarding a
     document that matches across several of them — closer to what these structured-attribute
     queries actually need.
  2. Field boosts (title highest, then category/colour, occasion/brand lowest) so an exact
     title match still outranks an incidental occasion-field match.
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


def make_search_fn(client, fuzziness=None):
    def search(query: str) -> list[str]:
        multi_match: dict = {
            "query": query,
            "type": "cross_fields",
            "fields": BOOSTED_FIELDS,
        }
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
    print_report("EXP12 BM25 boosted fields + cross_fields (train+val)", rows, summary)
