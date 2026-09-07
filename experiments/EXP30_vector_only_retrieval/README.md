# EXP30 — Vector-only retrieval

- **Role:** Semantic baseline (architecture §14)
- **Status:** Accepted — evidence for G6, motivates Stage 11 hybrid fusion
- **Run:** `python experiments/EXP30_vector_only_retrieval/run.py`
- **Representation:** EXP22's winner (title-only embeddings)
- **Compared against:** EXP31 (= EXP14's BM25, the lexical comparator)

## The actual question (G6)

Architecture §17, gate G6: *"Does vector retrieval add useful candidates? Wins and failures are
measured by query type."* This is **not** "is vector-only retrieval a better ranker than BM25" —
EXP22's README already shows plainly that it isn't (ndcg@10 0.293 vs BM25's 0.755), and that's
an expected result for an attribute-heavy, keyword-driven fashion query set against a
general-purpose (not fashion-tuned) embedding model, not a failure of the method.

## Method

For every train/val query with at least one graded-relevant (grade ≥ 2) product, compare the
set of relevant products in BM25's (EXP31) top-50 against vector search's (EXP22
representation) top-50. Count relevant products vector search found that BM25's own candidate
set missed *entirely* — not just ranked lower, genuinely absent from BM25's top 50.

## Result

**5 of 15 queries (33%) had at least one relevant candidate that only vector search found — 7
such candidates total:**

| Query | Products BM25 missed entirely |
|---|---|
| "black nike shoes" | `12695` |
| "green saree" | `31877`, `51101` |
| "formal black trousers" | `29780` |
| "kids summer dress" | `12849` |
| "leather handbag" | `25181`, `25188` |

## Interpretation

Vector retrieval genuinely does add candidates BM25's exact-term matching misses — likely cases
of synonymy or phrasing the BM25 index (even with EXP14's synonym expansion) doesn't cover, that
the embedding model's more general notion of similarity catches instead. This is exactly the
complementary relationship hybrid fusion (Stage 11) is meant to exploit: BM25 as the strong
overall ranker, vector retrieval contributing candidates BM25 would otherwise never surface at
all, regardless of rank.

## Decision

G6 passed: vector retrieval adds useful candidates on a third of queries even where it isn't
competitive as a standalone ranker. Proceed to Stage 11 (RRF hybrid fusion, EXP32) using EXP31
(BM25/EXP14) and this experiment's vector retrieval (EXP22 representation) as the two lists to
combine.
