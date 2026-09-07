# ADR-1: Baseline technology stack

- Status: Accepted
- Date: 2026-09-07
- Deciders: Project owner (via `STYLESEE1.docx` §20 final architecture recommendation)

## Context

StyleSeek needs a concrete, non-hypothetical stack before any code is written, so that every
later stage (catalogue, API, search, ML) builds on the same foundations rather than being
re-platformed mid-project.

## Decision

Adopt the stack specified in the governing architecture document:

- **Frontend:** Next.js — search, category browsing, product pages, filters, basket simulation.
- **Backend:** Python FastAPI — `/products`, `/search`, `/events`, validation, orchestration.
- **Operational database:** PostgreSQL — source of truth for products, variants, stock.
- **Search:** OpenSearch — BM25 lexical index now; vector fields and hybrid retrieval later.
- **Fusion:** Reciprocal Rank Fusion (RRF) as the initial baseline, with alternatives evaluated
  as experiments (EXP32–34) before any replacement.
- **Learning-to-rank:** LightGBM (`LGBMRanker`, LambdaRank objective), introduced only once
  sufficient labelled/behavioural data exists (Stage 13, not before).
- **Personalisation:** anonymous, bounded session features — never overriding explicit query
  constraints.

## Alternatives considered

- **Elasticsearch instead of OpenSearch** — not chosen; architecture document specifies
  OpenSearch throughout (data architecture §8.2, deployment §10), and OpenSearch's documented
  hybrid-search pipelines/RRF support match the fusion design directly.
- **Django instead of FastAPI** — not chosen; FastAPI's async support and typed request/response
  contracts fit the documented `/search` response contract (architecture §7) more directly, and
  is what the architecture names explicitly.
- **A single relational full-text search (no OpenSearch)** — considered as an early experiment
  (EXP10, PostgreSQL full-text search) and retained as a comparison baseline, not the serving
  path, per "baseline first" (architecture §4).

## Consequences

- Local development requires PostgreSQL and OpenSearch running (containers recommended once
  Stage 15/operationalise introduces them; local processes acceptable before that, per
  deployment architecture §10).
- All later stages depend on this decision remaining stable — changing it later is a new ADR
  that supersedes this one, not a silent drift.

## Evidence

`STYLESEE1.docx` §20, "Final architecture recommendation"; mirrored in
[`docs/architecture/STYLESEEK_ARCHITECTURE.md`](../architecture/STYLESEEK_ARCHITECTURE.md#20-finished-implementation-plan).
