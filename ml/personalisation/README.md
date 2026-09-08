# ml/personalisation/

Empty by design, not an oversight. Architecture §18's proposed structure puts personalisation
here, but the actual code is `backend/app/personalization.py` — it's a request-time lookup
against live session data (Postgres `event` rows), not an offline-trained artefact, so it lives
with the rest of the request-serving code it's called from (`backend/app/routers/search.py`)
rather than as a separate ML pipeline stage. See `backend/app/personalization.py`'s module
docstring.
