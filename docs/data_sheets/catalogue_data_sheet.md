# Catalogue Data Sheet — Fashion Product Images Dataset

Governance artefact required by architecture §8.3 (data quality gates), §11 (data provenance)
and §16 ("unlicensed content" risk). Must be completed/confirmed before the dataset is ingested
in Stage 4.

## Source

- **Dataset:** Fashion Product Images Dataset
- **Author/owner:** Param Aggarwal (Kaggle username `paramaggarwal`)
- **URL:** https://www.kaggle.com/datasets/paramaggarwal/fashion-product-images-dataset/data
- **Access method:** `kagglehub.dataset_download("paramaggarwal/fashion-product-images-dataset")`
  (the dataset is too large — several GB of images — for a manual browser download). This
  requires a one-off Kaggle account authentication step, walked through when Stage 4 is reached.
  Downloaded file(s) are kept out of version control (see `.gitignore`) and referenced by local
  cache path only.
- **Local path:** _to be recorded here once downloaded — see `database/data/RAW_DATA_README.md`_

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

## Expected structure (per Kaggle dataset description)

- `styles.csv` — one row per product: `id, gender, masterCategory, subCategory, articleType,
  baseColour, season, year, usage, productDisplayName`
- `images/` — one image per product, filename `<id>.jpg`
- `styles/` (JSON variant, some dataset versions) — per-product JSON with extended attributes
- A smaller ~2,900-row sample subset is commonly distributed alongside the ~44,000-row full set;
  which one is used is recorded once downloaded.

The exact columns are re-verified programmatically against this list during ingestion
(Stage 4) — the ingestion script fails loudly rather than guessing if the schema differs.

## Mapping to StyleSeek entities

| Dataset field | StyleSeek entity.field | Notes |
|---|---|---|
| `id` | `product.product_id` (source id, re-keyed) | |
| `productDisplayName` | `product.title` | |
| `masterCategory` / `subCategory` / `articleType` | `product.category` | Collapsed to a controlled vocabulary — architecture §8.3. |
| `baseColour` | `product_variant.colour` | One product may need synthetic size/colour variants since the dataset itself is not variant-level. |
| `usage` | `product.occasion` | Closest available field; occasion vocabulary may need supplementing. |
| `gender` | `product.attributes.gender` | |
| — (not in dataset) | `product.price`, `product_variant.stock_quantity`, `product_variant.size`, `product_variant.SKU` | **Not present in source data — must be clearly synthetic**, generated with a documented, seeded, reproducible method and labelled as synthetic per architecture §9 ("clearly label any synthetic behavioural data") and §2.2. |
| `images/<id>.jpg` | `product` permitted image | Subject to licence confirmation above. |

## Known limitations

- No real price, stock or size/variant data — must be synthesised and clearly labelled
  (architecture §9 training controls; §16 "poor catalogue metadata" risk).
- No genuine behavioural/interaction data — session/event data will be synthetic or
  self-generated during testing, never presented as real user behaviour (architecture §16, "too
  little genuine interaction data").
- Dataset is a single flat product listing, not variant-aware — the product/variant split
  (architecture §8.1) is StyleSeek's addition, not present in the source.
