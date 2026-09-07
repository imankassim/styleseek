"""Builds the denormalised search index (architecture §8.1 "Search document", §8.2) from the
Postgres source of truth. Rebuildable and idempotent — running it again just re-indexes
everything with the current database state (deletes and recreates the index).
"""

import sys
from pathlib import Path

import psycopg
from opensearchpy.helpers import bulk

sys.path.insert(0, str(Path(__file__).parent))
from mapping import INDEX_BODY, INDEX_NAME  # noqa: E402
from opensearch_client import get_client  # noqa: E402

REPO_ROOT = Path(__file__).parent.parent


def get_database_url() -> str:
    env_path = REPO_ROOT / "database" / ".env"
    for line in env_path.read_text().splitlines():
        if line.startswith("DATABASE_URL="):
            return line.split("=", 1)[1].strip()
    msg = "DATABASE_URL not found in database/.env"
    raise RuntimeError(msg)


def fetch_documents(conn: psycopg.Connection):
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT
                p.product_id, p.title, p.brand, p.category, p.occasion, p.gender, p.price,
                p.image_filename, extract(epoch from p.updated_at)::bigint AS source_version,
                array_agg(DISTINCT v.colour) AS colours,
                array_agg(DISTINCT v.size) AS sizes,
                bool_or(v.stock_quantity > 0) AS in_stock
            FROM product p
            JOIN product_variant v ON v.product_id = p.product_id
            GROUP BY p.product_id, p.title, p.brand, p.category, p.occasion, p.gender, p.price,
                     p.image_filename, p.updated_at
            """
        )
        columns = [desc[0] for desc in cur.description]
        for row in cur:
            yield dict(zip(columns, row, strict=True))


def to_actions(rows, index_name: str):
    for row in rows:
        colours = row["colours"] or []
        yield {
            "_index": index_name,
            "_id": row["product_id"],
            "_source": {
                "product_id": row["product_id"],
                "title": row["title"],
                "brand": row["brand"],
                "category": row["category"],
                "category_text": row["category"],
                "colours": colours,
                "colours_text": " ".join(colours),
                "occasion": row["occasion"],
                "gender": row["gender"],
                "price": float(row["price"]),
                "sizes": row["sizes"] or [],
                "in_stock": bool(row["in_stock"]),
                "image_filename": row["image_filename"],
                "source_version": row["source_version"],
            },
        }


def build_index(index_name: str = INDEX_NAME, index_body: dict | None = None) -> int:
    client = get_client()
    body = index_body if index_body is not None else INDEX_BODY

    if client.indices.exists(index=index_name):
        client.indices.delete(index=index_name)
    client.indices.create(index=index_name, body=body)

    with psycopg.connect(get_database_url()) as conn:
        rows = fetch_documents(conn)
        success, errors = bulk(client, to_actions(rows, index_name), chunk_size=2000)

    client.indices.refresh(index=index_name)
    if errors:
        print(f"WARNING: {len(errors)} documents failed to index")
    return success


if __name__ == "__main__":
    count = build_index()
    print(f"Indexed {count} documents into '{INDEX_NAME}'")
