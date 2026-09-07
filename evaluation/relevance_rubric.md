# Relevance Rubric

Defines how query-product relevance is graded for
[`relevance_judgments.json`](relevance_judgments.json), the labelled query set used by the
offline evaluation harness (Stage 8, NDCG@10 / Recall@50 — architecture §3.3, §9).

## Grades

| Grade | Meaning | Guidance |
|---|---|---|
| 3 | Highly relevant | Matches every explicit part of the query (brand, colour, category, occasion, and any stated constraint). What a shopper searching this exact query would want to see near the top. |
| 2 | Relevant | Matches the core intent but with a minor mismatch — an adjacent variant, a near-synonym material/attribute (e.g. "leatherette" for "leather"), or a plausible-but-not-ideal occasion fit. |
| 1 | Marginally relevant | Shares some terms or category with the query but misses a key attribute (wrong colour, wrong specific sub-type). A shopper would recognise why it appeared, but wouldn't consider it a good answer. |
| 0 | Irrelevant | Does not satisfy the query's intent — wrong category, wrong explicit constraint (e.g. over a stated price cap), or only a coincidental word match (architecture §16 "position-biased clicks" / false-positive risk this rubric exists to catch). |

## Grading rules

1. **Grade the full query intent, not individual words.** A product matching one keyword but
   violating an explicit constraint (price, category) is graded on the constraint violation, not
   the keyword match — see query `rj15` ("red dress under £50") where genuinely red dresses
   priced over £50 are graded 0, not 2 or 3, specifically to test constraint-satisfaction later
   (Stage 12, eligibility rules).
2. **No-result queries are graded by absence, not by weak positive grades.** `rj18` ("purple
   waterproof tuxedo") has an empty `graded_products` list because the catalogue genuinely has no
   tuxedo products (confirmed by direct query against the live database) — a system returning
   zero results for it should score well, not poorly, for that query.
3. **Typo queries are graded against the corrected intent.** `rj16`/`rj17` grade products as if
   the query had been spelled correctly — the point of these queries is to measure whether a
   retrieval method recovers from the typo, not to redefine what's relevant.
4. **Grades are assigned by inspecting real catalogue rows**, not guessed — every product in
   `relevance_judgments.json` was looked up against the live database before grading (see the
   `source_check` note per query for how candidates were found).
5. **This is a small, hand-built set**, not a statistically representative sample of shopper
   queries — sufficient to unit-test evaluation code and give an early evidence signal (Stage 8),
   not sufficient on its own to make strong final claims (architecture §16, "too little genuine
   interaction data" — the same caution applies to hand-built judgments at this scale).

## Query-level train/validation/test split

Per architecture §9 training controls: split **by query**, not by row, and the test split stays
untouched until model selection is complete (G4). Each query in the judgment set carries a
`split` field (`train` / `val` / `test`). Do not use `test`-split queries to tune retrieval,
fusion, or ranking configuration before the final held-out evaluation (Stage 16) — doing so
defeats the purpose of holding them out at all.
