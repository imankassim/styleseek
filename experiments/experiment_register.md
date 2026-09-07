# Experiment Register

Working register of every planned, running, completed and rejected experiment. Source list of
planned experiments: `STYLESEE1.docx` §14 (which numbers them `EXP-001`, `EXP-010`, etc.) — this
register and every experiment folder use a plain, unpadded numbering instead (`EXP1`, `EXP10`,
...); the mapping is 1:1 in document order. Each experiment gets its own folder under
`experiments/<EXPn>_<slug>/` once it is started, with its config, code/notebook and results.
Rejected experiments move to `discarded/<EXPn>_<slug>/` with a short reason, per the
negative-result policy (architecture §14): an experiment is rejected because it lowers
relevance, increases latency, adds operational complexity, relies on weak synthetic behaviour,
creates governance concerns, or duplicates a simpler capability — never just because it looks
less advanced.

Status values: `Not started` · `In progress` · `Accepted` · `Rejected`.

| Experiment | Possibility considered | Role | Status | Decision / notes |
|---|---|---|---|---|
| EXP1 | Whole-query substring search | Primitive baseline | Accepted | Intentional lower bound, any-hit rate 0.30/10. See `experiments/EXP1_substring_search/README.md`. |
| EXP2 | Token intersection search | Primitive baseline | Accepted | Better floor than EXP1 (any-hit 0.90/10) but with real false positives (no-result query) and hollow "wins" on occasion/constraint queries — see `experiments/EXP2_token_intersection_search/README.md`. |
| EXP10 | PostgreSQL full-text search | Architecture comparison | Not started | |
| EXP11 | BM25 equal field weights | Lexical baseline | Not started | |
| EXP12 | BM25 boosted structured fields | Lexical tuning | Not started | |
| EXP13 | BM25 fuzziness | Typo experiment | Not started | |
| EXP14 | Synonym expansion | Vocabulary experiment | Not started | |
| EXP20 | LLM query parser | Optional parser comparison | Not started | |
| EXP21 | Description-only embeddings | Representation comparison | Not started | |
| EXP22 | Title plus description embeddings | Representation comparison | Not started | |
| EXP23 | All metadata embeddings | Representation comparison | Not started | |
| EXP24 | Labelled structured embeddings | Representation comparison | Not started | |
| EXP30 | Vector-only retrieval | Semantic baseline | Not started | |
| EXP31 | BM25-only retrieval | Lexical comparator | Not started | |
| EXP32 | RRF hybrid retrieval | Rank-fusion baseline | Not started | |
| EXP33 | Normalised score fusion | Fusion alternative | Not started | |
| EXP34 | Weighted score fusion | Fusion alternative | Not started | |
| EXP40 | Simple pointwise model | Learned baseline | Not started | |
| EXP41 | Tree-based pointwise model | Learned baseline | Not started | |
| EXP43 | LightGBM LambdaRank | Ranking candidate | Not started | |
| EXP44 | Ranker with behavioural features | Context experiment | Not started | |
| EXP50 | Collaborative filtering | Optional recommendation experiment | Not started | |
| EXP51 | Two-tower model | Optional sparse-data investigation | Not started | |

## Log

Chronological one-line entries as experiments start/finish, newest last.

- 2026-09-07 — Register created (project controls).
- 2026-09-07 — EXP1 and EXP2 run against a synthetic 12-product fixture; both accepted as
  baselines only. See their README.md files for full results and failure analysis.
