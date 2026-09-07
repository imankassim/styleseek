# EXP12 — BM25, boosted structured fields

- **Role:** Lexical tuning (architecture §14)
- **Status:** Accepted — best result among the non-synonym experiments, but superseded by EXP14
  (synonym expansion, ndcg@10 0.755) for serving. Not promoted.
- **Run:** `python experiments/EXP12_bm25_boosted_fields/run.py`
- **Evaluated against:** `evaluation/relevance_judgments.json`, `train`+`val` splits only

## Hypothesis

Two changes on top of EXP11, both motivated directly by EXP11's own results:

1. `type: "cross_fields"` instead of `best_fields` — treats the query fields as one combined
   field, rewarding a document that matches evidence spread *across* several attribute fields,
   which is exactly EXP11's identified weakness.
2. Field boosts (`title^3`, `category_text^2`, `colours_text^2`, `occasion^1`, `brand^1`) so an
   exact title match still outranks an incidental occasion-field match.

## Result

**ndcg@10 = 0.661, recall@50 = 0.687** (n=15) — the best non-synonym lexical configuration.

| Query type | ndcg@10 | recall@50 |
|---|---|---|
| exact | 0.497 | 0.470 |
| attribute | 0.802 | 0.857 |
| occasion | 0.670 | 0.683 |
| typo | 0.000 | 0.000 |

Comparison across all lexical experiments (final numbers, after the judgment pooling pass — see
EXP10's README for why the numbers moved):

| Experiment | ndcg@10 | recall@50 |
|---|---|---|
| EXP10 (Postgres full-text) | 0.355 | 0.547 |
| EXP11 (BM25 equal weights) | 0.552 | 0.570 |
| EXP12 (BM25 boosted + cross_fields) | 0.661 | 0.687 |
| EXP13 (BM25 + fuzziness) — *rejected* | 0.441 | 0.526 |
| **EXP14 (BM25 boosted + synonyms)** | **0.755** | **0.693** |

## Findings

- `exact` was still the weakest category here (0.497) — a chunk of it turned out to be the
  vocabulary gap EXP14 targets directly: "adidas **trainers**" scored ndcg=0.00 in this
  experiment because the catalogue's controlled category vocabulary never uses the word
  "trainers" at all (it's "shoes"/"sandal"/"flip flops" — see `database/ingest.py`), so no
  amount of field boosting helps when the word simply isn't in the index.
- `typo` (rj17, "blu jeens") is still 0.00 — expected, motivated EXP13.

## Decision

Accepted as a real, substantial improvement over EXP10/11 (+86% relative ndcg@10 over Postgres),
but **not promoted to serving** — EXP14 (synonym expansion on top of this same query shape)
measured higher on every query type except typo, most dramatically on `exact` (0.497 → 0.762)
by resolving exactly the vocabulary gap identified above. Kept as the reference for "boosted
fields without synonyms," useful if EXP14's synonym list ever needs isolating as a variable.
