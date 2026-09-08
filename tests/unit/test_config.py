"""Unit tests for backend/app/config.py's get_cors_origins — the parsing logic behind Stage 15's
deployment-configurable CORS allowlist (previously hardcoded to localhost, see app/main.py)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "backend"))

from app.config import get_cors_origins  # noqa: E402


def test_defaults_to_local_dev_origin_when_unset(monkeypatch):
    monkeypatch.delenv("CORS_ORIGINS", raising=False)
    assert get_cors_origins() == ["http://localhost:3000"]


def test_defaults_to_local_dev_origin_when_blank(monkeypatch):
    monkeypatch.setenv("CORS_ORIGINS", "   ")
    assert get_cors_origins() == ["http://localhost:3000"]


def test_parses_single_origin(monkeypatch):
    monkeypatch.setenv("CORS_ORIGINS", "https://styleseek.example.com")
    assert get_cors_origins() == ["https://styleseek.example.com"]


def test_parses_comma_separated_origins_and_trims_whitespace(monkeypatch):
    monkeypatch.setenv("CORS_ORIGINS", "https://a.example.com, https://b.example.com ,https://c.example.com")
    assert get_cors_origins() == [
        "https://a.example.com",
        "https://b.example.com",
        "https://c.example.com",
    ]
