"""POST /events — records genuine impressions and clicks (architecture §7 step 12, §8.1 "Event"
entity). Batched (one call per result page render) rather than one request per product, to keep
this from being a pile of tiny round trips for a 24-result page.

Never blocks the shopper's search response — this is called after /search has already returned
and rendered; if it fails, the search experience is unaffected (architecture §10, "Event
collector unavailable: do not block search response").
"""

from fastapi import APIRouter, Depends, HTTPException
from psycopg import Connection
from psycopg.errors import ForeignKeyViolation
from pydantic import BaseModel, Field

from app.db import get_connection
from app.session import get_session_id

router = APIRouter()

MAX_EVENTS_PER_BATCH = 100


class EventIn(BaseModel):
    event_type: str = Field(pattern="^(impression|click)$")
    search_request_id: str | None = None
    product_id: str
    position: int | None = None


class EventBatch(BaseModel):
    events: list[EventIn] = Field(max_length=MAX_EVENTS_PER_BATCH)


class EventBatchResult(BaseModel):
    recorded: int


@router.post("/events", response_model=EventBatchResult)
def record_events(
    batch: EventBatch,
    conn: Connection = Depends(get_connection),
    session_id: str = Depends(get_session_id),
) -> EventBatchResult:
    if not batch.events:
        return EventBatchResult(recorded=0)

    recorded = 0
    with conn.cursor() as cur:
        for event in batch.events:
            try:
                # Each insert is its own transaction so one bad row (unknown product/
                # search_request_id — stale client state) can't roll back rows already
                # recorded earlier in the same batch.
                with conn.transaction():
                    cur.execute(
                        """
                        INSERT INTO event (event_type, session_id, search_request_id, product_id, position)
                        VALUES (%s, %s, %s, %s, %s)
                        """,
                        (event.event_type, session_id, event.search_request_id, event.product_id, event.position),
                    )
                recorded += 1
            except ForeignKeyViolation:
                continue

    if recorded == 0 and len(batch.events) > 0:
        raise HTTPException(status_code=422, detail="No events in the batch were valid.")

    return EventBatchResult(recorded=recorded)
