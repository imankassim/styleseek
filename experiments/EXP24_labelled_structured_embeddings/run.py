"""EXP24: labelled structured embeddings.

Representation comparison (architecture §14). Same fields as EXP23, but formatted with explicit
labels ("Title: X | Brand: Y | Category: Z | ...", search/embeddings.py:labelled_structured_text)
instead of plain concatenation — tests whether the embedding model benefits from structure, or
whether it makes no difference (or hurts, by diluting the semantic content with label tokens).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "evaluation"))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "search"))
from metrics import evaluate, print_report  # noqa: E402
from opensearch_client import get_client  # noqa: E402
from vector_search import make_vector_search_fn  # noqa: E402

if __name__ == "__main__":
    client = get_client()
    search_fn = make_vector_search_fn(client, "structured_vector")
    rows, summary = evaluate(search_fn, splits=["train", "val"])
    print_report("EXP24 labelled structured embeddings (train+val)", rows, summary)
