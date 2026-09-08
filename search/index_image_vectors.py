"""Builds the visual similarity index (search/image_vector_mapping.py) by embedding each
catalogue product's photo with CLIP (fastembed/ONNX, `Qdrant/clip-ViT-B-32-vision`, no torch —
same runtime convention as search/embeddings.py's text models). Products with no image
(`image_filename IS NULL` — 5 of 44,446, see docs/data_sheets/catalogue_data_sheet.md) are
skipped, not embedded as a blank/zero vector.

Usage: python search/index_image_vectors.py [limit]
  limit: only index this many products (for fast iteration); omit for the full catalogue
  (~44,441 images, measured ~34 minutes on this machine, threads=4 — see
  docs/progress.md's visual similarity extension notes).
"""

import sys
from pathlib import Path

import kagglehub
import psycopg
from fastembed import ImageEmbedding
from opensearchpy.helpers import bulk

sys.path.insert(0, str(Path(__file__).parent))
from image_vector_mapping import INDEX_BODY, INDEX_NAME  # noqa: E402
from opensearch_client import get_client  # noqa: E402

sys.path.insert(0, str(Path(__file__).parent.parent / "database"))
from ingest import load_database_url  # noqa: E402

MODEL_NAME = "Qdrant/clip-ViT-B-32-vision"


def fetch_products_with_images(conn: psycopg.Connection, limit: int | None):
    sql = "SELECT product_id, image_filename FROM product WHERE image_filename IS NOT NULL ORDER BY product_id"
    if limit is not None:
        sql += " LIMIT %s"
        params = (limit,)
    else:
        params = ()
    with conn.cursor() as cur:
        cur.execute(sql, params)
        return cur.fetchall()


def build_image_index(limit: int | None = None, batch_size: int = 256) -> int:
    images_dir = Path(kagglehub.dataset_download("paramaggarwal/fashion-product-images-small")) / "images"

    client = get_client()
    if client.indices.exists(index=INDEX_NAME):
        client.indices.delete(index=INDEX_NAME)
    client.indices.create(index=INDEX_NAME, body=INDEX_BODY)

    with psycopg.connect(load_database_url()) as conn:
        products = fetch_products_with_images(conn, limit)

    model = ImageEmbedding(model_name=MODEL_NAME, threads=4)

    total_indexed = 0
    total_missing_file = 0
    for start in range(0, len(products), batch_size):
        batch = products[start : start + batch_size]
        paths = [images_dir / image_filename for _, image_filename in batch]

        present = [(pid, str(path)) for (pid, _), path in zip(batch, paths, strict=True) if path.is_file()]
        total_missing_file += len(batch) - len(present)
        if not present:
            continue

        vectors = list(model.embed([path for _, path in present], batch_size=32))

        actions = [
            {
                "_index": INDEX_NAME,
                "_id": product_id,
                "_source": {"product_id": product_id, "image_vector": vector.tolist()},
            }
            for (product_id, _), vector in zip(present, vectors, strict=True)
        ]
        success, errors = bulk(client, actions, chunk_size=500)
        total_indexed += success
        if errors:
            print(f"WARNING: {len(errors)} documents failed to index in this batch")
        print(f"  {total_indexed}/{len(products)} embedded and indexed...")

    client.indices.refresh(index=INDEX_NAME)
    if total_missing_file:
        print(f"WARNING: {total_missing_file} rows had image_filename set but no file on disk")
    return total_indexed


if __name__ == "__main__":
    row_limit = int(sys.argv[1]) if len(sys.argv) > 1 else None
    count = build_image_index(limit=row_limit)
    print(f"Indexed {count} image vectors into '{INDEX_NAME}'")
