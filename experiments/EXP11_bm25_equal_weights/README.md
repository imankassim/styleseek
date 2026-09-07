# EXP11 — BM25, equal field weights

- **Role:** Lexical baseline (architecture §14)
- **Status:** Accepted — as an intermediate tuning step, superseded by EXP12
- **Run:** `python experiments/EXP11_bm25_equal_weights/run.py`
- **Evaluated against:** `evaluation/relevance_judgments.json`, `train`+`val` splits only

## Hypothesis

A plain OpenSearch `multi_match` across title/category/colour/occasion/brand, no boosting, no
special query type — the simplest thing OpenSearch BM25 can do, as the floor EXP12/13 need to
beat.

## Method

`multi_match` with default type (`best_fields`) across `[title, category_text, colours_text,
occasion, brand]`, equal weight, no boosts.

## Result

**ndcg@10 = 0.552, recall@50 = 0.570** (n=15) — already clears EXP10's Postgres baseline
(0.355) by a wide margin.

| Query type | ndcg@10 | recall@50 |
|---|---|---|
| exact | 0.449 | 0.409 |
| attribute | 0.626 | 0.659 |
| occasion | 0.641 | 0.683 |
| typo | 0.000 | 0.000 |

## Findings

`best_fields` scores each field independently and takes the single best match — this
structurally undersells multi-attribute queries like "black nike shoes", where "black" (colour),
"nike" (title/brand) and "shoes" (category) each live in a *different* field, so no single field
ever sees the whole query. Motivated EXP12's switch to `cross_fields`.

## Decision

Accepted as a real, measured intermediate step — not a guess that boosting would obviously help.
Superseded by EXP12 (ndcg@10 0.661) and then EXP14 (0.755, synonym expansion), not promoted to
serving.
