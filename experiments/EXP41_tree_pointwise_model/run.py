"""EXP41: tree-based pointwise model.

Learned baseline (architecture §14) — a gradient-boosted tree regressor (scikit-learn) predicting
grade from the same features as EXP40, still pointwise (no ranking-aware loss — that's EXP43).
Trees can capture non-linear feature interactions EXP40's linear model can't (e.g. "high BM25
score AND colour match" mattering more together than either alone).
"""

import sys
from pathlib import Path

import psycopg
from sklearn.ensemble import GradientBoostingRegressor

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
        print(f"Training rows: {len(X_train)} across {len(groups)} queries")

        # Small n_estimators/max_depth on purpose: 178 rows can't support a large tree ensemble
        # without overfitting immediately.
        model = GradientBoostingRegressor(n_estimators=30, max_depth=2, random_state=42)
        model.fit(X_train, y_train)

        search_fn = make_ltr_search_fn(model, conn, client)
        rows, summary = evaluate(search_fn, splits=["val"])
        print_report("EXP41 tree-based pointwise (GBM regressor), val split only, n=4", rows, summary)
