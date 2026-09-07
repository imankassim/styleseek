"""Shared OpenSearch connection helper. Same env-file-fallback pattern as
database/ingest.py and backend/app/config.py — one place credentials get read from.
"""

from pathlib import Path

from opensearchpy import OpenSearch

REPO_ROOT = Path(__file__).parent.parent


def get_opensearch_url() -> str:
    env_path = REPO_ROOT / "database" / ".env"
    for line in env_path.read_text().splitlines():
        if line.startswith("OPENSEARCH_URL="):
            value = line.split("=", 1)[1].strip()
            if value:
                return value
    msg = "OPENSEARCH_URL not found in database/.env"
    raise RuntimeError(msg)


def get_client() -> OpenSearch:
    return OpenSearch(hosts=[get_opensearch_url()], use_ssl=True, verify_certs=True, timeout=20)
