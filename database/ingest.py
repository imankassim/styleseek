"""Ingest the Kaggle fashion product catalogue into PostgreSQL.

Source: paramaggarwal/fashion-product-images-small (Kaggle), downloaded via kagglehub.
See docs/data_sheets/catalogue_data_sheet.md for provenance, the field mapping, and the open
licence-confirmation gate this ingestion does not resolve on its own.

The source dataset has no price, stock, size or variant data. Those are generated here with a
seeded, deterministic method so re-running ingestion is reproducible — and are explicitly
flagged (`is_synthetic_price`, `is_synthetic_variant`) rather than presented as real (data sheet
mapping table; architecture §9 "clearly label any synthetic behavioural data").

Quality gates enforced here (beyond what the DB schema itself enforces — see migrations/1_initial_schema.sql):
  - required columns present and non-empty (id, productDisplayName, category fields)
  - category collapsed to an allowed, controlled vocabulary
  - rows failing a gate are quarantined (written to a rejects file with a reason), not dropped
    silently and not inserted (architecture §8.3: "Failure prevents or quarantines an invalid
    downstream update.")
"""

import csv
import hashlib
import os
import random
import sys
from pathlib import Path

import psycopg

SOURCE_DATASET = "paramaggarwal/fashion-product-images-small"

# The controlled vocabulary is the dataset's own masterCategory/subCategory taxonomy
# (both, lowercased) as observed in styles.csv — not a hand-guessed subset. A future re-ingest
# against a changed/corrupted source will still be gated: anything outside this observed set is
# quarantined rather than silently accepted (architecture §8.3).
ALLOWED_MASTER_CATEGORIES = {
    "accessories",
    "apparel",
    "footwear",
    "free items",
    "home",
    "personal care",
    "sporting goods",
}

ALLOWED_SUB_CATEGORIES = {
    "accessories",
    "apparel set",
    "bags",
    "bath and body",
    "beauty accessories",
    "belts",
    "bottomwear",
    "cufflinks",
    "dress",
    "eyes",
    "eyewear",
    "flip flops",
    "fragrance",
    "free gifts",
    "gloves",
    "hair",
    "headwear",
    "home furnishing",
    "innerwear",
    "jewellery",
    "lips",
    "loungewear and nightwear",
    "makeup",
    "mufflers",
    "nails",
    "perfumes",
    "sandal",
    "saree",
    "scarves",
    "shoe accessories",
    "shoes",
    "skin",
    "skin care",
    "socks",
    "sports accessories",
    "sports equipment",
    "stoles",
    "ties",
    "topwear",
    "umbrellas",
    "vouchers",
    "wallets",
    "watches",
    "water bottle",
    "wristbands",
}

FOOTWEAR_CATEGORIES = {"shoes", "sandal", "flip flops", "shoe accessories"}
BOTTOM_CATEGORIES = {"bottomwear"}
TOP_CATEGORIES = {"topwear", "dress", "apparel set", "innerwear", "loungewear and nightwear", "saree"}

FOOTWEAR_SIZES = ["4", "5", "6", "7", "8", "9", "10", "11"]
BOTTOM_SIZES = ["26", "28", "30", "32", "34", "36"]
TOP_SIZES = ["XS", "S", "M", "L", "XL", "XXL"]
ONE_SIZE = ["One Size"]


def load_database_url() -> str:
    env_path = Path(__file__).parent / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            if line.startswith("DATABASE_URL="):
                return line.split("=", 1)[1].strip()
    url = os.environ.get("DATABASE_URL")
    if not url:
        msg = "DATABASE_URL not found in database/.env or the environment."
        raise RuntimeError(msg)
    return url


def seeded_random(product_id: str) -> random.Random:
    seed = int(hashlib.sha256(product_id.encode()).hexdigest(), 16) % (2**32)
    return random.Random(seed)


def synthetic_price(product_id: str, category: str) -> float:
    rng = seeded_random(product_id)
    bands = {
        "shoes": (30, 110),
        "sandal": (20, 70),
        "flip flops": (8, 25),
        "dress": (25, 90),
        "bags": (20, 120),
        "watches": (25, 200),
        "jewellery": (10, 80),
    }
    low, high = bands.get(category, (8, 60))
    return round(rng.uniform(low, high), 2)


def size_run_for(category: str) -> list[str]:
    if category in FOOTWEAR_CATEGORIES:
        return FOOTWEAR_SIZES
    if category in BOTTOM_CATEGORIES:
        return BOTTOM_SIZES
    if category in TOP_CATEGORIES:
        return TOP_SIZES
    return ONE_SIZE


def synthetic_stock(product_id: str, size: str) -> int:
    rng = seeded_random(f"{product_id}:{size}")
    if rng.random() < 0.1:
        return 0
    return rng.randint(1, 40)


def normalise_category(master_category: str, sub_category: str) -> str | None:
    sub = sub_category.strip().lower()
    if sub in ALLOWED_SUB_CATEGORIES:
        return sub
    master = master_category.strip().lower()
    if master in ALLOWED_MASTER_CATEGORIES:
        return master
    return None


def read_rows(styles_csv_path: Path):
    with open(styles_csv_path, encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        for row in reader:
            yield row


def validate_row(row: dict) -> tuple[str | None, str | None]:
    """Returns (category, rejection_reason). category is None if rejected."""
    product_id = (row.get("id") or "").strip()
    title = (row.get("productDisplayName") or "").strip()
    if not product_id:
        return None, "missing id"
    if not title:
        return None, "missing productDisplayName"

    category = normalise_category(row.get("masterCategory", ""), row.get("subCategory", ""))
    if category is None:
        return None, f"category not in controlled vocabulary: {row.get('subCategory')!r}/{row.get('masterCategory')!r}"

    return category, None


def ingest(
    styles_csv_path: Path,
    database_url: str,
    images_dir: Path | None = None,
    limit: int | None = None,
) -> None:
    accepted = 0
    rejected: list[tuple[str, str]] = []
    existing_images = set(os.listdir(images_dir)) if images_dir and images_dir.is_dir() else None

    with psycopg.connect(database_url, autocommit=False) as conn, conn.pipeline(), conn.cursor() as cur:
        for i, row in enumerate(read_rows(styles_csv_path)):
            if limit is not None and i >= limit:
                break

            category, reason = validate_row(row)
            product_id = (row.get("id") or f"row{i}").strip()
            if category is None:
                rejected.append((product_id, reason))
                continue

            title = row["productDisplayName"].strip()
            brand = None  # not present in this dataset
            colour = (row.get("baseColour") or "unknown").strip() or "unknown"
            occasion = (row.get("usage") or "").strip() or None
            gender = (row.get("gender") or "").strip() or None
            price = synthetic_price(product_id, category)
            image_filename = f"{product_id}.jpg"
            if existing_images is not None and image_filename not in existing_images:
                image_filename = None

            cur.execute(
                """
                INSERT INTO product (
                    product_id, title, brand, category, material, fit, occasion,
                    description, price, gender, source_dataset, source_row_id,
                    is_synthetic_price, image_filename
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, TRUE, %s)
                ON CONFLICT (product_id) DO UPDATE SET
                    title = EXCLUDED.title,
                    category = EXCLUDED.category,
                    occasion = EXCLUDED.occasion,
                    price = EXCLUDED.price,
                    image_filename = EXCLUDED.image_filename,
                    updated_at = now()
                """,
                (
                    product_id,
                    title,
                    brand,
                    category,
                    None,
                    None,
                    occasion,
                    None,
                    price,
                    gender,
                    SOURCE_DATASET,
                    product_id,
                    image_filename,
                ),
            )

            for size in size_run_for(category):
                variant_id = f"{product_id}-{colour[:3].upper()}-{size}".replace(" ", "")
                sku = variant_id
                stock = synthetic_stock(product_id, size)
                cur.execute(
                    """
                    INSERT INTO product_variant (
                        variant_id, product_id, colour, size, sku, stock_quantity,
                        is_synthetic_variant
                    ) VALUES (%s, %s, %s, %s, %s, %s, TRUE)
                    ON CONFLICT (variant_id) DO UPDATE SET
                        stock_quantity = EXCLUDED.stock_quantity
                    """,
                    (variant_id, product_id, colour, size, sku, stock),
                )

            accepted += 1

        conn.commit()

    print(f"Accepted: {accepted}")
    print(f"Rejected: {len(rejected)}")

    if rejected:
        report_path = Path(__file__).parent / "data" / "ingestion_rejects.csv"
        report_path.parent.mkdir(parents=True, exist_ok=True)
        with open(report_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["product_id", "reason"])
            writer.writerows(rejected)
        print(f"Rejected rows written to {report_path}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python database/ingest.py <path to styles.csv> [images_dir] [limit]")
        sys.exit(1)

    csv_path = Path(sys.argv[1])
    images_path = Path(sys.argv[2]) if len(sys.argv) > 2 and sys.argv[2] != "-" else None
    row_limit = int(sys.argv[3]) if len(sys.argv) > 3 else None
    ingest(csv_path, load_database_url(), images_dir=images_path, limit=row_limit)
