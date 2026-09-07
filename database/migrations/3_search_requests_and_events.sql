-- Instrumentation entities per architecture §8.1: "Search request" and "Event". Anonymous
-- sessions only (architecture §11 privacy) — session_id is a random token, never tied to any
-- real identity.

CREATE TABLE search_request (
    search_request_id  TEXT PRIMARY KEY,
    session_id          TEXT NOT NULL,
    query                TEXT NOT NULL,
    interpretation       JSONB,
    model_version        TEXT NOT NULL,
    fallback_used        BOOLEAN NOT NULL DEFAULT FALSE,
    result_count         INTEGER NOT NULL,
    latency_ms           INTEGER NOT NULL,
    created_at           TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_search_request_session_id ON search_request(session_id);
CREATE INDEX idx_search_request_created_at ON search_request(created_at);

CREATE TABLE event (
    event_id            BIGSERIAL PRIMARY KEY,
    event_type           TEXT NOT NULL CHECK (event_type IN ('impression', 'click')),
    session_id           TEXT NOT NULL,
    search_request_id    TEXT REFERENCES search_request(search_request_id) ON DELETE CASCADE,
    product_id           TEXT NOT NULL REFERENCES product(product_id) ON DELETE CASCADE,
    position              INTEGER,
    created_at            TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_event_search_request_id ON event(search_request_id);
CREATE INDEX idx_event_session_id ON event(session_id);
CREATE INDEX idx_event_product_id ON event(product_id);
