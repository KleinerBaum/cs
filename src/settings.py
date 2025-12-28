from __future__ import annotations

import importlib.util
import os
from typing import Any

APP_NAME = "CognitiveStaffing – Need Analysis Wizard"

# ---- OpenAI / LLM
DEFAULT_MODEL = "gpt-5-nano"  # Fastest low-cost default
DEFAULT_TEMPERATURE = 0.2
DEFAULT_MAX_OUTPUT_TOKENS = 1400
MODEL_ENV_KEY = "CS_OPENAI_MODEL"
_LEGACY_MODEL_ENV_KEYS: tuple[str, ...] = ("OPENAI_MODEL",)

# Keep prompts bounded to avoid accidental huge requests
MAX_SOURCE_TEXT_CHARS = 70_000
MAX_EVIDENCE_CHARS = 220

# ---- ESCO
ESCO_BASE_URL = "https://ec.europa.eu/esco/api"
ESCO_DEFAULT_VERSION = None  # e.g. "v1.2.0" if you want to pin a specific version

# ---- Networking
REQUEST_TIMEOUT_S = 20
USER_AGENT = "CognitiveStaffing/0.1 (+streamlit)"

# ---- UX
MAX_PRIMARY_QUESTIONS_PER_STEP = 10
LOW_CONFIDENCE_THRESHOLD = 0.60


def _get_streamlit_secret(key: str) -> str | None:
    if importlib.util.find_spec("streamlit") is None:
        return None

    import streamlit as st  # type: ignore

    raw_secrets: Any = getattr(st, "secrets", None)
    if raw_secrets is None:
        return None

    if not raw_secrets:
        return None

    direct = raw_secrets.get(key)
    if isinstance(direct, str) and direct.strip():
        return direct.strip()

    general = raw_secrets.get("general", {})
    if isinstance(general, dict):
        nested = general.get(key)
        if isinstance(nested, str) and nested.strip():
            return nested.strip()
    return None


def configured_model(default_model: str = DEFAULT_MODEL) -> str:
    """Return the model configured via env/Streamlit secrets with a safe fallback."""

    env_override = os.getenv(MODEL_ENV_KEY, "").strip()
    if env_override:
        return env_override

    for legacy_key in _LEGACY_MODEL_ENV_KEYS:
        legacy_env = os.getenv(legacy_key, "").strip()
        if legacy_env:
            return legacy_env

    secret_override = _get_streamlit_secret(MODEL_ENV_KEY)
    if secret_override:
        return secret_override

    for legacy_key in _LEGACY_MODEL_ENV_KEYS:
        legacy_secret = _get_streamlit_secret(legacy_key)
        if legacy_secret:
            return legacy_secret

    return default_model
