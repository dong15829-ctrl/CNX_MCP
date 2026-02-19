"""Jira monitoring backend package."""

from pathlib import Path

try:  # pragma: no cover - optional dependency
    from dotenv import load_dotenv

    env_path = Path(__file__).resolve().parents[2] / ".env"
    load_dotenv(env_path)
except Exception:
    pass
