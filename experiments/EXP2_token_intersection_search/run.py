"""EXP2: token intersection search.

Primitive baseline, one step up from EXP1: split the query into whitespace tokens and score
each product by how many query tokens appear as a substring somewhere in its searchable text.
Products with at least one matching token are returned, ranked by match count (ties broken by
catalogue order). Still no fuzziness, no synonyms, no numeric/attribute understanding — a query
token like "£40" or "12" only matches if it happens to appear verbatim in the product text, which
it never does in this fixture, so price/size constraints are expected to fail here too.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "fixtures"))
from evaluate import evaluate, print_report  # noqa: E402


def searchable_text(product: dict) -> str:
    return " ".join(
        [
            product["title"],
            product["brand"],
            product["category"],
            product["colour"],
            product["occasion"],
        ]
    ).lower()


def search(query: str, products: list[dict]) -> list[str]:
    tokens = [t for t in query.strip().lower().split() if t]
    if not tokens:
        return []

    scored = []
    for p in products:
        text = searchable_text(p)
        score = sum(1 for t in tokens if t in text)
        if score > 0:
            scored.append((score, p["product_id"]))

    scored.sort(key=lambda pair: pair[0], reverse=True)
    return [product_id for _score, product_id in scored]


if __name__ == "__main__":
    rows, by_type, overall = evaluate(search)
    print_report("EXP2 token intersection search", rows, by_type, overall)
