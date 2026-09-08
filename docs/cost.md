# Cost

Architecture §3.2 NFR "Cost — Search, model and infrastructure costs are measured where
available and discussed alongside quality." Written up at Stage 15+ audit time (2026-09-08) —
not measured continuously throughout the project, since cost wasn't a live concern until this
check. Everything here is objectively measurable from what this project has direct access to
(the database/index connections); exact billing amounts would need each provider's own dashboard,
which this project only has connection-string-level access to, not account/billing access.

## Services used and why

| Service | Tier chosen | Why |
|---|---|---|
| Neon (PostgreSQL) | Free tier | Source of truth for the catalogue — chosen at Stage 4 because no local PostgreSQL/Docker was available (`docs/risk_register.md`). |
| Bonsai (OpenSearch) | "Hobby" plan (Bonsai's own free-tier category name, confirmed by the project owner) | BM25 + vector retrieval — chosen at Stage 8 for the same "no local install" reason. |
| Kaggle dataset | Free, MIT-licensed | Catalogue seed data (`docs/data_sheets/catalogue_data_sheet.md`). |
| `BAAI/bge-small-en-v1.5`, `Qdrant/clip-ViT-B-32-vision` | Free, open-weight, run locally via fastembed/ONNX | Text and image embeddings — no paid inference API used anywhere in this project. |

No LLM API, no paid third-party service, and no cloud compute (training or serving) is used
anywhere in the live system — every model runs locally on this development machine. This is also
why EXP20 (optional LLM query parser) and conversational discovery were the one extension not
pursued (`experiments/experiment_register.md`): everything else in this project's cost profile is
genuinely £0 beyond the two free-tier managed services above, and an LLM API would be the first
recurring paid cost introduced.

## Measured usage (2026-09-08 snapshot)

**PostgreSQL (Neon):**

| What | Size |
|---|---|
| Whole database | 68 MB |
| `product` table | 10 MB |
| `product_variant` table | 49 MB |
| `search_request` (instrumentation) | 368 kB |
| `event` (impressions/clicks) | 136 kB |

**OpenSearch (Bonsai):**

| Index | Documents | Size (primary + replica) |
|---|---|---|
| `styleseek_products_v1` | 44,446 | 10 MB |
| `styleseek_products_v2_synonyms` (live BM25) | 44,446 | 10.1 MB |
| `styleseek_products_v3_vectors` (live semantic, 3 representations) | 44,446 | 404.8 MB |
| `styleseek_products_v5_image_vectors` (visual similarity) | 44,441 (complete) | 178.6 MB |

Vector indices dominate storage, not the operational catalogue data itself — expected, since
each product carries multiple 384-dim or 512-dim float vectors versus a handful of scalar
fields. Total OpenSearch footprint: ~603.5 MB across all four indices. `styleseek_products_v1`
(the pre-synonym base index) is no longer needed by anything live and could be deleted to
reclaim 10 MB; kept for now as it's negligible against the vector indices' footprint and was
never a decision point worth revisiting on its own.

**Request volume**: 653+ real `/search` requests logged during development/testing (see
`monitoring/report.py`) — all from this project's own testing, not genuine independent shoppers
(consistent with `docs/ethics/README.md`'s "no real user testing" limitation).

## Discussion alongside quality

The single largest cost/complexity driver in this project was the vector indices, not the
operational database or the lexical index — and the two highest-value retrieval improvements
(hybrid fusion, Stage 11; visual similarity, the optional extension) are exactly the two features
that needed them. That's a real trade-off worth stating plainly: better relevance and a genuinely
new capability (visual similarity) cost roughly 60x the storage of the base lexical index. At this
project's scale (44,446 products, prototype traffic) both free/hobby tiers comfortably absorbed
it; that would not necessarily hold at a larger catalogue or real production traffic, and re-
checking storage/tier limits would be a reasonable early step before any real deployment
(`docs/monitoring.md`'s deployment section already flags that a real deployment wasn't attempted).

## What isn't measured here

- **Exact monetary cost** — this project has connection-string access to Neon/Bonsai, not billing
  dashboard access; the project owner would need to check those directly for a £ figure.
- **Local compute cost** (electricity, hardware wear for the ~34-80 minute embedding jobs) — not
  tracked, consistent with typical research-prototype practice, but worth naming as excluded
  rather than silently assumed to be zero.
- **CI minutes** (GitHub Actions) — free for public repositories at this project's usage volume;
  not separately measured.
