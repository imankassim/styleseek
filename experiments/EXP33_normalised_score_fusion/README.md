# EXP33 — Normalised score fusion

- **Role:** Fusion alternative (architecture §14)
- **Status:** Accepted — real improvement over EXP32, superseded by EXP34 for serving
- **Run:** `python experiments/EXP33_normalised_score_fusion/run.py`
- **Evaluated against:** `evaluation/relevance_judgments.json`, `train`+`val` splits only

## Hypothesis

EXP32 (RRF) regressed ndcg@10 because rank-only fusion discards *how much* better one result is
than the next. Does preserving relative score magnitude — min-max normalising each list's raw
scores into [0, 1] before summing (`search/fusion.py:normalised_score_fusion`) — recover that
loss, or is the problem more fundamental (a much weaker ranker dragging down a much stronger one,
regardless of how the combination is done)?

## Result

**ndcg@10 = 0.673, recall@50 = 0.716** (n=15).

| | ndcg@10 | recall@50 |
|---|---|---|
| BM25 alone (EXP31/14) | 0.755 | 0.693 |
| RRF hybrid (EXP32) | 0.549 | 0.707 |
| **Normalised score fusion (this)** | **0.673** | **0.716** |

## Finding

Preserving score magnitude helps substantially over rank-only fusion (ndcg 0.549 → 0.673,
recall still improves to 0.716) — the "how much better" information RRF discards was worth
a lot. But equal-weight combination still costs some ndcg relative to BM25 alone (0.673 vs
0.755): a much weaker ranker (vector, ndcg 0.293) still measurably drags down a much stronger
one (BM25, 0.755) when trusted equally, just less severely than under RRF.

## Decision

Accepted as real, measured progress — not enough on its own to beat BM25-alone's ndcg, which is
exactly what motivated EXP34 (explicit lexical/semantic weighting rather than assuming equal
trust).
