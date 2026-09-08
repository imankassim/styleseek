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

## Licence — confirmed (Stage 16)

**MIT.** Kaggle's dataset page renders its licence panel client-side via JavaScript, which
earlier fetch attempts (both a plain `curl` and the agent's own web-fetch tool, which converts
rendered pages to markdown) couldn't see — both returned only the page shell. Confirmed instead
by fetching the raw page HTML with a standard browser User-Agent and reading the page's own
`schema.org` `Dataset` JSON-LD block (a structured-data script tag search engines use, present
in the raw HTML regardless of client-side rendering):

```json
"license": {"@type": "CreativeWork", "name": "MIT", "url": "https://www.mit.edu/~amini/LICENSE.md"}
```

Same result on both the full and small dataset variants (one page's metadata references the
other as an alternate size of the same dataset). MIT is broadly permissive — use, modification
and redistribution are permitted, commercial use included. This resolves architecture §16's
"unlicensed content" risk (`docs/risk_register.md`) for this dataset.

This doesn't retroactively bless anything already done differently: raw dataset files (CSVs,
images) still aren't committed to git — not a licence restriction, just standard practice for
large binary data — and product records here remain a derived, minimal subset (architecture
§2.2, §11).

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
