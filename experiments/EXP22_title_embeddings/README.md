# EXP22 — Title-only embeddings

- **Role:** Representation comparison (architecture §14)
- **Status:** Accepted — best of the three representations tested; used as "the" semantic
  representation going forward (EXP30, Stage 11 hybrid fusion)
- **Run:** `python experiments/EXP22_title_embeddings/run.py` (index built by `search/index_vectors.py`)
- **Evaluated against:** `evaluation/relevance_judgments.json`, `train`+`val` splits only, pure
  vector kNN (no lexical signal at all)
- **Model:** `BAAI/bge-small-en-v1.5` via fastembed, 384 dimensions (see `search/embeddings.py`)

## Hypothesis

Embed just the product title (`search/embeddings.py:title_only_text`) — the simplest possible
representation, and (given EXP21 was rejected — no description field exists in this catalogue)
effectively the minimal baseline for the representation comparison.

## Result

**ndcg@10 = 0.293, recall@50 = 0.399** (n=15) — the best of the three representations tested,
and the only one that beat the others on every query type.

| Query type | ndcg@10 |
|---|---|
| exact | 0.216 |
| attribute | 0.444 |
| occasion | 0.066 |
| typo | 0.000 |

Representation comparison:

| Experiment | Representation | ndcg@10 | recall@50 |
|---|---|---|---|
| **EXP22 (this one)** | Title only | **0.293** | **0.399** |
| EXP23 | Title + brand + category + colour + occasion + gender (plain concatenation) | 0.218 | 0.313 |
| EXP24 | Same fields, labelled ("Title: X \| Category: Y \| ...") | 0.258 | 0.397 |

## Findings

Counter-intuitively, adding *more* fields to the embedded text made retrieval worse, not
better — the opposite of what happened with lexical search (EXP11→EXP12, more structured
signal helped). `bge-small-en-v1.5` is a general-purpose sentence embedding model trained on
natural sentences; concatenating disconnected keyword-like fields ("shoes Black Sports Men")
onto a clean title sentence dilutes the semantic content the model actually knows how to embed
well, rather than adding useful signal. Labelling the fields (EXP24) recovers some of the loss
versus plain concatenation (EXP23) but still underperforms the plain title alone.

For reference, every representation here scores far below EXP14's BM25 (ndcg@10 0.755) — vector
retrieval alone is not a stronger *ranker* than tuned lexical search on this attribute-heavy,
keyword-driven query set. That is expected, not a failure: see EXP30 for the actual question
this stage needs to answer (does it add useful *candidates*, not "is it a better ranker alone").

## Decision

Accepted as the representation to carry forward. EXP23/24 remain accepted comparison points
(not rejected — they answered a real question, they just didn't win), kept for the evidence
trail rather than discarded.
