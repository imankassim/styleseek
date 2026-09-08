# infrastructure/

Empty by design, not an oversight. Architecture §18's proposed structure puts containers/CI/
deployment config in a dedicated top-level directory; this project put them alongside the
service they belong to instead — `backend/Dockerfile`, `frontend/Dockerfile`, `docker-compose.yml`
(repo root, orchestrates both), and `.github/workflows/ci.yml` — a more common convention for a
two-service repo, and what the CI workflow's own `-f backend/Dockerfile` / `-f frontend/Dockerfile`
paths already assume. See `docs/monitoring.md` for the operational runbook these support.
