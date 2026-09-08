"""EXP40: simple pointwise model.

Learned baseline (architecture §14) — a plain linear regression predicting the relevance grade
(0-3) directly from features (ml/learning_to_rank/features.py), then ranking by predicted score.
"Pointwise" because it's trained on individual (query, product, grade) rows independently, with
no notion of ranking within a query group — the simplest thing that could be called "learned
ranking", to measure before anything fancier (EXP41 tree-based, EXP43 LightGBM LambdaRank).

Trained on `train` split only (11 queries, see feature build output); evaluated on `val` split
only (4 queries) — evaluating on the training data itself would be circular for a fitted model,
unlike EXP32-34 which involved no fitting at all.
"""

import sys
from pathlib import Path

import psycopg
from sklearn.linear_model import Ridge

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "ml" / "learning_to_rank"))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "evaluation"))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "search"))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "database"))
from features import FEATURE_NAMES, build_feature_matrix, make_ltr_search_fn  # noqa: E402
from metrics import evaluate, print_report  # noqa: E402
from opensearch_client import get_client  # noqa: E402
from ingest import load_database_url  # noqa: E402

if __name__ == "__main__":
    client = get_client()
    with psycopg.connect(load_database_url()) as conn:
        X_train, y_train, groups, _keys = build_feature_matrix(conn, client, splits=["train"])
        print(f"Training rows: {len(X_train)} across {len(groups)} queries")

        model = Ridge(alpha=1.0)
        model.fit(X_train, y_train)

        print("\nLearned coefficients (feature importance direction, not causal):")
        for name, coef in zip(FEATURE_NAMES, model.coef_, strict=True):
            print(f"  {name:20} {coef:+.4f}")

        search_fn = make_ltr_search_fn(model, conn, client)
        rows, summary = evaluate(search_fn, splits=["val"])
        print_report("EXP40 simple pointwise (Ridge), val split only, n=4", rows, summary)
