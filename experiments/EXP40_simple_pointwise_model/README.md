# EXP40 — Simple pointwise model

- **Role:** Learned baseline (architecture §14)
- **Status:** Rejected — see negative-result policy
- **Run:** `python experiments/EXP40_simple_pointwise_model/run.py`
- **Trained on:** `train` split only (11 queries, 178 rows). **Evaluated on:** `val` split only
  (4 queries) — a fitted model can't be fairly evaluated on the data it was trained on, unlike
  EXP32-34 (no fitting involved there).

## Hypothesis

A plain linear model (`sklearn.linear_model.Ridge`) predicting the relevance grade (0-3) from
`ml/learning_to_rank/features.py`'s 9 features (BM25/vector scores, colour/category/gender/
occasion match flags, price, stock), then ranking by predicted score — the simplest thing that
could be called "learned ranking".

## Result

**ndcg@10 = 0.253, recall@50 = 0.683** (n=4) — far below the hybrid fusion baseline (EXP34)
measured the same way on the same 4 val queries: **ndcg@10 = 0.703, recall@50 = 0.733**.

| | ndcg@10 | recall@50 |
|---|---|---|
| EXP34 hybrid fusion (baseline) | 0.703 | 0.733 |
| **EXP40 (this)** | **0.253** | **0.683** |

## Finding

178 training rows across 11 query groups is nowhere near enough to learn a useful combination of
9 features — the model can't reliably separate signal from noise at this scale, and ends up
worse than the already-tuned, hand-weighted 90/10 fusion it's trying to replace. This is exactly
the outcome architecture §16's "too little genuine interaction data" risk and §20's "LightGBM
LambdaRank only after sufficient labelled data" caution predict — confirmed directly rather than
assumed.

## Decision

Rejected — not promoted. Not moved to `discarded/`: like EXP32, it's a documented, necessary
step in the reasoning chain (see EXP41/43 for the same finding replicated across two more model
types) rather than a dead end nobody needed to try.
