"""GET /products, GET /products/{product_id}, GET /categories, GET /products/{product_id}/similar."""

from fastapi import APIRouter, Depends, HTTPException, Query
from psycopg import Connection

from app import opensearch
from app.db import get_connection
from app.schemas import (
    CategoryListResponse,
    CategorySummary,
    ProductDetail,
    ProductListResponse,
    ProductResult,
    ProductVariant,
    SimilarProductsResponse,
)
from app.visual_similarity import find_similar_products

router = APIRouter()

SORT_OPTIONS = {
    "relevance": "p.product_id",
    "price_asc": "p.price ASC, p.product_id",
    "price_desc": "p.price DESC, p.product_id",
}


@router.get("/products", response_model=ProductListResponse)
def list_products(
    category: str | None = None,
    min_price: float | None = Query(default=None, ge=0),
    max_price: float | None = Query(default=None, ge=0),
    in_stock_only: bool = False,
    sort: str = Query(default="relevance", pattern="^(relevance|price_asc|price_desc)$"),
    limit: int = Query(default=24, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    conn: Connection = Depends(get_connection),
) -> ProductListResponse:
    conditions = []
    params: list = []
    if category:
        conditions.append("p.category = %s")
        params.append(category)
    if min_price is not None:
        conditions.append("p.price >= %s")
        params.append(min_price)
    if max_price is not None:
        conditions.append("p.price <= %s")
        params.append(max_price)
    if in_stock_only:
        conditions.append(
            "EXISTS (SELECT 1 FROM product_variant v2 "
            "WHERE v2.product_id = p.product_id AND v2.stock_quantity > 0)"
        )
    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    order_by = SORT_OPTIONS[sort]

    with conn.cursor() as cur:
        cur.execute(f"SELECT COUNT(*) FROM product p {where}", params)  # noqa: S608
        (total,) = cur.fetchone()

        cur.execute(
            f"""
            WITH product_colour AS (
                SELECT DISTINCT ON (product_id) product_id, colour
                FROM product_variant
                ORDER BY product_id, colour
            )
            SELECT
                p.product_id, p.title, p.brand, p.category, p.price, p.image_filename,
                pc.colour,
                array_agg(DISTINCT v.size) AS sizes,
                bool_or(v.stock_quantity > 0) AS in_stock
            FROM product p
            JOIN product_colour pc ON pc.product_id = p.product_id
            JOIN product_variant v ON v.product_id = p.product_id
            {where}
            GROUP BY p.product_id, p.title, p.brand, p.category, p.price, p.image_filename, pc.colour
            ORDER BY {order_by}
            LIMIT %s OFFSET %s
            """,  # noqa: S608
            [*params, limit, offset],
        )
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
            sizes=sorted(row[7]) if row[7] else [],
            in_stock=bool(row[8]),
        )
        for row in rows
    ]

    return ProductListResponse(total=total, limit=limit, offset=offset, results=results)


@router.get("/categories", response_model=CategoryListResponse)
def list_categories(conn: Connection = Depends(get_connection)) -> CategoryListResponse:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT category, COUNT(*) AS n
            FROM product
            GROUP BY category
            ORDER BY n DESC, category
            """
        )
        rows = cur.fetchall()

    return CategoryListResponse(
        categories=[CategorySummary(category=row[0], product_count=row[1]) for row in rows]
    )


def _products_by_id(conn: Connection, product_ids: list[str]) -> dict[str, ProductResult]:
    if not product_ids:
        return {}
    with conn.cursor() as cur:
        cur.execute(
            """
            WITH product_colour AS (
                SELECT DISTINCT ON (product_id) product_id, colour
                FROM product_variant
                ORDER BY product_id, colour
            )
            SELECT
                p.product_id, p.title, p.brand, p.category, p.price, p.image_filename,
                pc.colour,
                array_agg(DISTINCT v.size) AS sizes,
                bool_or(v.stock_quantity > 0) AS in_stock
            FROM product p
            JOIN product_colour pc ON pc.product_id = p.product_id
            JOIN product_variant v ON v.product_id = p.product_id
            WHERE p.product_id = ANY(%s)
            GROUP BY p.product_id, p.title, p.brand, p.category, p.price, p.image_filename, pc.colour
            """,
            (product_ids,),
        )
        rows = cur.fetchall()

    return {
        row[0]: ProductResult(
            product_id=row[0],
            title=row[1],
            brand=row[2],
            category=row[3],
            price=float(row[4]),
            image_filename=row[5],
            colour=row[6],
            sizes=sorted(row[7]) if row[7] else [],
            in_stock=bool(row[8]),
        )
        for row in rows
    }


@router.get("/products/{product_id}/similar", response_model=SimilarProductsResponse)
def get_similar_products(
    product_id: str,
    limit: int = Query(default=12, ge=1, le=50),
    conn: Connection = Depends(get_connection),
) -> SimilarProductsResponse:
    with conn.cursor() as cur:
        cur.execute("SELECT 1 FROM product WHERE product_id = %s", (product_id,))
        if cur.fetchone() is None:
            raise HTTPException(status_code=404, detail="Product not found")

    client = opensearch.get_client()
    if client is None:
        return SimilarProductsResponse(product_id=product_id, available=False, results=[])

    similar_ids = find_similar_products(client, product_id, limit)
    if similar_ids is None:
        return SimilarProductsResponse(product_id=product_id, available=False, results=[])

    products_by_id = _products_by_id(conn, similar_ids)
    results = [products_by_id[pid] for pid in similar_ids if pid in products_by_id]
    return SimilarProductsResponse(product_id=product_id, available=True, results=results)


@router.get("/products/{product_id}", response_model=ProductDetail)
def get_product(
    product_id: str,
    conn: Connection = Depends(get_connection),
) -> ProductDetail:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT product_id, title, brand, category, occasion, gender, price, image_filename
            FROM product WHERE product_id = %s
            """,
            (product_id,),
        )
        product_row = cur.fetchone()
        if product_row is None:
            raise HTTPException(status_code=404, detail="Product not found")

        cur.execute(
            """
            SELECT variant_id, colour, size, sku, stock_quantity
            FROM product_variant WHERE product_id = %s
            ORDER BY colour, size
            """,
            (product_id,),
        )
        variant_rows = cur.fetchall()

    return ProductDetail(
        product_id=product_row[0],
        title=product_row[1],
        brand=product_row[2],
        category=product_row[3],
        occasion=product_row[4],
        gender=product_row[5],
        price=float(product_row[6]),
        image_filename=product_row[7],
        variants=[
            ProductVariant(
                variant_id=v[0],
                colour=v[1],
                size=v[2],
                sku=v[3],
                stock_quantity=v[4],
            )
            for v in variant_rows
        ],
    )
