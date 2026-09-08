# Monitoring and operational runbook

Architecture §10 ("Monitoring: application logs and local metrics" — the local/development-role
counterpart of the cloud-role "central logs, metrics, alerts and dashboards" this prototype
doesn't have the infrastructure or traffic volume to justify) and G10 ("Can the system be
operated and restored?").

## What's monitored, and how

Every real `/search` call writes one row to `search_request`
(`database/migrations/3_search_requests_and_events.sql`) via
`backend/app/routers/search.py`'s `_log_search_request` — `model_version`, `fallback_used`,
`result_count`, and `latency_ms`. That's the entire metrics pipeline; there's no separate
collector to keep in sync, because search itself can't succeed without writing the row (the
insert happens on the same request, same connection).

`python monitoring/report.py [hours]` reads that table and reports:

| Metric | What a healthy number looks like | What a bad number means |
|---|---|---|
| Fallback rate | Low single digits (OpenSearch/vector hiccups are rare) | Rising fallback rate → check OpenSearch/Bonsai availability (`docs/risk_register.md` "OpenSearch unavailable") |
| Zero-result rate | Reflects genuinely unmatched queries, not broken retrieval | A sudden jump suggests a broken filter or an index that's gone stale — cross-check `tests/sync/test_index_sync.py` |
| p50 / p95 / p99 latency | p50 ~300-650ms, matches Stage 11's measured hybrid latency | Sustained latency growth → see "Latency growth" in the risk register |
| Model version distribution | Mostly `hybrid_weighted_fusion_v1`, the live default | A version other than the current default dominating means fallbacks are firing far more than expected |

There's no alerting on top of this (no paging, no dashboard) — for a solo-developer prototype at
this traffic volume, running the report manually when something seems off is proportionate. The
closest thing to automated alerting that does exist is CI: `tests/sync/` and `tests/drift/` run
against the live database/index and would fail a build if staleness or a quality regression
crept in, which is the failure mode this table alone can't see (the table only knows what
`/search` itself observed, not whether the index backing it is stale).

## Failure playbook

Cross-referencing architecture §10's availability/fallback table against what's actually built:

| Failure | Expected behaviour | Where it's implemented / verified |
|---|---|---|
| Vector index unavailable | Run lexical retrieval, omit semantic contribution | `backend/app/routers/search.py::_search_hybrid`'s `except Exception` around `semantic.search_with_scores`; `test_search_falls_back_to_bm25_only_when_vector_search_unavailable` |
| OpenSearch unavailable | Explicitly defined limited fallback, not unrelated results | `_search_hybrid` returns `None` → `_search_postgres_fallback`; `test_search_falls_back_to_postgres_when_opensearch_unavailable` |
| Session feature service unavailable | Non-personalised ranking | `_apply_eligibility_and_diversity`'s `try/except` around `get_session_preferred_colour` (Stage 15 fix — this was silently missing through Stage 14); `test_search_falls_back_to_non_personalised_when_session_feature_lookup_fails` |
| Event collector unavailable | Don't block the search response | `/events` is a separate endpoint called after `/search` has already returned and rendered (`backend/app/routers/events.py` docstring) — structurally can't block it |
| Ranker unavailable or invalid | Use RRF or the last approved rule configuration | Not directly applicable yet — no learned ranker is live (Stage 13: G8 said no, EXP34's hybrid fusion remains the served ranker) |
| Catalogue synchronisation failure | Keep the last known serving index, alert, prevent silent promotion of incomplete data | **Partial.** `tests/sync/` makes staleness visible (in CI and on demand) but there's no automatic gate that would stop a broken `search/index.py` re-run from silently replacing a good index with a bad one, and no alert channel beyond a failed test run. Documented as an open gap, not fixed here — see `docs/risk_register.md` "Index staleness". |

## Restoring the system after an outage

- **Backend down**: `docker run` the image built from `backend/Dockerfile` (or `python
  backend/run.py` locally), pointed at the same `DATABASE_URL`/`OPENSEARCH_URL`. No local state
  to restore — the connection pool and embedding model both rebuild from scratch on startup.
- **Frontend down**: same idea with `frontend/Dockerfile`, or `npm run start` after `npm run
  build`. Stateless.
- **OpenSearch index corrupted or deleted**: rebuild from Postgres (the source of truth) with
  `python search/index.py` (BM25) and `python search/index_vectors.py` (vectors, ~80 minutes for
  the full catalogue), then re-run
  `experiments/EXP14_synonym_expansion/run.py` for the synonym-enabled index actually served.
  Nothing is lost: OpenSearch only ever holds a denormalised copy of Postgres.
- **Postgres data corrupted**: this prototype has no separate backup/restore procedure beyond
  Neon's own managed backups — re-running `database/ingest.py` against the original Kaggle
  dataset would reconstruct the catalogue tables, but `search_request`/`event` history
  (real usage instrumentation) would be lost. Not exercised or drilled in this project.

## CI

`.github/workflows/ci.yml` runs on every push/PR to `main`: the hermetic backend unit suite,
a frontend lint + build, and a Docker build of both images (smoke test only, no push/deploy).
The DB/OpenSearch-dependent suites (`tests/data_quality`, `tests/integration`,
`tests/search_regression`, `tests/sync`, `tests/drift`) are not run in CI — they need the live
Neon/Bonsai credentials, which aren't configured as repository secrets (a deliberate choice left
to the repo owner, not made unilaterally here). Run them locally with `database/.env` present.

## Deployment

Not actually deployed anywhere beyond this local machine — see `docker-compose.yml` for local
container orchestration and each `Dockerfile`'s header comment for standalone `docker build`/`run`
usage. Architecture §10's cloud-oriented roles (managed application runtime for the API, static
or server-rendered hosting for the web layer) describe *roles*, not a mandated vendor, and
actually provisioning one (Render, Fly.io, Vercel, etc.) would mean creating new external
accounts and ongoing costs/exposure — a decision for whoever runs this prototype next, not one to
make autonomously.
