# Experiment Register

Working register of every planned, running, completed and rejected experiment. Source list of
planned experiments: `STYLESEE1.docx` §14. Each experiment gets its own folder under
`experiments/<EXP-ID>_<slug>/` once it is started, with its config, code/notebook and results.
Rejected experiments move to `discarded/<EXP-ID>_<slug>/` with a short reason, per the
negative-result policy (architecture §14): an experiment is rejected because it lowers
relevance, increases latency, adds operational complexity, relies on weak synthetic behaviour,
creates governance concerns, or duplicates a simpler capability — never just because it looks
less advanced.

Status values: `Not started` · `In progress` · `Accepted` · `Rejected`.

| Experiment | Possibility considered | Role | Status | Decision / notes |
|---|---|---|---|---|
| EXP-001 | Whole-query substring search | Primitive baseline | Not started | |
| EXP-002 | Token intersection search | Primitive baseline | Not started | |
| EXP-010 | PostgreSQL full-text search | Architecture comparison | Not started | |
| EXP-011 | BM25 equal field weights | Lexical baseline | Not started | |
| EXP-012 | BM25 boosted structured fields | Lexical tuning | Not started | |
| EXP-013 | BM25 fuzziness | Typo experiment | Not started | |
| EXP-014 | Synonym expansion | Vocabulary experiment | Not started | |
| EXP-020 | LLM query parser | Optional parser comparison | Not started | |
| EXP-021 | Description-only embeddings | Representation comparison | Not started | |
| EXP-022 | Title plus description embeddings | Representation comparison | Not started | |
| EXP-023 | All metadata embeddings | Representation comparison | Not started | |
| EXP-024 | Labelled structured embeddings | Representation comparison | Not started | |
| EXP-030 | Vector-only retrieval | Semantic baseline | Not started | |
| EXP-031 | BM25-only retrieval | Lexical comparator | Not started | |
| EXP-032 | RRF hybrid retrieval | Rank-fusion baseline | Not started | |
| EXP-033 | Normalised score fusion | Fusion alternative | Not started | |
| EXP-034 | Weighted score fusion | Fusion alternative | Not started | |
| EXP-040 | Simple pointwise model | Learned baseline | Not started | |
| EXP-041 | Tree-based pointwise model | Learned baseline | Not started | |
| EXP-043 | LightGBM LambdaRank | Ranking candidate | Not started | |
| EXP-044 | Ranker with behavioural features | Context experiment | Not started | |
| EXP-050 | Collaborative filtering | Optional recommendation experiment | Not started | |
| EXP-051 | Two-tower model | Optional sparse-data investigation | Not started | |

## Log

Chronological one-line entries as experiments start/finish, newest last.

- 2026-09-07 — Register created (Stage 1, WP1).
