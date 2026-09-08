# ADR-3: Freeze serving configuration for final evaluation

- Status: Accepted
- Date: 2026-09-08
- Deciders: Project owner (Stage 16, architecture §20 "Conclude" — freeze, held-out evaluation)

## Context

Every configuration decision so far (EXP10-EXP44) was tuned or compared using only the `train`
and `val` judgment splits (`evaluation/relevance_judgments.json`) — confirmed by checking every
experiment's `run.py`, none call `evaluate(..., splits=[..., "test", ...])`. The `test` split
(3 queries: rj15 constraint, rj16 typo, rj18 no_result) has never been used to pick anything.
That makes it the one genuinely held-out set available for a defensible final claim (architecture
G11: "Are the claims supported? Held-out outputs ... published") — but only if nothing changes
after this point that the test split could have influenced, even indirectly.

## Decision

Freeze the following as the final serving configuration, effective this commit. No further
tuning, weight changes, or query-understanding changes are made against evidence involving the
`test` split:

- **Retrieval**: BM25 (EXP14 synonym-expanded index, boosted fields) + vector kNN (EXP22
  title-only `BAAI/bge-small-en-v1.5` embeddings via fastembed), combined with EXP34's 90/10
  weighted score fusion. Live `model_version`: `hybrid_weighted_fusion_v1`, with the two-tier
  fallback (BM25-only, then Postgres token-intersection) documented in
  `backend/app/routers/search.py`.
- **Query understanding**: Stage 9's deterministic parser (colour/gender/price/size as hard
  filters; category/occasion shown but never filtered — the Stage 9 finding).
- **Eligibility and diversity**: Stage 12's stock/size confirmation and (title, category, colour)
  duplicate control.
- **Ranking**: no learned ranker is live — Stage 13 (G8) measured three model families
  (EXP40/41/43) below the hybrid fusion baseline on 178 training rows and rejected all three.
  The feature pipeline (`ml/learning_to_rank/features.py`) is retained, not deleted, in case
  future genuine interaction volume changes that answer.
- **Personalisation**: Stage 14's bounded same-session colour boost, gated on the query having
  no explicit colour, reordering only the top-10 window.

## Consequences

- The held-out evaluation in `evaluation/final_evaluation.md` reflects exactly this
  configuration — a reader can reproduce it against the same live system.
- n=3 for the held-out test split is small enough that its number should be read as indicative,
  not a tight confidence interval — stated plainly in `evaluation/final_evaluation.md` rather
  than presented as more precise than it is.
- Any future change to retrieval, fusion weights, or query understanding after this point (e.g.
  a real deployment gaining enough traffic to revisit Stage 13's G8 answer) supersedes this ADR
  with a new one, the same pattern as ADR-1.

## Evidence

`grep -rn "splits=\[" experiments/` (2026-09-08) confirms no experiment ever evaluated against
the `test` split; `experiments/experiment_register.md`; `evaluation/final_evaluation.md`.
