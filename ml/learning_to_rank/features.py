"""Feature generation for Stage 13 (learning-to-rank). Versioned (FEATURE_VERSION) and shared
between offline training (this module, used by EXP40/41/43/44) and — if a model is ever
promoted — live serving, per architecture §9 training controls: "Version feature generation and
use the same logic in training and serving." No model here is promoted in this stage (see
Stage 13 README in docs/progress.md for why), so this module isn't imported by backend/ yet —
kept ready for if/when there's enough data to justify it.

Features are deliberately simple and inspectable (architecture §11 explainability): raw
retrieval scores from the two methods already in production (BM25, vector), a handful of
query/product attribute-match flags from the same deterministic parser already serving live
traffic (Stage 9), and price/stock. No behavioural (click) features — see EXP44's rejection for
why.
"""

import sys
from dataclasses import dataclass
from pathlib import Path

import psycopg

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "backend"))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "search"))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "evaluation"))

from app.query_understanding import parse_query  # noqa: E402
from hybrid_candidates import bm25_candidates, vector_candidates  # noqa: E402
from metrics import load_judgments  # noqa: E402

FEATURE_VERSION = "ltr_features_v1"
FEATURE_NAMES = [
    "bm25_score",
    "vector_score",
    "colour_match",
    "category_match",
    "gender_match",
    "occasion_text_match",
    "price",
    "under_max_price",
    "in_stock",
]

CANDIDATE_LIMIT = 200  # wide enough that every graded product should be reachable by at least one method


@dataclass
class ProductMeta:
    category: str
    colours: list[str]
    occasion: str | None
    gender: str | None
    price: float
    in_stock: bool


def _load_product_meta(conn: psycopg.Connection, product_ids: list[str]) -> dict[str, ProductMeta]:
    if not product_ids:
        return {}
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT
                p.product_id, p.category, p.occasion, p.gender, p.price,
                array_agg(DISTINCT v.colour) AS colours,
                bool_or(v.stock_quantity > 0) AS in_stock
            FROM product p
            JOIN product_variant v ON v.product_id = p.product_id
            WHERE p.product_id = ANY(%s)
            GROUP BY p.product_id, p.category, p.occasion, p.gender, p.price
            """,
            (product_ids,),
        )
        return {
            row[0]: ProductMeta(
                category=row[1],
                occasion=row[2],
                gender=row[3],
                price=float(row[4]),
                colours=row[5] or [],
                in_stock=bool(row[6]),
            )
            for row in cur.fetchall()
        }


def build_feature_row(parsed, meta: ProductMeta, bm25_score: float, vector_score: float) -> list[float]:
    colour_match = 1.0 if parsed.colour and parsed.colour in meta.colours else 0.0
    category_match = 1.0 if parsed.category and parsed.category == meta.category else 0.0
    gender_match = 1.0 if parsed.gender and parsed.gender == meta.gender else 0.0
    occasion_text_match = (
        1.0 if parsed.occasion and meta.occasion and parsed.occasion.lower() in meta.occasion.lower() else 0.0
    )
    under_max_price = 1.0 if parsed.max_price is None or meta.price <= parsed.max_price else 0.0
    return [
        bm25_score,
        vector_score,
        colour_match,
        category_match,
        gender_match,
        occasion_text_match,
        meta.price,
        under_max_price,
        1.0 if meta.in_stock else 0.0,
    ]


def build_feature_matrix(
    conn: psycopg.Connection, client, splits: list[str]
) -> tuple[list[list[float]], list[float], list[int], list[tuple[str, str]]]:
    """Returns (X, y, group_sizes, row_keys). group_sizes are per-query row counts, in the
    order LightGBM's LGBMRanker expects (architecture §9: "split by query", grouped evaluation).
    row_keys[i] = (query_id, product_id) for traceability back to the judgment set.
    """
    queries = load_judgments(splits)
    X: list[list[float]] = []
    y: list[float] = []
    group_sizes: list[int] = []
    row_keys: list[tuple[str, str]] = []

    for q in queries:
        graded = q["graded_products"]
        if not graded:
            continue

        parsed = parse_query(q["query"])
        product_ids = [p["product_id"] for p in graded]
        meta_by_id = _load_product_meta(conn, product_ids)

        bm25_scores = dict(bm25_candidates(client, q["query"], CANDIDATE_LIMIT))
        vector_scores = dict(vector_candidates(client, q["query"], "title_vector", CANDIDATE_LIMIT))

        rows_for_query = 0
        for p in graded:
            pid = p["product_id"]
            meta = meta_by_id.get(pid)
            if meta is None:
                continue  # shouldn't happen (all judgment products verified to exist), but be safe
            row = build_feature_row(parsed, meta, bm25_scores.get(pid, 0.0), vector_scores.get(pid, 0.0))
            X.append(row)
            y.append(float(p["grade"]))
            row_keys.append((q["query_id"], pid))
            rows_for_query += 1

        if rows_for_query:
            group_sizes.append(rows_for_query)

    return X, y, group_sizes, row_keys


def build_query_candidate_features(
    conn: psycopg.Connection, client, query: str, candidate_limit: int = 50
) -> tuple[list[str], list[list[float]]]:
    """Like build_feature_matrix, but scores the *actual retrieved candidate pool* for one
    query (the union of BM25's and vector's top-k), not just the graded judgment products —
    this is what a real reranking step would see, and what makes the resulting ndcg@10/
    recall@50 comparable to EXP34's (which were measured the same way, not against a
    pre-filtered "only graded" set).
    """
    parsed = parse_query(query)
    bm25_scored = dict(bm25_candidates(client, query, candidate_limit))
    vector_scored = dict(vector_candidates(client, query, "title_vector", candidate_limit))
    candidate_ids = list(dict.fromkeys([*bm25_scored.keys(), *vector_scored.keys()]))

    meta_by_id = _load_product_meta(conn, candidate_ids)
    rows: list[list[float]] = []
    valid_ids: list[str] = []
    for pid in candidate_ids:
        meta = meta_by_id.get(pid)
        if meta is None:
            continue
        rows.append(build_feature_row(parsed, meta, bm25_scored.get(pid, 0.0), vector_scored.get(pid, 0.0)))
        valid_ids.append(pid)
    return valid_ids, rows


def make_ltr_search_fn(model, conn: psycopg.Connection, client, candidate_limit: int = 50):
    """Wraps a trained model (anything with .predict(X) -> per-row scores) as a
    evaluation/metrics.py-compatible search_fn(query) -> ranked product_ids, for a like-for-like
    comparison against EXP34 and friends."""

    def search(query: str) -> list[str]:
        ids, rows = build_query_candidate_features(conn, client, query, candidate_limit)
        if not ids:
            return []
        scores = model.predict(rows)
        ranked = sorted(zip(scores, ids, strict=True), key=lambda pair: pair[0], reverse=True)
        return [pid for _score, pid in ranked]

    return search
