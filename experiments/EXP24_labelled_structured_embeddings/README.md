# EXP24 — Labelled structured embeddings

- **Role:** Representation comparison (architecture §14)
- **Status:** Accepted — comparison point, not the winner (see EXP22)
- **Run:** `python experiments/EXP24_labelled_structured_embeddings/run.py`
- **Evaluated against:** `evaluation/relevance_judgments.json`, `train`+`val` splits only

## Hypothesis

Same fields as EXP23, but formatted with explicit labels (`"Title: X | Brand: Y | Category: Z |
..."`, `search/embeddings.py:labelled_structured_text`) instead of plain concatenation — does
giving the model explicit field boundaries recover the loss EXP23 showed from mixing metadata
into the title?

## Result

**ndcg@10 = 0.258, recall@50 = 0.397** (n=15) — better than EXP23's plain concatenation (0.218)
but still worse than EXP22's title-only (0.293).

## Finding

Labelling partially recovers the loss from adding metadata (structure helps the model separate
fields somewhat), but doesn't fully close the gap to embedding the title alone — the extra
fields are still net noise for this general-purpose embedding model on this catalogue, whether
or not they're labelled. See EXP22's README for the full comparison table.

## Decision

Accepted as a real, measured comparison point — superseded by EXP22 for the representation
actually carried forward.
