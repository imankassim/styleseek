"""EXP22: title-only embeddings.

Representation comparison (architecture §14). Embeds just the product title
(search/embeddings.py:title_only_text) — the simplest possible representation, and (since the
catalogue has no description field — see EXP21's rejection) the closest thing to a "minimal"
baseline for this comparison. Vector-only kNN retrieval (no lexical signal at all), against the
same synonym-index... no — against search/vector_mapping.py's dedicated vector index, built by
search/index_vectors.py.
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
    search_fn = make_vector_search_fn(client, "title_vector")
    rows, summary = evaluate(search_fn, splits=["train", "val"])
    print_report("EXP22 title-only embeddings (train+val)", rows, summary)
