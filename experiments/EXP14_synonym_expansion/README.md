# EXP14 — Synonym expansion

- **Role:** Vocabulary experiment (architecture §14)
- **Status:** **Accepted and promoted to serving** — replaces EXP12 as the live `/search`
  implementation, model version `bm25_opensearch_synonyms_v1`.
- **Run:** `python experiments/EXP14_synonym_expansion/run.py` (builds its own index each run)
- **Evaluated against:** `evaluation/relevance_judgments.json`, `train`+`val` splits only

## Hypothesis

Architecture §2.3's own target-journey examples use the word "trainers" throughout, but the
catalogue's controlled category vocabulary (`database/ingest.py`) never contains that word at
all — it's "shoes"/"sandal"/"flip flops". A shopper who searches "trainers" gets zero
category-field credit no matter how well the fields are boosted (confirmed directly in EXP12's
findings: rj3 "adidas trainers" scored ndcg=0.00 there). Same story for "jeans" vs "denim",
"purse" vs "handbag", "frock" vs "dress".

## Method

A separate index (`styleseek_products_v2_synonyms` — synonym filters are index-time settings,
can't be bolted onto EXP12's existing index) with a `synonym` token filter applied via a custom
analyzer, used for both indexing and querying. Same query shape as EXP12 (`cross_fields` +
boosted fields) otherwise, so this experiment isolates the synonym effect. Synonym set (a small,
hand-picked fashion vocabulary, not exhaustive — see `synonym_mapping.py`):

```
trainers, sneakers, shoes
jeans, denim
frock, dress
purse, handbag, bag
tee, tshirt, t-shirt
trousers, pants
jumper, sweater
saree, sari
```

## Result

**ndcg@10 = 0.755, recall@50 = 0.693** (n=15) — the best of every lexical experiment run.

| Query type | ndcg@10 | recall@50 |
|---|---|---|
| exact | 0.762 | 0.570 |
| attribute | 0.879 | 0.829 |
| occasion | 0.670 | 0.683 |
| typo | 0.000 | 0.000 |

Full comparison (final numbers, all against the same pooled judgment set):

| Experiment | ndcg@10 | recall@50 |
|---|---|---|
| EXP10 (Postgres full-text) | 0.355 | 0.547 |
| EXP11 (BM25 equal weights) | 0.552 | 0.570 |
| EXP12 (BM25 boosted + cross_fields) | 0.661 | 0.687 |
| EXP13 (BM25 + fuzziness) — *rejected* | 0.441 | 0.526 |
| **EXP14 (BM25 boosted + synonyms)** | **0.755** | **0.693** |

## A build bug worth recording

The first run of this experiment produced misleadingly plausible-looking numbers (ndcg@10
0.565) from the **wrong index** — `run.py` imported a local `mapping.py`, but `search/index.py`
(which this experiment also imports) does its own `from mapping import ...` internally, and
Python caches modules by name in `sys.modules` regardless of which directory a same-named module
lives in or what order `sys.path` was manipulated. The cached module — `search/mapping.py`, the
plain non-synonym one — won every subsequent `from mapping import ...`, so this experiment
silently rebuilt the **production index** with the wrong (non-synonym) settings and then
benchmarked that. Caught only by checking `client.cat.indices()` and noticing only one index
existed. Fixed by renaming the local file to `synonym_mapping.py` — no name shared with anything
`search/index.py` imports. No data was lost (the rebuild used identical document content, just
the wrong mapping), but the lesson generalises: two experiments that both do path-based
`sys.path` imports of same-named local files are not isolated from each other just because
they live in different directories.

## A note on the judgment set — this experiment is why it grew twice

The first fair run of this experiment (correct index, still using the *original* judgment set)
scored ndcg@10 = 0.501 — *worse* than EXP12. Investigating rj3 ("adidas trainers", still 0.00)
showed the synonym expansion was working exactly as intended (`client.indices.analyze` confirmed
"trainers" → also indexed as "sneakers"/"shoes") and correctly surfacing genuinely relevant
products like "ADIDAS Men Black Shoes" — they just weren't in the judgment set yet, so they
scored as irrelevant by default. This was the third time the same pooling-bias pattern showed up
in Stage 8 (also hit by EXP10's first run and EXP13's typo query), so rather than patch one more
query, `relevance_judgments.json` got a second, thorough pooling pass across every experiment's
actual top results before any final numbers were trusted — see `evaluation/relevance_rubric.md`
and the other experiments' READMEs for the same note.

## Decision

Promoted to serving (G5: "Is BM25 a credible tuned baseline?" — yes: +113% relative ndcg@10 over
the Postgres comparison point, and a specific, named, verified mechanism for the improvement,
not just a bigger number). `backend/app/routers/search.py` now queries this synonym-enabled
index with EXP12's query shape, with a documented fallback to the Stage 5 Postgres placeholder
if OpenSearch is unavailable (architecture §10).

**Known remaining gap:** typo queries (rj17) still score 0.00 — EXP13 showed that naively adding
fuzziness elsewhere costs more than it's worth; combining synonym expansion with fuzzy matching
(rather than either alone) is a reasonable follow-up but wasn't tested here and shouldn't be
assumed to work without measuring it.
