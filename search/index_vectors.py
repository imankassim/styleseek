"""Builds the vector-enabled index (search/vector_mapping.py) with all three representations
embedded (EXP22 title-only, EXP23 all-metadata, EXP24 labelled-structured) — see
search/embeddings.py for what text each representation embeds.

Usage: python search/index_vectors.py [limit]
  limit: only index this many products (for fast iteration); omit for the full catalogue.
"""

import sys
from pathlib import Path

import psycopg
from opensearchpy.helpers import bulk

sys.path.insert(0, str(Path(__file__).parent))
from embeddings import (  # noqa: E402
    all_metadata_text,
    embed_texts,
    labelled_structured_text,
    title_only_text,
)
from opensearch_client import get_client  # noqa: E402
from vector_mapping import INDEX_BODY, INDEX_NAME  # noqa: E402

sys.path.insert(0, str(Path(__file__).parent.parent / "database"))
from ingest import load_database_url  # noqa: E402


def fetch_products(conn: psycopg.Connection, limit: int | None):
    sql = """
        SELECT
            p.product_id, p.title, p.brand, p.category, p.occasion, p.gender, p.price,
            p.image_filename,
            array_agg(DISTINCT v.colour) AS colours,
            array_agg(DISTINCT v.size) AS sizes,
            bool_or(v.stock_quantity > 0) AS in_stock
        FROM product p
        JOIN product_variant v ON v.product_id = p.product_id
        GROUP BY p.product_id, p.title, p.brand, p.category, p.occasion, p.gender, p.price,
                 p.image_filename
        ORDER BY p.product_id
    """
    if limit is not None:
        sql += " LIMIT %s"
        params = (limit,)
    else:
        params = ()

    with conn.cursor() as cur:
        cur.execute(sql, params)
        columns = [d[0] for d in cur.description]
        return [dict(zip(columns, row, strict=True)) for row in cur]


def build_vector_index(limit: int | None = None, batch_size: int = 1000) -> int:
    client = get_client()
    if client.indices.exists(index=INDEX_NAME):
        client.indices.delete(index=INDEX_NAME)
    client.indices.create(index=INDEX_NAME, body=INDEX_BODY)

    with psycopg.connect(load_database_url()) as conn:
        products = fetch_products(conn, limit)

    print(f"Embedding {len(products)} products x 3 representations...")
    total_indexed = 0
    for start in range(0, len(products), batch_size):
        batch = products[start : start + batch_size]

        title_vecs = embed_texts([title_only_text(p) for p in batch])
        metadata_vecs = embed_texts([all_metadata_text(p) for p in batch])
        structured_vecs = embed_texts([labelled_structured_text(p) for p in batch])

        actions = []
        for product, tv, mv, sv in zip(batch, title_vecs, metadata_vecs, structured_vecs, strict=True):
            actions.append(
                {
                    "_index": INDEX_NAME,
                    "_id": product["product_id"],
                    "_source": {
                        "product_id": product["product_id"],
                        "title": product["title"],
                        "brand": product["brand"],
                        "category": product["category"],
                        "colours": product["colours"] or [],
                        "occasion": product["occasion"],
                        "gender": product["gender"],
                        "price": float(product["price"]),
                        "sizes": product["sizes"] or [],
                        "in_stock": bool(product["in_stock"]),
                        "image_filename": product["image_filename"],
                        "title_vector": tv,
                        "metadata_vector": mv,
                        "structured_vector": sv,
                    },
                }
            )

        success, errors = bulk(client, actions, chunk_size=500)
        total_indexed += success
        if errors:
            print(f"  WARNING: {len(errors)} documents failed in this batch")
        print(f"  {total_indexed}/{len(products)} indexed")

    client.indices.refresh(index=INDEX_NAME)
    return total_indexed


if __name__ == "__main__":
    limit_arg = int(sys.argv[1]) if len(sys.argv) > 1 else None
    count = build_vector_index(limit=limit_arg)
    print(f"Indexed {count} documents into '{INDEX_NAME}'")
