# EXP1 — Whole-query substring search

- **Role:** Primitive baseline (architecture §14)
- **Status:** Accepted — as the intentional lower bound, not as a candidate for serving
- **Fixture:** [`experiments/fixtures/primitive_search_fixture.json`](../fixtures/primitive_search_fixture.json) (12 synthetic products, 10 labelled queries)
- **Run:** `python experiments/EXP1_substring_search/run.py`

## Hypothesis

The simplest possible thing that could be called "search" — does the whole query string appear
verbatim, in order, anywhere in a product's text — will work for very short, verbatim queries and
fail for almost everything else, giving a true floor to compare later retrieval methods against.

## Method

For each product, concatenate `title + brand + category + colour + occasion` and lowercase it.
A product matches if the trimmed, lowercased query is a substring of that text. No tokenisation.

## Result

Any-hit rate: **0.30** (3/10 queries), top-1 hit rate: 0.30.

| Query type | Any-hit rate |
|---|---|
| exact | 0/1 |
| attribute | 0/3 |
| occasion | 0/1 |
| constraint | 0/1 |
| typo | 0/1 |
| broad | 2/2 |
| no_result | 1/1 |

## Findings / failures

- **Fails on word order.** `"black adidas trainers"` misses `mock-001` ("Adidas Cloudline
  Trainers … black casual") purely because the query's word order doesn't match the
  concatenated product text's word order — not because the product is irrelevant. This is the
  headline failure mode of whole-query substring matching and the reason EXP2 exists.
- **Only "succeeds" on queries that are already a verbatim substring of some product's text**
  (`"midi dress"`, `"trainers"`) — i.e. on queries a user is unlikely to always phrase correctly.
- **Gets the one no-result query right "for free".** Returning nothing when nothing matches
  verbatim is a correct behaviour here, but it's a side effect of being maximally strict, not
  evidence of good no-result handling — a query one character off (typo) fails identically.
- Zero attribute, occasion, constraint or typo queries succeed at all.

## Decision

Retained as the documented lower-bound baseline (negative-result policy, architecture §14) —
not promoted, not deleted. Every later retrieval stage (BM25 at G5, hybrid at G7) is expected to
clear this floor by a wide margin; if one doesn't, that is itself a finding worth recording.
