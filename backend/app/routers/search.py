"""GET /search.

Primary path (Stage 11): BM25 (EXP14's config) and semantic vector search (EXP22/30's config),
combined via weighted score fusion at 90/10 lexical/semantic — the configuration EXP34 measured
beating BM25 alone on both ndcg@10 (+1.3%) and recall@50 (+4.0%) at once. model_version
`hybrid_weighted_fusion_v1`. Retrieved sequentially, not in parallel — see the note in
_search_hybrid: parallelising with a ThreadPoolExecutor was tried and measured *slower* here.

Two-tier fallback, each reflected honestly in `model_version`/`fallback_used` (architecture §11
auditability — the response says what actually served it, not just what was attempted):
  - Vector search unavailable/fails -> BM25-only (architecture §10, "Vector index unavailable:
    run lexical retrieval and omit semantic contribution"). model_version reverts to Stage 9's
    BM25+query-understanding version.
  - OpenSearch itself unavailable -> the Stage 5 Postgres token-intersection placeholder
    (architecture §10, "OpenSearch unavailable: ...an explicitly defined limited fallback").

Stage 9 query understanding (app/query_understanding.py) still runs first: colour/gender/price
become hard filters applied to *both* BM25 and vector queries; category/occasion are extracted
and shown in `interpretation` but never filtered (Stage 9 finding — see app/opensearch.py's
build_filters docstring).
"""

import json
import logging
import time
import uuid

from fastapi import APIRouter, Depends, Query, Response
from opensearchpy.exceptions import OpenSearchException
from psycopg import Connection

from app import opensearch, semantic
from app.db import get_connection
from app.fusion import weighted_score_fusion
from app.query_understanding import ParsedQuery, parse_query
from app.schemas import ProductResult, QueryInterpretation, SearchResponse
from app.session import get_session_id

router = APIRouter()
logger = logging.getLogger(__name__)

HYBRID_MODEL_VERSION = "hybrid_weighted_fusion_v1"
BM25_ONLY_MODEL_VERSION = "bm25_opensearch_synonyms_qu_v1"
FALLBACK_MODEL_VERSION = "token_intersection_postgres_v0"
RESULT_LIMIT = 24
CANDIDATE_LIMIT = 50  # wider pool for fusion to draw from before truncating to RESULT_LIMIT


def _to_product_result(doc: dict) -> ProductResult:
    colours = doc.get("colours") or []
    return ProductResult(
        product_id=doc["product_id"],
        title=doc["title"],
        brand=doc["brand"],
        category=doc["category"],
        price=float(doc["price"]),
        image_filename=doc["image_filename"],
        colour=colours[0] if colours else "unknown",
        sizes=sorted(doc["sizes"]) if doc["sizes"] else [],
        in_stock=bool(doc["in_stock"]),
    )


def _score_expr(num_tokens: int) -> str:
    clauses = ["(CASE WHEN searchable_text ILIKE %s THEN 1 ELSE 0 END)" for _ in range(num_tokens)]
    return " + ".join(clauses) if clauses else "0"


def _search_hybrid(query: str, limit: int, parsed: ParsedQuery) -> tuple[list[ProductResult], str, bool] | None:
    """Returns (results, model_version, fallback_used), or None if OpenSearch itself is
    unavailable (both BM25 and vector depend on it) — the caller falls back to Postgres."""
    client = opensearch.get_client()
    if client is None:
        return None

    # Measured, not assumed: submitting these to a ThreadPoolExecutor (true parallel retrieval,
    # as architecture §16 recommends for latency) was tried here and measured *slower* in
    # practice (~1050ms) than calling them sequentially (~650ms) — nested-thread-pool overhead
    # (this handler already runs inside FastAPI/anyio's own worker thread) outweighed the
    # theoretical benefit on this platform. Kept sequential per that measurement, not the
    # architectural recommendation in the abstract — see docs/risk_register.md.
    try:
        bm25_docs = opensearch.search_with_scores(client, query, CANDIDATE_LIMIT, parsed)
    except OpenSearchException:
        logger.warning("BM25 query failed, falling back to Postgres", exc_info=True)
        opensearch.mark_unavailable()
        return None

    try:
        vector_docs = semantic.search_with_scores(client, query, CANDIDATE_LIMIT, parsed)
    except Exception:  # noqa: BLE001 -- any semantic-path failure just means "omit it"
        logger.warning("Vector query failed, continuing BM25-only", exc_info=True)
        vector_docs = None

    docs_by_id = {doc["product_id"]: doc for doc in bm25_docs}
    if vector_docs:
        for doc in vector_docs:
            docs_by_id.setdefault(doc["product_id"], doc)

    if not vector_docs:
        ranked_ids = [doc["product_id"] for doc in bm25_docs][:limit]
        results = [_to_product_result(docs_by_id[pid]) for pid in ranked_ids]
        return results, BM25_ONLY_MODEL_VERSION, True

    lexical_scores = {doc["product_id"]: doc["_bm25_score"] for doc in bm25_docs}
    semantic_scores = {doc["product_id"]: doc["_vector_score"] for doc in vector_docs}
    ranked_ids = weighted_score_fusion(lexical_scores, semantic_scores)[:limit]
    results = [_to_product_result(docs_by_id[pid]) for pid in ranked_ids]
    return results, HYBRID_MODEL_VERSION, False


def _search_postgres_fallback(
    conn: Connection, query: str, limit: int, parsed: ParsedQuery
) -> list[ProductResult]:
    tokens = [t for t in query.lower().split() if t]
    token_patterns = [f"%{t}%" for t in tokens]
    score_sql = _score_expr(len(tokens))

    # Same hard constraints as the hybrid path (app/opensearch.py's build_filters) —
    # architecture's "hard constraints before soft preference" isn't optional just because
    # we're on the fallback engine.
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
    model_version = HYBRID_MODEL_VERSION
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

        hybrid_result = _search_hybrid(query, RESULT_LIMIT, parsed)
        if hybrid_result is not None:
            results, model_version, fallback_used = hybrid_result
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
