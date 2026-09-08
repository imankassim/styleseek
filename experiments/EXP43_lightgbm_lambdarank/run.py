"""EXP43: LightGBM LambdaRank.

Ranking candidate (architecture §14) — the model the architecture's own final recommendation
(§20) names explicitly, "only after sufficient labelled data". Unlike EXP40/41 (pointwise —
trained on individual rows with no notion of ranking), LGBMRanker's LambdaRank objective is
ranking-aware: it optimises directly for getting the *order* right within each query group, not
just predicting the grade of each row independently.
"""

import sys
from pathlib import Path

import psycopg
from lightgbm import LGBMRanker

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "ml" / "learning_to_rank"))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "evaluation"))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "search"))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "database"))
from features import build_feature_matrix, make_ltr_search_fn  # noqa: E402
from metrics import evaluate, print_report  # noqa: E402
from opensearch_client import get_client  # noqa: E402
from ingest import load_database_url  # noqa: E402

if __name__ == "__main__":
    client = get_client()
    with psycopg.connect(load_database_url()) as conn:
        X_train, y_train, groups, _keys = build_feature_matrix(conn, client, splits=["train"])
        print(f"Training rows: {len(X_train)} across {len(groups)} query groups: {groups}")

        # Deliberately small capacity (few leaves, few trees, no subsampling) — LightGBM's own
        # docs and architecture §21's cited "LightGBM advanced topics" both note small/sparse
        # ranking data needs conservative settings, not defaults tuned for much larger datasets.
        model = LGBMRanker(
            objective="lambdarank",
            n_estimators=30,
            num_leaves=7,
            min_child_samples=5,
            learning_rate=0.05,
            verbosity=-1,
        )
        model.fit(X_train, y_train, group=groups)

        search_fn = make_ltr_search_fn(model, conn, client)
        rows, summary = evaluate(search_fn, splits=["val"])
        print_report("EXP43 LightGBM LambdaRank, val split only, n=4", rows, summary)
