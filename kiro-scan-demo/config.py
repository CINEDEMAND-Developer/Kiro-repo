# config.py — Application configuration
# All secrets and environment-specific values are read from environment variables.
# Copy .env.example to .env and fill in real values before running locally.
# Never hardcode credentials or secrets in this file.

import os


def _require_env(name: str) -> str:
    """Raise a clear error at startup if a required env var is missing."""
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(
            f"Required environment variable '{name}' is not set. "
            "See .env.example for the full list of required variables."
        )
    return value


# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------
DATABASE = os.environ.get("DATABASE", "users.db")

# ---------------------------------------------------------------------------
# Security — these MUST be set in the environment; no defaults are provided.
# ---------------------------------------------------------------------------
SECRET_KEY = _require_env("SECRET_KEY")

# ---------------------------------------------------------------------------
# Admin credentials — loaded from environment, never hardcoded.
# ---------------------------------------------------------------------------
ADMIN_USERNAME = _require_env("ADMIN_USERNAME")
ADMIN_PASSWORD = _require_env("ADMIN_PASSWORD")

# ---------------------------------------------------------------------------
# Runtime behaviour
# ---------------------------------------------------------------------------
# Set FLASK_DEBUG=true only in local development. Never in staging or production.
DEBUG = os.environ.get("FLASK_DEBUG", "false").lower() == "true"

# ---------------------------------------------------------------------------
# File uploads
# ---------------------------------------------------------------------------
UPLOAD_FOLDER = os.environ.get("UPLOAD_FOLDER", "/tmp/uploads")

# Maximum allowed upload size: 5 MB
MAX_CONTENT_LENGTH = int(os.environ.get("MAX_UPLOAD_BYTES", str(5 * 1024 * 1024)))
