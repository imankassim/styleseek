"""GET /search.

Primary path: OpenSearch BM25, synonym-enabled index + boosted cross_fields query — the
configuration EXP14 (experiments/EXP14_synonym_expansion) measured as the best lexical baseline
(ndcg@10 0.755 vs EXP10's Postgres comparison at 0.355). model_version `bm25_opensearch_synonyms_v1`.

Fallback path: if OpenSearch is unavailable, falls back to the Stage 5 Postgres token-intersection
placeholder (architecture §10, "OpenSearch unavailable: return a controlled service error or an
explicitly defined limited fallback — do not display unrelated products as search results").
`fallback_used=True` and `model_version` reflect what actually served the response, not just
what was requested — architecture §11 auditability.

No query understanding yet (`interpretation` is always null) — that's Stage 9.
No semantic/hybrid retrieval yet — Stages 10-11.

Every request is logged to `search_request` (architecture §8.1), tagged with an anonymous
session id (architecture §11 privacy), for evaluation and event correlation (POST /events).
"""

import json
import logging
import time
import uuid

from fastapi import APIRouter, Depends, Query, Response
from opensearchpy.exceptions import OpenSearchException
from psycopg import Connection

from app import opensearch
from app.db import get_connection
from app.schemas import ProductResult, SearchResponse
from app.session import get_session_id

router = APIRouter()
logger = logging.getLogger(__name__)

OPENSEARCH_MODEL_VERSION = "bm25_opensearch_synonyms_v1"
FALLBACK_MODEL_VERSION = "token_intersection_postgres_v0"
RESULT_LIMIT = 24


def _score_expr(num_tokens: int) -> str:
    clauses = ["(CASE WHEN searchable_text ILIKE %s THEN 1 ELSE 0 END)" for _ in range(num_tokens)]
    return " + ".join(clauses) if clauses else "0"


def _search_opensearch(query: str, limit: int) -> list[ProductResult] | None:
    """Returns None (not an exception) on any failure — the caller falls back to Postgres."""
    client = opensearch.get_client()
    if client is None:
        return None

    try:
        docs = opensearch.search(client, query, limit)
    except OpenSearchException:
        logger.warning("OpenSearch query failed, falling back to Postgres", exc_info=True)
        opensearch.mark_unavailable()
        return None

    return [
        ProductResult(
            product_id=doc["product_id"],
            title=doc["title"],
            brand=doc["brand"],
            category=doc["category"],
            price=float(doc["price"]),
            image_filename=doc["image_filename"],
            colour=(doc["colours"] or ["unknown"])[0],
            sizes=sorted(doc["sizes"]) if doc["sizes"] else [],
            in_stock=bool(doc["in_stock"]),
        )
        for doc in docs
    ]


def _search_postgres_fallback(conn: Connection, query: str, limit: int) -> list[ProductResult]:
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

    with conn.cursor() as cur:
        cur.execute(sql, [*token_patterns, limit])
        rows = cur.fetchall()

    return [
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


def _log_search_request(
    conn: Connection,
    *,
    search_request_id: str,
    session_id: str,
    query: str,
    model_version: str,
    fallback_used: bool,
    result_count: int,
    latency_ms: int,
) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO search_request (
                search_request_id, session_id, query, interpretation, model_version,
                fallback_used, result_count, latency_ms
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                search_request_id,
                session_id,
                query,
                json.dumps(None),
                model_version,
                fallback_used,
                result_count,
                latency_ms,
            ),
        )
    conn.commit()


@router.get("/search", response_model=SearchResponse)
def search(
    response: Response,
    q: str = Query(default="", max_length=200),
    conn: Connection = Depends(get_connection),
    session_id: str = Depends(get_session_id),
) -> SearchResponse:
    started_at = time.perf_counter()
    search_request_id = f"srch_{uuid.uuid4().hex[:10]}"
    query = q.strip()

    results: list[ProductResult] = []
    model_version = OPENSEARCH_MODEL_VERSION
    fallback_used = False

    if query:
        opensearch_results = _search_opensearch(query, RESULT_LIMIT)
        if opensearch_results is not None:
            results = opensearch_results
        else:
            results = _search_postgres_fallback(conn, query, RESULT_LIMIT)
            model_version = FALLBACK_MODEL_VERSION
            fallback_used = True

    latency_ms = int((time.perf_counter() - started_at) * 1000)
    _log_search_request(
        conn,
        search_request_id=search_request_id,
        session_id=session_id,
        query=query,
        model_version=model_version,
        fallback_used=fallback_used,
        result_count=len(results),
        latency_ms=latency_ms,
    )

    return SearchResponse(
        search_request_id=search_request_id,
        query=query,
        interpretation=None,
        model_version=model_version,
        fallback_used=fallback_used,
        results=results,
    )
