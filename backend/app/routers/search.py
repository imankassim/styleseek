"""GET /search.

Stage 5 scope only: wire a real, working page-to-Python-to-database path (architecture journey
5 exit outcome). The retrieval method here is deliberately the *same* token-intersection
approach validated (and found wanting) as EXP2 against the mock fixture in Stage 3 — now run as
real SQL against the real catalogue — not a new invention. It is explicitly a placeholder:

  - No query understanding yet (`interpretation` is always null) — that's Stage 9.
  - No BM25/OpenSearch yet — EXP10 (Postgres full-text) and BM25 tuning are Stage 8.
  - No semantic/hybrid retrieval yet — Stages 10-11.

model_version is versioned accordingly (`token_intersection_postgres_v0`) so later stages can be
measured as an explicit improvement over this baseline, not just assumed better.
"""

import uuid

from fastapi import APIRouter, Depends, Query
from psycopg import Connection

from app.db import get_connection
from app.schemas import ProductResult, SearchResponse

router = APIRouter()

MODEL_VERSION = "token_intersection_postgres_v0"
RESULT_LIMIT = 24


def _score_expr(num_tokens: int) -> str:
    clauses = ["(CASE WHEN searchable_text ILIKE %s THEN 1 ELSE 0 END)" for _ in range(num_tokens)]
    return " + ".join(clauses) if clauses else "0"


@router.get("/search", response_model=SearchResponse)
def search(
    q: str = Query(default="", max_length=200),
    conn: Connection = Depends(get_connection),
) -> SearchResponse:
    search_request_id = f"srch_{uuid.uuid4().hex[:10]}"
    query = q.strip()

    if not query:
        return SearchResponse(
            search_request_id=search_request_id,
            query=query,
            interpretation=None,
            model_version=MODEL_VERSION,
            fallback_used=False,
            results=[],
        )

    tokens = [t for t in query.lower().split() if t]
    token_patterns = [f"%{t}%" for t in tokens]
    score_sql = _score_expr(len(tokens))

    sql = f"""
        WITH product_colour AS (
            SELECT DISTINCT ON (product_id) product_id, colour
            FROM product_variant
            ORDER BY product_id, colour
        ),
        searchable AS (
            SELECT
                p.product_id, p.title, p.brand, p.category, p.price, p.image_filename,
                pc.colour,
                lower(
                    p.title || ' ' || p.category || ' ' || coalesce(p.occasion, '')
                    || ' ' || coalesce(p.gender, '') || ' ' || pc.colour
                ) AS searchable_text
            FROM product p
            JOIN product_colour pc ON pc.product_id = p.product_id
        ),
        scored AS (
            SELECT product_id, title, brand, category, price, image_filename, colour,
                   ({score_sql}) AS score
            FROM searchable
        )
        SELECT
            sc.product_id, sc.title, sc.brand, sc.category, sc.price, sc.image_filename,
            sc.colour, sc.score,
            array_agg(DISTINCT v.size) AS sizes,
            bool_or(v.stock_quantity > 0) AS in_stock
        FROM scored sc
        JOIN product_variant v ON v.product_id = sc.product_id
        WHERE sc.score > 0
        GROUP BY sc.product_id, sc.title, sc.brand, sc.category, sc.price, sc.image_filename,
                 sc.colour, sc.score
        ORDER BY sc.score DESC, sc.product_id
        LIMIT %s
    """

    params = [*token_patterns, RESULT_LIMIT]

    with conn.cursor() as cur:
        cur.execute(sql, params)
        rows = cur.fetchall()

    results = [
        ProductResult(
            product_id=row[0],
            title=row[1],
            brand=row[2],
            category=row[3],
            price=float(row[4]),
            image_filename=row[5],
            colour=row[6],
            sizes=sorted(row[8]) if row[8] else [],
            in_stock=bool(row[9]),
        )
        for row in rows
    ]

    return SearchResponse(
        search_request_id=search_request_id,
        query=query,
        interpretation=None,
        model_version=MODEL_VERSION,
        fallback_used=False,
        results=results,
    )
