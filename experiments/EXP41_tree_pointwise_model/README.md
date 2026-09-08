# EXP41 — Tree-based pointwise model

- **Role:** Learned baseline (architecture §14)
- **Status:** Rejected — see negative-result policy
- **Run:** `python experiments/EXP41_tree_pointwise_model/run.py`
- **Trained on:** `train` split only. **Evaluated on:** `val` split only (4 queries).

## Hypothesis

A gradient-boosted tree regressor (`sklearn.ensemble.GradientBoostingRegressor`, deliberately
small: 30 estimators, max depth 2) — can non-linear feature interactions a linear model (EXP40)
can't capture recover the loss?

## Result

**ndcg@10 = 0.188, recall@50 = 0.374** (n=4) — worse than EXP40's already-poor result, and worse
than the EXP34 baseline (0.703/0.733) by a wide margin.

| | ndcg@10 | recall@50 |
|---|---|---|
| EXP34 hybrid fusion (baseline) | 0.703 | 0.733 |
| EXP40 (linear) | 0.253 | 0.683 |
| **EXP41 (this, trees)** | **0.188** | **0.374** |

## Finding

More model capacity made things worse, not better, on 178 rows — a tree ensemble overfits even
faster than a linear model at this scale, exactly the direction the evidence rule warns about
("no experiment is promoted because it looks more advanced"). Confirms EXP40's finding rather
than contradicting it: the bottleneck is data volume, not model choice.

## Decision

Rejected — not promoted. Kept in `experiments/` (not `discarded/`) as part of the same
reasoning chain as EXP40/43.
