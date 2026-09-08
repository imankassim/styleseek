"""Saves raw per-query ranked result lists to disk (architecture §18 minimum artefact set:
"evaluation harness and saved result lists" -- found missing during the 2026-09-08 brief-
fulfilment audit, see docs/progress.md). evaluation/metrics.py's evaluate() computes ndcg/recall
per query but never returns the underlying ranked product_id list -- reproducible by re-running
each experiment, but not inspectable without doing so.

This is a dated snapshot of the CURRENT index/model state, not a literal reconstruction of each
historical EXPnn run -- several of those used index states (pre-synonym-expansion, for instance)
that no longer exist unchanged; the index has been rebuilt multiple times since (see
docs/risk_register.md). Three search paths, each directly comparable to the others because they
all run against today's same index:

  - live: the real, currently-served /search endpoint (via TestClient) -- the honest end-to-end
    system, query understanding/eligibility/personalisation included.
  - bm25_only / vector_only: the two individual retrieval paths (search/hybrid_candidates.py),
    same comparison EXP30-34 made, run fresh against today's index.

Run: python evaluation/save_results.py
Writes evaluation/results/<label>_<date>.json (all 18 labelled queries, all splits, so the file
is a complete current-state snapshot rather than a training-split-only artefact).
"""

import json
import sys
from datetime import date, datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))
sys.path.insert(0, str(Path(__file__).parent.parent / "search"))

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402
from hybrid_candidates import bm25_candidates, vector_candidates  # noqa: E402
from metrics import load_judgments, ndcg_at_k, recall_at_k  # noqa: E402
from opensearch_client import get_client  # noqa: E402

RESULTS_DIR = Path(__file__).parent / "results"
CANDIDATE_LIMIT = 50


def save_snapshot(label: str, search_fn) -> Path:
    queries = load_judgments(splits=None)  # all 18, all splits -- a complete snapshot
    rows = []
    for q in queries:
        ranked_ids = search_fn(q["query"])
        rows.append(
            {
                "query_id": q["query_id"],
                "query": q["query"],
                "type": q["type"],
                "split": q["split"],
                "ranked_product_ids": ranked_ids,
                "ndcg_at_10": ndcg_at_k(ranked_ids, q["graded_products"], k=10),
                "recall_at_50": recall_at_k(ranked_ids, q["graded_products"], k=50),
            }
        )

    snapshot = {
        "label": label,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "index_state_note": (
            "Run against whichever OpenSearch index state existed at generated_at -- not "
            "necessarily identical to the state any historical EXPnn comparison used."
        ),
        "queries": rows,
    }

    RESULTS_DIR.mkdir(exist_ok=True)
    out_path = RESULTS_DIR / f"{label}_{date.today().isoformat()}.json"
    out_path.write_text(json.dumps(snapshot, indent=2), encoding="utf-8")
    return out_path


if __name__ == "__main__":
    client = get_client()

    with TestClient(app) as test_client:

        def live_search(query: str) -> list[str]:
            resp = test_client.get("/search", params={"q": query})
            return [r["product_id"] for r in resp.json()["results"]]

        path = save_snapshot("live_hybrid", live_search)
        print(f"Saved {path}")

    def bm25_search(query: str) -> list[str]:
        return [pid for pid, _ in bm25_candidates(client, query, CANDIDATE_LIMIT)]

    path = save_snapshot("bm25_only", bm25_search)
    print(f"Saved {path}")

    def vector_search(query: str) -> list[str]:
        return [pid for pid, _ in vector_candidates(client, query, "title_vector", CANDIDATE_LIMIT)]

    path = save_snapshot("vector_only", vector_search)
    print(f"Saved {path}")
