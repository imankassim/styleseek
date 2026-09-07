"""Anonymous session handling (architecture §11 privacy: prefer anonymous sessions). A random
opaque token in a cookie — never an identity, never tied to a real user, just enough to group a
shopper's own requests together for instrumentation and (later, Stage 14) bounded
personalisation.
"""

import uuid

from fastapi import Request, Response

SESSION_COOKIE_NAME = "styleseek_session"
SESSION_MAX_AGE_SECONDS = 60 * 60 * 24 * 180  # 180 days


def get_session_id(request: Request, response: Response) -> str:
    existing = request.cookies.get(SESSION_COOKIE_NAME)
    if existing:
        return existing

    new_session_id = uuid.uuid4().hex
    response.set_cookie(
        SESSION_COOKIE_NAME,
        new_session_id,
        max_age=SESSION_MAX_AGE_SECONDS,
        httponly=True,
        samesite="lax",
    )
    return new_session_id
