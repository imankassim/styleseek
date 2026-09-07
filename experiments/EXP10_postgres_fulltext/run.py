"""EXP10: PostgreSQL full-text search.

Architecture comparison (architecture §14): how does Postgres's built-in `tsvector`/`ts_rank`
full-text search compare to the OpenSearch BM25 experiments (EXP11-14)? Uses
`websearch_to_tsquery`, which tolerates free-text input (unlike `plainto_tsquery`, it handles
quoted phrases/operators, closer to what a real search box needs) and ranks with `ts_rank`.

No fuzziness, no synonyms, no field boosting beyond `setweight` — this is meant to be a fair,
reasonably-configured comparison point, not a tuned system (that's EXP12/13).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "evaluation"))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "database"))
from metrics import evaluate, print_report  # noqa: E402

import psycopg  # noqa: E402
from ingest import load_database_url  # noqa: E402

RESULT_LIMIT_NDCG = 10
RESULT_LIMIT_RECALL = 50

SQL = """
    SELECT product_id
    FROM (
        SELECT
            p.product_id,
            ts_rank(
                setweight(to_tsvector('english', p.title), 'A')
                || setweight(to_tsvector('english', p.category), 'B')
                || setweight(to_tsvector('english', coalesce(p.occasion, '')), 'C')
                || setweight(to_tsvector('english', coalesce(pc.colour, '')), 'B'),
                websearch_to_tsquery('english', %s)
            ) AS rank
        FROM product p
        JOIN (
            SELECT DISTINCT ON (product_id) product_id, colour
            FROM product_variant
            ORDER BY product_id, colour
        ) pc ON pc.product_id = p.product_id
    ) scored
    WHERE rank > 0
    ORDER BY rank DESC, product_id
    LIMIT %s
"""


def make_search_fn(conn: psycopg.Connection):
    def search(query: str) -> list[str]:
        with conn.cursor() as cur:
            cur.execute(SQL, (query, RESULT_LIMIT_RECALL))
            return [row[0] for row in cur.fetchall()]

    return search


if __name__ == "__main__":
    with psycopg.connect(load_database_url()) as conn:
        rows, summary = evaluate(make_search_fn(conn), splits=["train", "val"])
    print_report("EXP10 PostgreSQL full-text search (train+val)", rows, summary)
