"""Stage 14: bounded anonymous session personalisation (architecture journey 15 exit outcome,
"Small contextual adaptation"; target journey §2.3, "Session adaptation" — "broad dress search
after viewing neutral midi dresses... apply a small transparent preference boost without
overriding the query").

Deliberately narrower than EXP44 (Stage 13, rejected): this doesn't use pooled/aggregate click
data to train anything — it reads *this one session's own* recent real clicks at request time
and uses them as a same-session signal, which doesn't have the "synthetic data presented as
real" problem EXP44 was rejected for for. Still genuinely bounded:

  - Only ever a same-session signal — no cross-session profiling, no persistent identity
    (architecture §11 privacy; session_id is a random anonymous token, app/session.py).
  - Only applied when the *current* query doesn't already specify a colour — architecture "hard
    constraints before soft preference": if the shopper said "red dress", that's already
    satisfied by the existing hard filter (Stage 9), and session history must never second-
    guess an explicit, stated preference.
  - Only reorders *within* the existing top-`window` results — never pulls in a candidate that
    wasn't already there, never drops one that was. A transparent nudge, not new retrieval.
  - Cold start (no session history yet) is a no-op, not a special case to handle — the function
    just returns the ranking unchanged (architecture journey 15, "cold-start fallback").
"""

from psycopg import Connection

SESSION_BOOST_WINDOW = 10
MIN_CLICKS_FOR_SIGNAL = 2  # a single accidental click shouldn't establish a "preference"


def get_session_preferred_colour(conn: Connection, session_id: str) -> str | None:
    """None means either a genuinely new session (cold start) or no clear colour signal yet —
    both are treated identically: no personalisation applied."""
    with conn.cursor() as cur:
        cur.execute(
            """
            WITH product_colour AS (
                SELECT DISTINCT ON (product_id) product_id, colour
                FROM product_variant
                ORDER BY product_id, colour
            )
            SELECT pc.colour, COUNT(*) AS n
            FROM event e
            JOIN product_colour pc ON pc.product_id = e.product_id
            WHERE e.session_id = %s AND e.event_type = 'click'
            GROUP BY pc.colour
            ORDER BY n DESC
            LIMIT 1
            """,
            (session_id,),
        )
        row = cur.fetchone()
        if row and row[1] >= MIN_CLICKS_FOR_SIGNAL:
            return row[0]
        return None


def apply_session_colour_boost(
    ranked_ids: list[str],
    docs_by_id: dict,
    preferred_colour: str | None,
    window: int = SESSION_BOOST_WINDOW,
) -> list[str]:
    """Moves products matching `preferred_colour` to the front of the top-`window` slice,
    preserving relative order within each group; everything beyond the window is untouched.
    A no-op if there's no preference to apply."""
    if not preferred_colour:
        return ranked_ids

    head, tail = ranked_ids[:window], ranked_ids[window:]
    matches = [pid for pid in head if preferred_colour in (docs_by_id[pid].get("colours") or [])]
    non_matches = [pid for pid in head if pid not in set(matches)]
    return [*matches, *non_matches, *tail]
