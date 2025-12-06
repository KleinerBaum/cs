from __future__ import annotations

APP_NAME = "CognitiveStaffing – Need Analysis Wizard"

# ---- OpenAI / LLM
DEFAULT_MODEL = "gpt-5-mini"  # https://platform.openai.com/docs/models/gpt-5-mini
DEFAULT_TEMPERATURE = 0.2
DEFAULT_MAX_OUTPUT_TOKENS = 1400

# Keep prompts bounded to avoid accidental huge requests
MAX_SOURCE_TEXT_CHARS = 70_000
MAX_EVIDENCE_CHARS = 220

# ---- ESCO
ESCO_BASE_URL = "https://ec.europa.eu/esco/api"
ESCO_DEFAULT_VERSION = None  # e.g. "v1.2.0" if you want to pin

# ---- Networking
REQUEST_TIMEOUT_S = 20
USER_AGENT = "CognitiveStaffing/0.1 (+streamlit)"

# ---- UX
MAX_PRIMARY_QUESTIONS_PER_STEP = 10
LOW_CONFIDENCE_THRESHOLD = 0.60
