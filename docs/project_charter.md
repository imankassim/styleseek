# StyleSeek — Project Charter

Source: `STYLESEE1.docx` §1–3. See [`docs/architecture/STYLESEEK_ARCHITECTURE.md`](architecture/STYLESEEK_ARCHITECTURE.md)
for the full architecture this charter sits under.

## Problem

StyleSeek is an original fashion e-commerce prototype, inspired by (but not a copy of) the
shopping journeys used by large online retailers. It exists to investigate whether a staged
hybrid search system can improve product discovery over a credible keyword baseline.

**Primary research question.** To what extent does hybrid lexical and semantic retrieval,
followed by learning-to-rank, improve fashion-product search relevance compared with a tuned
BM25 baseline?

## Users

Shoppers who search using a mix of exact product terms, structured attributes, occasion/style
language, spelling variants, and hard constraints (price, size, category, stock) — no single
retrieval method handles all of these well on its own.

## Scope

**In scope** (see architecture §2.1 for the full list): responsive Next.js storefront, product
catalogue (products/variants/colours/sizes/prices/stock), FastAPI backend, PostgreSQL source of
truth, OpenSearch lexical + vector index, query understanding, RRF fusion, LightGBM
learning-to-rank, bounded anonymous session personalisation, evaluation and monitoring.

**Out of scope initially** (architecture §2.2): real payments/fulfilment, ASOS branding or
proprietary assets, production-scale identity platform, unrestricted LLM control of
filters/ranking, unvalidated transformer/two-tower models, unreviewed automatic retraining.

## Intended outcomes

- A working, evidence-led progression from a static page to an evaluated hybrid ML search
  service, with every stage validated against the previous one (architecture §17, decision
  gates).
- A reproducible experiment trail — including rejected experiments — supporting the research
  question with NDCG@10, Recall@50, no-result rate, constraint-violation rate, and latency
  evidence (architecture §3.3).
- Documentation suitable as Level 7 apprenticeship evidence (architecture §19), while remaining
  an original, honestly-scoped learning prototype rather than a production system.

## Data source

Product catalogue seed data: [Fashion Product Images Dataset](https://www.kaggle.com/datasets/paramaggarwal/fashion-product-images-dataset/data)
(Kaggle, Param Aggarwal). Provenance, licence and usage terms are tracked in
[`docs/data_sheets/catalogue_data_sheet.md`](data_sheets/catalogue_data_sheet.md) before any
ingestion — per architecture §11 (data provenance) and §2.2 (no unlicensed content).

## Governing documents

- [`docs/architecture/STYLESEEK_ARCHITECTURE.md`](architecture/STYLESEEK_ARCHITECTURE.md) — full architecture (source of truth: `STYLESEE1.docx`)
- [`experiments/experiment_register.md`](../experiments/experiment_register.md) — planned/run/rejected experiments
- [`docs/risk_register.md`](risk_register.md) — risks, assumptions, mitigations
- [`docs/decisions/`](decisions/) — architecture decision records (ADRs)
- [`docs/data_sheets/`](data_sheets/) — catalogue provenance and permitted-data rules
