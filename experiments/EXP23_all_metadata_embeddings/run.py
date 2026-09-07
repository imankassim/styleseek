"""EXP23: all-metadata embeddings.

Representation comparison (architecture §14). Embeds title + brand + category + colour(s) +
occasion + gender concatenated as plain text (search/embeddings.py:all_metadata_text) — more
signal than EXP22's title-only, no explicit field labels (compare EXP24).
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
    search_fn = make_vector_search_fn(client, "metadata_vector")
    rows, summary = evaluate(search_fn, splits=["train", "val"])
    print_report("EXP23 all-metadata embeddings (train+val)", rows, summary)
