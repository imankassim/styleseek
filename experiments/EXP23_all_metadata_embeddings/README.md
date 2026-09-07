# EXP23 — All-metadata embeddings

- **Role:** Representation comparison (architecture §14)
- **Status:** Accepted — comparison point, not the winner (see EXP22)
- **Run:** `python experiments/EXP23_all_metadata_embeddings/run.py`
- **Evaluated against:** `evaluation/relevance_judgments.json`, `train`+`val` splits only

## Hypothesis

Embed title + brand + category + colour(s) + occasion + gender, concatenated as plain text
(`search/embeddings.py:all_metadata_text`) — more signal available to the model than title alone
(EXP22). By analogy with lexical search, where adding structured fields helped (EXP11→EXP12),
this was expected to help embeddings too.

## Result

**ndcg@10 = 0.218, recall@50 = 0.313** (n=15) — worse than title-only (EXP22: 0.293) on every
metric.

## Finding

The lexical-search analogy doesn't transfer to embeddings: `bge-small-en-v1.5` is trained on
natural sentences, and concatenating disconnected keyword fields onto a title dilutes rather
than enriches the semantic representation — see EXP22's README for the full comparison table and
discussion.

## Decision

Accepted as a real, measured comparison point (not a guess that more fields must help) —
superseded by EXP22 for the representation actually carried forward.
