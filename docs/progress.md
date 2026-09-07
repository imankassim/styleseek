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
| 6 | Complete search-related commerce | Not started | — |
| 7 | Instrument and label | Not started | — |
| 8 | Create lexical baseline | Not started | G4, G5 |
| 9 | Understand queries | Not started | — |
| 10 | Add semantic retrieval | Not started | G6 |
| 11 | Build hybrid retrieval | Not started | G7 |
| 12 | Guarantee safety | Not started | — |
| 13 | Train learned ranking | Not started | G8 |
| 14 | Add bounded context | Not started | G9 |
| 15 | Operationalise | Not started | G10 |
| 16 | Conclude | Not started | G11 |

## Notes / open items carried forward

- Catalogue licence still not confirmed on the Kaggle dataset page — see
  [`docs/data_sheets/catalogue_data_sheet.md`](data_sheets/catalogue_data_sheet.md). Not blocking
  local dev/experimentation, but must be resolved before anything derived from the dataset
  (product text, images) appears in a public-facing demo or deployment.
- Using the *small* Kaggle dataset variant (`fashion-product-images-small`), not the originally
  linked full one — disk space on this machine couldn't fit the full 23.1GB archive. Same
  catalogue/metadata either way; only image resolution differs (irrelevant to search/ranking).
- Database is a managed free-tier Neon Postgres project (no local Postgres/Docker installed) —
  connection string lives only in git-ignored `database/.env`.
- `/search`'s retrieval is a deliberate placeholder (`token_intersection_postgres_v0` — SQL port
  of Stage 3's EXP2), not BM25/lexical work yet. EXP10 (Postgres full-text search) and BM25
  tuning are still "Not started" in the experiment register — that's Stage 8, not done early.
- To run locally: `python backend/run.py` (port 8000) and `npm run dev` in `frontend/` (port
  3000) — both need `database/.env` (or `backend/.env`) with `DATABASE_URL` set.
