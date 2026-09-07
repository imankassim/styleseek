"""EXP1: whole-query substring search.

Primitive baseline: a product matches only if the *entire*, trimmed, lowercased query string
appears verbatim as a substring somewhere in its searchable text. No tokenisation, no fuzziness,
no attribute understanding. Deliberately the simplest thing that could be called "search".
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
    needle = query.strip().lower()
    if not needle:
        return []
    return [p["product_id"] for p in products if needle in searchable_text(p)]


if __name__ == "__main__":
    rows, by_type, overall = evaluate(search)
    print_report("EXP1 whole-query substring search", rows, by_type, overall)
