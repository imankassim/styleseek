"""Operational monitoring report (architecture §10 "Monitoring: application logs and local
metrics" — the local/development-role counterpart to the cloud-role "central logs, metrics,
alerts and dashboards" this prototype doesn't have budget/infrastructure for). Reads directly
from the `search_request` table (database/migrations/3_search_requests_and_events.sql), which
every real /search call already writes to (backend/app/routers/search.py's
_log_search_request) — no separate metrics pipeline needed for a prototype at this scale.

Usage: python monitoring/report.py [hours]
  hours: only include requests from the last N hours (default: all time).

See docs/monitoring.md for what these numbers mean and what to do about them.
"""

import sys
from pathlib import Path

import psycopg

REPO_ROOT = Path(__file__).parent.parent


def load_database_url() -> str:
    env_path = REPO_ROOT / "database" / ".env"
    for line in env_path.read_text().splitlines():
        if line.startswith("DATABASE_URL="):
            return line.split("=", 1)[1].strip()
    msg = "DATABASE_URL not found in database/.env"
    raise RuntimeError(msg)


def build_report(conn: psycopg.Connection, since_hours: float | None) -> dict:
    window_sql = "WHERE created_at >= now() - (%s || ' hours')::interval" if since_hours else ""
    params = (since_hours,) if since_hours else ()

    with conn.cursor() as cur:
        cur.execute(f"SELECT COUNT(*) FROM search_request {window_sql}", params)
        (total,) = cur.fetchone()

        if total == 0:
            return {"total": 0}

        cur.execute(
            f"""
            SELECT
                COUNT(*) FILTER (WHERE fallback_used) AS fallback_count,
                percentile_cont(0.5) WITHIN GROUP (ORDER BY latency_ms) AS p50,
                percentile_cont(0.95) WITHIN GROUP (ORDER BY latency_ms) AS p95,
                percentile_cont(0.99) WITHIN GROUP (ORDER BY latency_ms) AS p99,
                AVG(result_count) AS avg_result_count,
                COUNT(*) FILTER (WHERE result_count = 0) AS zero_result_count
            FROM search_request {window_sql}
            """,
            params,
        )
        fallback_count, p50, p95, p99, avg_result_count, zero_result_count = cur.fetchone()

        cur.execute(
            f"""
            SELECT model_version, COUNT(*)
            FROM search_request {window_sql}
            GROUP BY model_version ORDER BY COUNT(*) DESC
            """,
            params,
        )
        model_versions = cur.fetchall()

    return {
        "total": total,
        "fallback_rate": fallback_count / total,
        "p50_latency_ms": p50,
        "p95_latency_ms": p95,
        "p99_latency_ms": p99,
        "avg_result_count": avg_result_count,
        "zero_result_rate": zero_result_count / total,
        "model_versions": model_versions,
    }


def print_report(report: dict, since_hours: float | None) -> None:
    window = f"last {since_hours}h" if since_hours else "all time"
    print(f"\n=== StyleSeek /search monitoring report ({window}) ===")
    if report["total"] == 0:
        print("No search_request rows in this window.")
        return

    print(f"Total requests:      {report['total']}")
    print(f"Fallback rate:       {report['fallback_rate']:.1%}")
    print(f"Zero-result rate:    {report['zero_result_rate']:.1%}")
    print(f"Avg result count:    {report['avg_result_count']:.1f}")
    print(
        f"Latency p50/p95/p99: {report['p50_latency_ms']:.0f}ms / "
        f"{report['p95_latency_ms']:.0f}ms / {report['p99_latency_ms']:.0f}ms"
    )
    print("\nModel version distribution:")
    for version, count in report["model_versions"]:
        print(f"  {version:35} {count:6}  ({count / report['total']:.1%})")


if __name__ == "__main__":
    since_hours = float(sys.argv[1]) if len(sys.argv) > 1 else None
    with psycopg.connect(load_database_url()) as conn:
        report = build_report(conn, since_hours)
    print_report(report, since_hours)
