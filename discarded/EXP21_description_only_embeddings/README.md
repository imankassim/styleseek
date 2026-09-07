# EXP21 — Description-only embeddings

- **Role:** Representation comparison (architecture §14)
- **Status:** Rejected before running — no experiment to run
- **Run:** N/A

## Why this wasn't run

The catalogue has no description text at all. `database/ingest.py` sets `product.description =
NULL` for every one of the 44,446 ingested products — the source dataset (`styles.csv`, see
`docs/data_sheets/catalogue_data_sheet.md`) only provides `productDisplayName` (the title) plus
structured attribute columns (category, colour, occasion, gender), never free-text description.

Embedding an empty string for every product would produce (near-)identical vectors across the
entire catalogue, telling a nearest-neighbour search nothing. Running this "experiment" would
not measure anything real — it would just consume compute to produce a number that looks like
evidence but isn't, which is exactly what the evidence rule (architecture §14) warns against:
"No experiment is promoted because it looks more advanced."

## Decision

Rejected without running. The representation comparison that *is* meaningful with this
catalogue's actual data is title-only (EXP22) vs all-metadata (EXP23) vs labelled-structured
(EXP24) — see those experiments' READMEs.
