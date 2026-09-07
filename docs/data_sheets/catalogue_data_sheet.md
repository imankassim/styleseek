# Catalogue Data Sheet — Fashion Product Images Dataset

Governance artefact required by architecture §8.3 (data quality gates), §11 (data provenance)
and §16 ("unlicensed content" risk). Must be completed/confirmed before the dataset is ingested
in Stage 4.

## Source

- **Dataset used:** `paramaggarwal/fashion-product-images-small` — **not** the full
  `fashion-product-images-dataset` originally linked. The full dataset's image archive is 23.1GB;
  this machine's disk didn't have room even after cleanup (see risk register). The "small"
  variant has the identical `styles.csv` catalogue/metadata (44,446 rows, same schema) with
  lower-resolution images, which doesn't affect search/ranking work at all.
- **Author/owner:** Param Aggarwal (Kaggle username `paramaggarwal`)
- **URL:** https://www.kaggle.com/datasets/paramaggarwal/fashion-product-images-dataset/data
  (small variant: https://www.kaggle.com/datasets/paramaggarwal/fashion-product-images-small)
- **Access method:** `kagglehub.dataset_download("paramaggarwal/fashion-product-images-small")`,
  authenticated via a Kaggle API token at `~/.kaggle/access_token` (kagglehub's newer
  single-token auth, resolved by `kagglesdk.kaggle_env.get_access_token_from_env`). Downloaded
  files are kept out of version control — kagglehub caches them under
  `~/.cache/kagglehub/datasets/...`, outside the repo entirely.
- **Local path (this machine):** `~/.cache/kagglehub/datasets/paramaggarwal/fashion-product-images-small/versions/1/`
  (`styles.csv` + `images/*.jpg`, 44,446 rows, 44,441 with a matching image file — 5 rows have
  no image).

## Licence — ⚠ action required before ingestion

Kaggle lists a licence for this dataset on its page, which could not be confirmed
programmatically (the page is JavaScript-rendered and not fetchable as plain text from this
environment). **Before any product record or image derived from this dataset is used beyond
local experimentation, or committed/shared in this repository, confirm the exact licence text
shown on the Kaggle dataset page and paste it below.**

> Licence text (paste from Kaggle "Usability"/"License" panel): `PENDING — confirm on Kaggle`

Until confirmed:

- Raw dataset files (CSVs, images) are **not** committed to git — this repo only holds derived,
  minimal fields needed for the prototype schema, and only once licence terms are confirmed to
  permit that use.
- No dataset imagery or text is used in any public-facing demo/deployment without that
  confirmation.
- This mirrors architecture §2.2 ("no unlicensed content") and §11 ("data provenance").

## Confirmed structure

- `styles.csv` — 44,446 rows, columns exactly: `id, gender, masterCategory, subCategory,
  articleType, baseColour, season, year, usage, productDisplayName`. No missing `id` or
  `productDisplayName` values.
- `images/` — one image per product, filename `<id>.jpg`. 44,441 of 44,446 rows have a matching
  file (5 do not — `image_filename` is left `NULL` for those, not rejected outright).
- `masterCategory` has 7 distinct values, `subCategory` has 44. Ingestion's controlled vocabulary
  (`database/ingest.py`, `ALLOWED_MASTER_CATEGORIES` / `ALLOWED_SUB_CATEGORIES`) is the observed
  union of both, lowercased — every row in this snapshot was accepted (0 rejected on the full run).

## Mapping to StyleSeek entities (as implemented in `database/ingest.py`)

| Dataset field | StyleSeek entity.field | Notes |
|---|---|---|
| `id` | `product.product_id` | Used verbatim as the primary key. |
| `productDisplayName` | `product.title` | |
| `subCategory` (falling back to `masterCategory`) | `product.category` | Controlled vocabulary — architecture §8.3. |
| `baseColour` | `product_variant.colour` | Real dataset value — colour is not synthetic. |
| `usage` | `product.occasion` | Closest available field. |
| `gender` | `product.gender` | |
| `images/<id>.jpg` (if present) | `product.image_filename` | Subject to the licence confirmation above — stored as a local reference only, not served publicly. |
| — (not in dataset) | `product.price` | **Synthetic** — seeded by `sha256(product_id)`, category-priced band, `is_synthetic_price = TRUE`. Reproducible: re-ingesting yields identical prices. |
| — (not in dataset) | `product_variant.size`, `.sku`, `.stock_quantity` | **Synthetic** — a fixed size run per category (footwear/bottoms/tops/one-size), seeded stock per `(product_id, size)`, `is_synthetic_variant = TRUE`. |
| — (not in dataset) | `product_variant.colour` count | Each product gets exactly one colour (the dataset's `baseColour`) × its category's size run as variants — real multi-colour variants aren't in the source data, so this isn't simulated either. |

Result of the full ingestion run: **44,446 products, 216,108 variants, 0 rejected.**

## Known limitations

- No real price or stock data — synthesised as above, and flagged (`is_synthetic_price`,
  `is_synthetic_variant`) rather than presented as real (architecture §9, §2.2).
- Only one colour per product (the dataset's own `baseColour`) — genuine colour-variant
  products aren't represented; this is a limitation of the source data, not simulated.
- No genuine behavioural/interaction data — session/event data will be synthetic or
  self-generated during testing, never presented as real user behaviour (architecture §16, "too
  little genuine interaction data").
- Dataset is a single flat product listing, not variant-aware — the product/variant split
  (architecture §8.1) is StyleSeek's addition, not present in the source.
