# Progress

Tracks the [finished implementation plan](architecture/STYLESEEK_ARCHITECTURE.md#20-finished-implementation-plan)
(§20) and [stage decision gates](architecture/STYLESEEK_ARCHITECTURE.md#17-stage-decision-gates)
(§17). Updated as each stage completes — check here before resuming work rather than inferring
progress from git log alone.

| Stage | Focus | Status | Gate |
|---|---|---|---|
| 1 | Create project controls | Done | — |
| 2 | Build the visible search journey | Done | G1 met — idle/loading/error/empty/success states verified in browser, no console errors |
| 3 | Create primitive baselines | Done | EXP1 (any-hit 0.30/10), EXP2 (0.90/10, several hollow hits) — see `experiments/experiment_register.md` |
| 4 | Build product foundation | Done | G2 met — 44,446 products / 216,108 variants ingested from the Kaggle "small" dataset into Neon Postgres, 0 rejected, 7/7 data quality tests pass (`tests/data_quality/test_catalogue.py`) |
| 5 | Connect the application | Done | G3 met — FastAPI (`/health`, `/products`, `/products/{id}`, `/search`) connected to the real Postgres catalogue; frontend calls the real API end-to-end (verified in browser); 15/15 backend + integration tests pass |
| 6 | Complete search-related commerce | Done | Product detail page (size selection, add-to-basket), basket simulation (localStorage), `/browse` (category/price filters, sort, pagination) — full journey verified in browser end-to-end, no console errors |
| 7 | Instrument and label | Done | Anonymous session cookies, `search_request`/`event` logging, batched impression/click tracking (verified in browser + DB), relevance rubric + 18-query labelled set (58 verified product ids, train/val/test split) |
| 8 | Create lexical baseline | Done | G4 met (evaluation harness + frozen 18-query judgment set), G5 met — EXP14 (BM25 boosted + synonyms) promoted to serving, ndcg@10 0.755 vs EXP10's Postgres comparison at 0.355 (+113%). 45/45 tests pass including a failure-injection test for the OpenSearch→Postgres fallback |
| 9 | Understand queries | Done | Deterministic parser (colour/gender/price as hard filters; category/occasion measured and deliberately excluded from filtering — see risk register). Live `/search` model version `bm25_opensearch_synonyms_qu_v1`. 69/69 tests pass, interpretation surfaced in the UI |
| 10 | Add semantic retrieval | Done | G6 met — title-only embeddings (EXP22, `BAAI/bge-small-en-v1.5` via fastembed) are the best representation; not competitive as a standalone ranker (ndcg@10 0.293 vs BM25's 0.755) but found relevant candidates BM25 missed entirely on 5/15 queries (EXP30). 93/93 tests pass |
| 11 | Build hybrid retrieval | Done | G7 met — EXP34 (90/10 weighted BM25+vector fusion) beats BM25 alone on ndcg@10 (+1.3%) and recall@50 (+4.0%) simultaneously, sub-second latency (~650ms). Live `/search` model version `hybrid_weighted_fusion_v1`, two-tier fallback. 95/95 tests pass |
| 12 | Guarantee safety | Done | Size extraction added to query understanding; stock/size eligibility (unconditional `in_stock` filter, per-size stock confirmed against Postgres) and post-fusion duplicate control ((title, category, colour) dedup) wired into live `/search`. 110/110 tests pass |
| 13 | Train learned ranking | Done | G8 result: **no** — EXP40/41/43 (linear, trees, LightGBM LambdaRank) all scored well below EXP34's hybrid fusion (0.703) on held-out validation, consistently (0.253/0.188/0.252). 178 training rows isn't enough data yet. EXP34 remains the live ranker; feature pipeline kept ready. 120/120 tests pass |
| 14 | Add bounded context | Done | G9 met — session colour boost (`backend/app/personalization.py`) reorders only the top-10 window, only when the query itself has no explicit colour, using only that session's own real clicks (2+ needed for a signal). Confirmed live: repeated clicks on a Black dress bubble Black items to the front of a broad "dress" search, while an explicit "blue dress" search stays 100% blue regardless of click history. 130/130 tests pass |
| 15 | Operationalise | Done | G10 met — sync tests (index staleness now visible), a drift test (live ndcg@10/recall@50 gated against a floor), a fixed failure-injection bug (session feature lookup could crash all of `/search`), Dockerfiles + docker-compose (both images verified building in CI), GitHub Actions CI (green), a monitoring report + operational runbook against real `search_request` data, a security/privacy pass (secret scan, log review, one input-validation fix), and an accessibility scan (axe-core, zero violations across 4 states). 141/141 pytest tests pass |
| 16 | Conclude | Done | G11 met — serving configuration frozen ([ADR-3](decisions/3-freeze-serving-configuration.md)), held-out evaluation run on the never-tuned test split (ndcg@10=0.660, recall@50=0.667, n=3, honest small-n caveat stated — `evaluation/final_evaluation.md`), catalogue licence confirmed MIT (resolving a gap open since Stage 4), model card and ethics/limitations assessment written, root README rewritten as the complete journey publication |

- Stage 14 added `backend/app/personalization.py` (bounded session colour boost) and wired it
  into `/search` as the last eligibility/diversity step. It never fires when the query has an
  explicit colour, never fires for a cold-start session (no click history yet), and only ever
  reorders the top-10 window of already-retrieved candidates — no new candidates pulled in, none
  dropped. See `tests/unit/test_personalization.py` (pure-function boost logic) and the three G9
  tests in `tests/integration/test_api_contract.py` (live-API override/cold-start checks).

## Optional extensions (after Stage 16)

The §20 plan above is frozen (ADR-3) and complete. Architecture §12 journey 16 names "visual
similarity and conversational discovery" as explicitly separate, optional extensions — not part
of any gated stage, not in the §14 experiment catalogue. Continuing here at the user's direction
after Stage 16 concluded.

- **Visual similarity** — Done. `GET /products/{id}/similar`, CLIP image embeddings
  (`Qdrant/clip-ViT-B-32-vision` via fastembed), one kNN lookup against an offline-built index
  (`search/index_image_vectors.py`), surfaced as a "Similar styles" section on the product
  detail page. No ground truth exists for this, so it's evaluated qualitatively rather than
  against the NDCG harness — see `docs/model_cards/visual_similarity_v1.md` for the honest
  finding (colour/background-dominated for flat garment photos, reliably within-category for
  structured objects like shoes/watches). 151/151 tests pass.
- **Conversational discovery** — not started. Would need an LLM API (cost/credentials the user
  would need to provide), unlike visual similarity which ran entirely on local compute.

## Notes / open items carried forward

- Catalogue licence still not confirmed on the Kaggle dataset page — see
  [`docs/data_sheets/catalogue_data_sheet.md`](data_sheets/catalogue_data_sheet.md). Not blocking
  local dev/experimentation, but must be resolved before anything derived from the dataset
  (product text, images) appears in a public-facing demo or deployment.
- Using the *small* Kaggle dataset variant (`fashion-product-images-small`), not the originally
  linked full one — disk space on this machine couldn't fit the full 23.1GB archive. Same
  catalogue/metadata either way; only image resolution differs (irrelevant to search/ranking).
- Database is a managed free-tier Neon Postgres project; search index is a managed free-tier
  Bonsai OpenSearch project (no local Postgres/OpenSearch/Docker installed) — both connection
  strings live only in git-ignored `database/.env`.
- `/search` now serves from OpenSearch (`bm25_opensearch_synonyms_v1`, EXP14's config), with an
  automatic fallback to the old Postgres placeholder (`token_intersection_postgres_v0`) if
  OpenSearch is unreachable — `fallback_used` in the response says which one actually served it.
- To run locally: `python backend/run.py` (port 8000) and `npm run dev` in `frontend/` (port
  3000) — both need `database/.env` (or `backend/.env`) with `DATABASE_URL` and `OPENSEARCH_URL`
  set. Rebuild the search index after a catalogue change with `python search/index.py` (base
  index) and `python experiments/EXP14_synonym_expansion/run.py` (the one actually served).
- Known gap, deliberately not fixed yet, and worse than it was at Stage 8: `/search` always
  returns *something*, even for a genuinely no-result query — vector kNN has no concept of "no
  match" at all (BM25 alone could at least occasionally score zero). See
  `tests/search_regression/test_search_regression.py`. **Still open after Stage 12**: that
  stage's eligibility work was stock/size (a product either qualifies or doesn't) and duplicate
  control, not a minimum-relevance score cutoff — the two are different problems. A relevance
  threshold hasn't been scheduled to a specific later stage; revisit if it becomes a real
  nuisance rather than a theoretical gap.
- Live `/search` now serves hybrid BM25+vector fusion (`hybrid_weighted_fusion_v1`, Stage 11).
  Vector index: `styleseek_products_v3_vectors` (title/metadata/structured vector fields), built
  by `python search/index_vectors.py`. Rebuilding the full catalogue's embeddings takes roughly
  80 minutes on this machine (CPU-only ONNX, ~44,446 products × 3 representations) — budget for
  that if the catalogue changes. Re-run `python experiments/EXP34_weighted_score_fusion/run.py`
  (or the others) to re-check the fusion weights still hold after a catalogue/model change.
- Local dev gotcha (Windows): if `/search` ever looks suspiciously slow (multi-second) when
  testing with a Python script, check whether the script uses `"localhost"` — Python's
  `requests` (and some other clients) try IPv6 `::1` first, time out, then fall back to IPv4,
  adding 1-2+ seconds per request that has nothing to do with the backend. Use `127.0.0.1`
  directly to get a true reading. The browser/frontend's own `fetch()` isn't affected.
- Stage 12's eligibility/dedup work was **not** re-measured against `evaluation/metrics.py`'s
  harness the way every EXP-numbered comparison in Stages 8/10/11 was — it isn't one of
  architecture §14's planned comparison experiments, and removing exact-duplicate/out-of-stock
  items from a page of results has an obvious direction of effect (frees result slots for
  distinct, available products) rather than a genuine trade-off worth a formal before/after
  measurement. Flagging this explicitly as a scope choice, not an oversight — if a future stage
  needs precise numbers here, they don't exist yet.
