"""GET /health — liveness only. Doesn't check the database; that's what a readiness probe
(not built yet) would do, and conflating the two makes container orchestration harder later."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
def health() -> dict:
    return {"status": "ok"}
