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
| EXP10 | PostgreSQL full-text search | Architecture comparison | Accepted | ndcg@10 0.355. Comparison point only, not promoted. See `experiments/EXP10_postgres_fulltext/README.md`. |
| EXP11 | BM25 equal field weights | Lexical baseline | Accepted | ndcg@10 0.552. `best_fields` undersells multi-attribute queries — motivated EXP12. See `experiments/EXP11_bm25_equal_weights/README.md`. |
| EXP12 | BM25 boosted structured fields | Lexical tuning | Accepted | ndcg@10 0.661 (best non-synonym config). Superseded by EXP14 for serving. See `experiments/EXP12_bm25_boosted_fields/README.md`. |
| EXP13 | BM25 fuzziness | Typo experiment | Rejected | Fixes the one typo query (ndcg 0→0.601) but `most_fields` regresses every other type; net ndcg@10 0.441 vs EXP12's 0.661. Moved to `discarded/EXP13_bm25_fuzziness/`. |
| EXP14 | Synonym expansion | Vocabulary experiment | **Accepted — promoted to serving** | ndcg@10 0.755, best of all lexical experiments. Live `/search` model version `bm25_opensearch_synonyms_qu_v1` (Stage 9 added query understanding on top), with fallback to EXP2-style Postgres search if OpenSearch is unavailable. See `experiments/EXP14_synonym_expansion/README.md`. |
| EXP20 | LLM query parser | Optional parser comparison | Not started | Optional per architecture §14; the deterministic parser (Stage 9, `backend/app/query_understanding.py`) already met the "safe structured constraints" exit outcome — revisit only if a named problem the deterministic parser can't solve shows up. |
| EXP21 | Description-only embeddings | Representation comparison | Rejected before running | Catalogue has no description field at all (`product.description` is always NULL). See `discarded/EXP21_description_only_embeddings/README.md`. |
| EXP22 | Title plus description embeddings | Representation comparison | **Accepted — carried forward** | Run as title-only (no description exists). ndcg@10 0.293, best of the three representations tested. See `experiments/EXP22_title_embeddings/README.md`. |
| EXP23 | All metadata embeddings | Representation comparison | Accepted | ndcg@10 0.218 — worse than title-only; concatenating metadata dilutes this general-purpose embedding model's representation. See `experiments/EXP23_all_metadata_embeddings/README.md`. |
| EXP24 | Labelled structured embeddings | Representation comparison | Accepted | ndcg@10 0.258 — better than plain concatenation (EXP23) but still worse than title-only (EXP22). See `experiments/EXP24_labelled_structured_embeddings/README.md`. |
| EXP30 | Vector-only retrieval | Semantic baseline | Accepted | Not competitive as a standalone ranker (ndcg@10 0.293 vs BM25's 0.755) but found relevant candidates BM25 missed entirely on 5/15 queries (G6 evidence). See `experiments/EXP30_vector_only_retrieval/README.md`. |
| EXP31 | BM25-only retrieval | Lexical comparator | Accepted | = EXP14, referenced under this ID for the Stage 10/11 comparison. See `experiments/EXP31_bm25_only_retrieval/README.md`. |
| EXP32 | RRF hybrid retrieval | Rank-fusion baseline | Rejected | ndcg@10 0.549 (vs BM25 alone 0.755) — recall improved but ranking quality regressed 27% relative; equal-rank trust between a strong and a weak ranker doesn't work. See `experiments/EXP32_rrf_hybrid/README.md`. |
| EXP33 | Normalised score fusion | Fusion alternative | Accepted | ndcg@10 0.673 — better than RRF but still below BM25 alone; preserving score magnitude helps, equal weighting still doesn't. See `experiments/EXP33_normalised_score_fusion/README.md`. |
| EXP34 | Weighted score fusion | Fusion alternative | **Accepted — promoted to serving** | 90/10 lexical/semantic beats BM25 alone on ndcg@10 (0.765, +1.3%) AND recall@50 (0.721, +4.0%) simultaneously. Live `/search` model version `hybrid_weighted_fusion_v1`. See `experiments/EXP34_weighted_score_fusion/README.md`. |
| EXP40 | Simple pointwise model | Learned baseline | Rejected | ndcg@10 0.253 vs EXP34's 0.703 (val split, n=4) — 178 training rows isn't enough. See `experiments/EXP40_simple_pointwise_model/README.md`. |
| EXP41 | Tree-based pointwise model | Learned baseline | Rejected | ndcg@10 0.188 — more model capacity made it worse, confirming EXP40's finding was about data volume, not model choice. See `experiments/EXP41_tree_pointwise_model/README.md`. |
| EXP43 | LightGBM LambdaRank | Ranking candidate | Rejected (for now) | ndcg@10 0.252 — same result a third time with a ranking-aware objective. G8: learned ranking does not yet beat simpler ranking. See `experiments/EXP43_lightgbm_lambdarank/README.md`. |
| EXP44 | Ranker with behavioural features | Context experiment | Rejected before running | Only synthetic (test-harness) click data exists, no genuine shopper behaviour. See `discarded/EXP44_behavioural_features_ranker/README.md`. |
| EXP50 | Collaborative filtering | Optional recommendation experiment | Not started | |
| EXP51 | Two-tower model | Optional sparse-data investigation | Not started | |

## Log

Chronological one-line entries as experiments start/finish, newest last.

- 2026-09-07 — Register created (project controls).
- 2026-09-07 — EXP1 and EXP2 run against a synthetic 12-product fixture; both accepted as
  baselines only. See their README.md files for full results and failure analysis.
- 2026-09-07 — EXP10-14 run against the real catalogue and the labelled query set
  (`evaluation/relevance_judgments.json`), using the new NDCG@10/Recall@50 harness
  (`evaluation/metrics.py`). EXP14 (BM25 + synonym expansion) promoted to serving. EXP13
  rejected and moved to `discarded/`. The judgment set itself grew from 18 to 230 graded
  products across two pooling passes after repeated cases of genuinely good but ungraded
  results scoring as irrelevant by default — see the experiment READMEs and
  `evaluation/relevance_rubric.md`.
