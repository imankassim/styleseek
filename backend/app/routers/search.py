"""GET /search.

Primary path: OpenSearch BM25, synonym-enabled index + boosted cross_fields query — the
configuration EXP14 (experiments/EXP14_synonym_expansion) measured as the best lexical baseline
(ndcg@10 0.755 vs EXP10's Postgres comparison at 0.355).

Stage 9 adds query understanding (app/query_understanding.py): a deterministic parser extracts
category/colour/occasion/gender/max_price from the free text, validated only against the
catalogue's own controlled vocabulary. Extracted attributes become hard filters applied
alongside — not instead of — the full free-text query, on both the OpenSearch path and the
Postgres fallback (architecture "hard constraints before soft preference" applies regardless of
which engine actually serves the request). model_version `bm25_opensearch_synonyms_qu_v1`.

Fallback path: if OpenSearch is unavailable, falls back to the Stage 5 Postgres token-intersection
placeholder (architecture §10, "OpenSearch unavailable: return a controlled service error or an
explicitly defined limited fallback — do not display unrelated products as search results").
`fallback_used=True` and `model_version` reflect what actually served the response, not just
what was requested — architecture §11 auditability.

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
from app.query_understanding import ParsedQuery, parse_query
from app.schemas import ProductResult, QueryInterpretation, SearchResponse
from app.session import get_session_id

router = APIRouter()
logger = logging.getLogger(__name__)

OPENSEARCH_MODEL_VERSION = "bm25_opensearch_synonyms_qu_v1"
FALLBACK_MODEL_VERSION = "token_intersection_postgres_v0"
RESULT_LIMIT = 24


def _score_expr(num_tokens: int) -> str:
    clauses = ["(CASE WHEN searchable_text ILIKE %s THEN 1 ELSE 0 END)" for _ in range(num_tokens)]
    return " + ".join(clauses) if clauses else "0"


def _search_opensearch(query: str, limit: int, parsed: ParsedQuery) -> list[ProductResult] | None:
    """Returns None (not an exception) on any failure — the caller falls back to Postgres."""
    client = opensearch.get_client()
    if client is None:
        return None

    try:
        docs = opensearch.search(client, query, limit, parsed=parsed)
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


def _search_postgres_fallback(
    conn: Connection, query: str, limit: int, parsed: ParsedQuery
) -> list[ProductResult]:
    tokens = [t for t in query.lower().split() if t]
    token_patterns = [f"%{t}%" for t in tokens]
    score_sql = _score_expr(len(tokens))

    # Same hard constraints as the OpenSearch path (app/opensearch.py's _build_filters) —
    # architecture's "hard constraints before soft preference" isn't optional just because
    # we're on the fallback engine. Only colour/gender/price — category and occasion are
    # deliberately excluded, see app/opensearch.py's _build_filters docstring for the measured
    # reason (both hurt overall ndcg@10 when tried as hard filters).
    filter_conditions = []
    filter_params: list = []
    if parsed.colour:
        filter_conditions.append("pc.colour = %s")
        filter_params.append(parsed.colour)
    if parsed.gender:
        filter_conditions.append("p.gender = %s")
        filter_params.append(parsed.gender)
    if parsed.max_price is not None:
        filter_conditions.append("p.price <= %s")
        filter_params.append(parsed.max_price)
    filter_sql = ("AND " + " AND ".join(filter_conditions)) if filter_conditions else ""

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
            WHERE TRUE {filter_sql}
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
    """  # noqa: S608 -- filter_sql is built from a fixed set of literal clauses, not user input

    with conn.cursor() as cur:
        cur.execute(sql, [*filter_params, *token_patterns, limit])
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
    interpretation: dict | None,
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
                json.dumps(interpretation),
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
    parsed = ParsedQuery()
    interpretation: QueryInterpretation | None = None

    if query:
        parsed = parse_query(query)
        if not parsed.is_empty():
            interpretation = QueryInterpretation(
                category=parsed.category,
                range=None,  # not extracted — no controlled "range"/fit vocabulary in this catalogue
                colour=parsed.colour,
                occasion=parsed.occasion,
                max_price=parsed.max_price,
            )

        opensearch_results = _search_opensearch(query, RESULT_LIMIT, parsed)
        if opensearch_results is not None:
            results = opensearch_results
        else:
            results = _search_postgres_fallback(conn, query, RESULT_LIMIT, parsed)
            model_version = FALLBACK_MODEL_VERSION
            fallback_used = True

    latency_ms = int((time.perf_counter() - started_at) * 1000)
    _log_search_request(
        conn,
        search_request_id=search_request_id,
        session_id=session_id,
        query=query,
        interpretation=interpretation.model_dump() if interpretation else None,
        model_version=model_version,
        fallback_used=fallback_used,
        result_count=len(results),
        latency_ms=latency_ms,
    )

    return SearchResponse(
        search_request_id=search_request_id,
        query=query,
        interpretation=interpretation,
        model_version=model_version,
        fallback_used=fallback_used,
        results=results,
    )
