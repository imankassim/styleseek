"""GET /products and GET /products/{product_id}."""

from fastapi import APIRouter, Depends, HTTPException, Query
from psycopg import Connection

from app.db import get_connection
from app.schemas import ProductDetail, ProductListResponse, ProductResult, ProductVariant

router = APIRouter()


@router.get("/products", response_model=ProductListResponse)
def list_products(
    category: str | None = None,
    limit: int = Query(default=24, le=100),
    offset: int = Query(default=0, ge=0),
    conn: Connection = Depends(get_connection),
) -> ProductListResponse:
    where = "WHERE p.category = %s" if category else ""
    params: list = [category] if category else []

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
            ORDER BY p.product_id
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
