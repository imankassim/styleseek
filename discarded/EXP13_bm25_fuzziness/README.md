# EXP13 — BM25 fuzziness

- **Role:** Typo experiment (architecture §14)
- **Status:** Rejected — see negative-result policy (architecture §14)
- **Run:** `python discarded/EXP13_bm25_fuzziness/run.py`
- **Evaluated against:** `evaluation/relevance_judgments.json`, `train`+`val` splits only

## Hypothesis

Add `fuzziness: "AUTO"` on top of EXP12's boosted fields to fix the one typo query (rj17, "blu
jeens") that every prior lexical configuration (EXP10/11/12) scored ndcg=0.00 on identically.

## Method

OpenSearch rejects `fuzziness` on `type: "cross_fields"` outright (`400 parsing_exception:
"Fuzziness not allowed for type [cross_fields]"`). Switched to `type: "most_fields"` — like
cross_fields it sums evidence across matching fields (unlike `best_fields`'s take-the-max
behaviour), and does support fuzziness — same boosted fields as EXP12, `fuzziness: "AUTO"` added.

## Result

**ndcg@10 = 0.441, recall@50 = 0.526** (n=15) — worse than EXP12 (0.661) and far worse than
EXP14 (0.755) on both metrics.

| Query type | EXP12 ndcg@10 | EXP13 ndcg@10 |
|---|---|---|
| exact | 0.497 | 0.387 |
| attribute | 0.802 | 0.523 |
| occasion | 0.670 | 0.224 |
| typo | 0.000 | **0.601** |

## Findings

The fuzziness genuinely worked — rj17 ("blu jeens") went from ndcg 0.00 to 0.601, correctly
surfacing "Blue Jeans" products it previously missed entirely (this also caught a second pooling
gap in the judgment set: the real top matches were different brands, "Kraus"/"Pepe" Jeans, than
the ones originally graded — fixed by pooling these into `relevance_judgments.json` before
scoring, same as the EXP10/12 pooling pass).

But the underlying cause is `most_fields` itself, not the fuzziness: `most_fields` is a weaker
multi-field combination than `cross_fields` for our attribute-heavy queries (it doesn't group
terms per-field before scoring the way cross_fields does), so every other query type regressed —
`occasion` dropped from 0.670 to 0.224, `attribute` from 0.802 to 0.523. One query type improving
by 0.601 wasn't worth every other type losing 0.11–0.45.

## Decision

**Rejected** as configured — moved to `discarded/EXP13_bm25_fuzziness/` per the negative-result
policy: it solves a named problem (typo recovery) but at an unacceptable cost to overall
relevance, and a simpler capability (EXP12 alone) already covers the non-typo majority of
queries better. The evidence rule (architecture §14) is explicit that fixing one problem while
regressing others isn't sufficient grounds to promote a change.

**Follow-up idea, not built here:** a `bool` query with EXP12's `cross_fields` clause as the
primary `should` and a lightweight fuzzy `best_fields` clause as a secondary `should` might get
typo tolerance without regressing the rest — worth a future experiment (would need its own
EXP-ID) rather than assuming it works.
