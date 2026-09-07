# EXP31 — BM25-only retrieval

- **Role:** Lexical comparator (architecture §14)
- **Status:** Accepted — not a new experiment, a reference to an existing one
- **Run:** `python experiments/EXP14_synonym_expansion/run.py`

## What this is

Architecture §14 lists "BM25-only retrieval" as its own experiment, role "Lexical comparator" —
the point of comparison Stage 11's hybrid fusion experiments (EXP32 RRF, etc.) measure
themselves against. That configuration already exists and is already the live serving baseline:
**EXP14** (BM25, boosted fields + `cross_fields` + synonym expansion, ndcg@10 0.755, promoted to
serving in Stage 8). Re-running an identical experiment under a second ID would just duplicate
code and results for no reason — the negative-result policy's spirit ("duplicates a simpler
capability") applies here in reverse: don't build a second thing that's identical to the first.

## Decision

EXP31 = EXP14, referenced under this ID for Stage 10/11 comparison purposes. See
`experiments/EXP14_synonym_expansion/README.md` for the full method and results, and
`experiments/EXP30_vector_only_retrieval/README.md` for the semantic-vs-lexical comparison this
experiment exists to support.
