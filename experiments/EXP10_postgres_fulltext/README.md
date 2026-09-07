# EXP10 — PostgreSQL full-text search

- **Role:** Architecture comparison (architecture §14)
- **Status:** Accepted — as a real comparison point, not a serving candidate
- **Run:** `python experiments/EXP10_postgres_fulltext/run.py`
- **Evaluated against:** `evaluation/relevance_judgments.json`, `train`+`val` splits only (15 of 18 queries — `test` held out, see `evaluation/relevance_rubric.md`)

## Hypothesis

Before standing up OpenSearch, is Postgres's built-in full-text search (`tsvector`/`ts_rank`,
`websearch_to_tsquery`) good enough on its own? Architecture §14 lists this explicitly as an
"architecture comparison" experiment.

## Method

`ts_rank` over a weighted `tsvector` (title weight A, category/colour weight B, occasion weight
C), queried with `websearch_to_tsquery` (tolerates free-text input, unlike `plainto_tsquery`).

## Result

**ndcg@10 = 0.355, recall@50 = 0.547** (n=15)

| Query type | ndcg@10 | recall@50 |
|---|---|---|
| exact | 0.217 | 0.414 |
| attribute | 0.533 | 0.785 |
| occasion | 0.138 | 0.226 |
| typo | 0.000 | 0.000 |

(Numbers were revised upward once during this experiment's own analysis — see "A note on the
judgment set" below.)

## A note on the judgment set

Early runs against a smaller judgment set understated every experiment's real performance,
because several genuinely good results simply hadn't been graded yet (an unjudged product
defaults to grade 0 — architecture-standard IR "pooling" issue). `relevance_judgments.json` was
extended twice by pooling top candidates from this experiment and EXP12/13/14's actual result
lists before these final numbers were produced. See `evaluation/relevance_rubric.md`.

## Decision

Accepted as the comparison point that justifies the architecture's OpenSearch choice — see
EXP11/12/14, which all beat it substantially (EXP14: ndcg@10 0.755, +113% relative). Not
promoted to serving. Confirms architecture §4 "baseline first" is the right instinct (this was
worth measuring, not assuming), and gives EXP11-14 something concrete to beat rather than an
assumed floor.
