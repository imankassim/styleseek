# EXP43 — LightGBM LambdaRank

- **Role:** Ranking candidate (architecture §14) — the model architecture §20's final
  recommendation names explicitly, "only after sufficient labelled data"
- **Status:** Rejected for now — data volume is the blocker, not the model
- **Run:** `python experiments/EXP43_lightgbm_lambdarank/run.py`
- **Trained on:** `train` split only (11 query groups, sizes `[14, 13, 20, 15, 21, 16, 12, 17,
  12, 18, 20]`). **Evaluated on:** `val` split only (4 queries).

## Hypothesis

`LGBMRanker` with the LambdaRank objective is ranking-aware — unlike EXP40/41 (pointwise, no
notion of order within a query), it optimises directly for getting the relative order right
within each group. Conservative hyperparameters (7 leaves, 30 trees, `min_child_samples=5`) were
used deliberately — LightGBM's own documentation and architecture §21's cited "LightGBM advanced
topics" both flag that small/sparse ranking data needs conservative settings, not defaults tuned
for much larger datasets.

## Result

**ndcg@10 = 0.252, recall@50 = 0.436** (n=4) — still far below the EXP34 baseline, in line with
EXP40/41.

| | ndcg@10 | recall@50 |
|---|---|---|
| EXP34 hybrid fusion (baseline) | 0.703 | 0.733 |
| EXP40 (linear, pointwise) | 0.253 | 0.683 |
| EXP41 (trees, pointwise) | 0.188 | 0.374 |
| **EXP43 (this, LambdaRank)** | **0.252** | **0.436** |

## Finding

Three different model families (linear, tree ensemble, ranking-aware boosted trees) all land in
the same place: well below the hand-tuned fusion heuristic, on 11 training queries / 178 rows.
This isn't a LightGBM-specific weakness — it's the training-data volume, consistent across every
architecture tried. **This is precisely the scenario architecture §16 names**: "Too little
genuine interaction data — Personalised and two-tower models may appear convincing without
being valid," mitigated by "retain advanced models as experiments" — which is exactly what this
is: a documented experiment, not a shipped feature.

## Decision — G8 gate result

Architecture §17 G8: *"Does learned ranking beat simpler ranking? Grouped validation improves
and fallback works."* **No** — not with the labelled data available right now. EXP34's hybrid
fusion remains the live serving ranker. The feature pipeline
(`ml/learning_to_rank/features.py`), grouped train/val/test infrastructure, and this evaluation
are kept ready — retraining is a matter of re-running this script once the judgment set (or
genuine behavioural data) grows meaningfully larger, not a rebuild.

**A caveat on the evidence itself, in the interest of honesty**: n=4 validation queries is an
extremely small sample — one query ("blu jeens", the typo case every method scores 0.00 on
regardless) makes up a quarter of it. This result is a real, repeated, multi-model signal that
data volume is the bottleneck, not a precise measurement of exactly how much worse learned
ranking is. Both things are true at once.
