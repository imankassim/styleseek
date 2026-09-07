# EXP2 — Token intersection search

- **Role:** Primitive baseline (architecture §14)
- **Status:** Accepted — as a better floor than EXP1, not as a candidate for serving
- **Fixture:** [`experiments/fixtures/primitive_search_fixture.json`](../fixtures/primitive_search_fixture.json) (12 synthetic products, 10 labelled queries)
- **Run:** `python experiments/EXP2_token_intersection_search/run.py`

## Hypothesis

Splitting the query into tokens and scoring by overlap should recover from EXP1's word-order
failure and handle most queries the same way a naive keyword search would — while still having
no fuzziness, synonyms, or attribute/numeric understanding.

## Method

Split the query on whitespace. Score each product by how many query tokens appear as a substring
somewhere in `title + brand + category + colour + occasion`. Return every product with a
non-zero score, ranked by score (ties keep catalogue order).

## Result

Any-hit rate: **0.90** (9/10 queries), top-1 hit rate: 0.90 — a large jump over EXP1's 0.30.

| Query type | Any-hit rate |
|---|---|
| exact | 1/1 |
| attribute | 3/3 |
| occasion | 1/1 |
| constraint | 1/1 |
| typo | 1/1 |
| broad | 2/2 |
| no_result | 0/1 |

## Findings / failures — the headline number overstates how good this is

The any-hit metric is lenient (it doesn't check precision or true rank quality), and several of
the "hits" above are hollow:

- **The one query type EXP1 got right, EXP2 gets wrong.** `"purple waterproof tuxedo"` (expected:
  no results) now returns `mock-009` ("Black Tuxedo Jacket") purely because the token `"tuxedo"`
  matches. Token overlap trades away EXP1's free true-negative behaviour — any shared word now
  produces a false positive, with no relevance check at all.
- **The occasion "hit" is really a near-complete dump of the catalogue.** For `"smart casual
  outfit for a summer wedding"`, EXP2 returns 10 of 12 products — it isn't understanding
  occasion semantics, it's returning almost everything that shares any single common word
  (`"summer"`, `"casual"`, etc.) with anything. The expected products happen to rank first only
  by catalogue-order tie-breaking, not because the algorithm identified them as more relevant.
- **The constraint "hit" ignores the constraint.** `"petite black work trousers under £40"`
  ranks `mock-004` first, but also returns four other products that violate the price/petite
  constraint outright (there is no price or size field in the searchable text at all — `"£40"`
  and `"petite"` only ever match by coincidence, never by actually checking the number or flag).
- **The typo "hit" isn't typo tolerance.** `"grren satn midi drss"` only matches because the one
  correctly-spelled token, `"midi"`, happens to be enough — `"grren"`, `"satn"` and `"drss"`
  never match anything. A typo in the one token that matters (e.g. `"midi"` → `"midy"`) would
  fail completely; this experiment doesn't demonstrate typo tolerance, it demonstrates partial
  credit disguised as a hit.

## Decision

Retained as a slightly better baseline floor than EXP1, but the failures above are the more
important output of this experiment: they give concrete, named justification for constraint
eligibility (architecture §12, journey 13), fuzziness/synonyms (EXP13/EXP14), and semantic
retrieval (EXP21–24, EXP30) rather than assuming those stages are needed on faith.
