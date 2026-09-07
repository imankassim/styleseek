# ADR-2: Repository and artefact structure

- Status: Accepted
- Date: 2026-09-07
- Deciders: Project owner (via `STYLESEE1.docx` §18)

## Context

The project spans a frontend, a backend, ML experimentation, evaluation, infrastructure and
governance documentation. Without an agreed layout up front, later stages (especially
experiments and rejected approaches) would have nowhere consistent to live.

## Decision

Use the repository structure specified in architecture §18 verbatim:

```
styleseek/
├── frontend/       backend/        database/       search/
├── ml/{embeddings, learning_to_rank, personalisation}/
├── experiments/    discarded/      evaluation/
├── tests/{unit, integration, search_regression, data_quality}/
├── infrastructure/
├── docs/{architecture, decisions, model_cards, data_sheets, ethics}/
└── README.md
```

`experiments/` holds every reproducible investigation (one folder per `EXP-ID`); `discarded/`
holds the same for rejected experiments, each with a short reason — nothing is deleted, per the
negative-result policy (architecture §14).

## Alternatives considered

- A monorepo tool (Nx/Turborepo) — not chosen; the project is a single small team learning
  exercise, and the documented structure is already the minimum artefact set called for in
  architecture §18 without extra tooling overhead.

## Consequences

- Every new file created in this project should be placed under one of these top-level
  directories rather than at the repo root, keeping the root reserved for `README.md` and
  config files.

## Evidence

`STYLESEE1.docx` §18, "Proposed repository and artefact structure".
