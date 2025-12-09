from __future__ import annotations

import logging
import time
from typing import Any, Iterable

from openai import APIConnectionError, APITimeoutError, BadRequestError, OpenAI

from src.llm_prompts import response_to_text, safe_parse_json

logger = logging.getLogger(__name__)

# Parameter allow-list per model to avoid sending unsupported options
_ALLOWED_PARAMS: dict[str, set[str]] = {
    "gpt-4o-mini": {"input", "instructions", "max_output_tokens", "metadata", "response_format", "text"},
    "o3-mini": {"input", "instructions", "max_output_tokens", "metadata", "response_format", "text"},
}
_DEFAULT_ALLOWED = {
    "input",
    "instructions",
    "max_output_tokens",
    "metadata",
    "response_format",
    "text",
    "temperature",
    "top_p",
}


def call_llm(client: OpenAI, *, model: str, **kwargs: Any) -> str:
    """Call the Responses API with unsupported parameters stripped."""

    allowed = _ALLOWED_PARAMS.get(model, _DEFAULT_ALLOWED)
    payload = {k: v for k, v in kwargs.items() if k in allowed and v is not None}
    dropped = {k for k in kwargs if k not in payload}
    logger.debug(
        "Calling LLM model=%s with params=%s dropped=%s",
        model,
        sorted(payload),
        sorted(dropped),
    )
    delays = [0.4, 0.8]
    last_error: Exception | None = None
    for attempt, delay in enumerate([0.0, *delays]):
        if attempt:
            time.sleep(delay)
        try:
            response = client.responses.create(model=model, **payload)
            return response_to_text(response)
        except (APIConnectionError, APITimeoutError) as exc:
            last_error = exc
            logger.warning("LLM transient error (attempt %s): %s", attempt + 1, exc)
            continue
        except BadRequestError:
            # Do not retry invalid requests; propagate immediately
            raise
    if last_error:
        raise last_error
    return ""


def _build_prompt(title: str, context: Iterable[str]) -> str:
    ctx = "\n".join(x for x in context if x)
    return f"{title}\n\nKontext/Context:\n{ctx}" if ctx else title


def generate_role_summary(
    job_title: str,
    context: dict[str, Any],
    *,
    client: OpenAI,
    model: str,
) -> str:
    prompt = _build_prompt(
        "Erstelle eine kurze Rollenbeschreibung (5-7 Sätze) in der UI-Sprache. Keep bullet spacing and stay concise.",
        [job_title, context.get("company_name", ""), context.get("team", "")],
    )
    raw = call_llm(
        client,
        model=model,
        input=prompt,
        instructions=(
            "Return only the role summary text. Avoid modifying any other fields."
        ),
        max_output_tokens=420,
    )
    return raw.strip()


def generate_tasks(
    job_title: str,
    context: dict[str, Any],
    *,
    client: OpenAI,
    model: str,
) -> list[str]:
    prompt = _build_prompt(
        "Liste 5-8 Kernaufgaben als Aufzählung in der UI-Sprache (ein Bullet pro Zeile).",
        [job_title, context.get("position_summary", ""), context.get("team", "")],
    )
    raw = call_llm(
        client,
        model=model,
        input=prompt,
        instructions="Return JSON with a 'tasks' list of strings.",
        response_format={"type": "json_object"},
        max_output_tokens=480,
    )
    try:
        parsed = safe_parse_json(raw)
        tasks = parsed.get("tasks") if isinstance(parsed, dict) else None
        if isinstance(tasks, list):
            return [str(t).strip() for t in tasks if str(t).strip()]
    except ValueError as exc:
        logger.warning("Could not parse tasks JSON: %s", exc)
    return [line.strip().lstrip("-•").strip() for line in raw.splitlines() if line.strip()]


def suggest_skills(
    job_title: str,
    tasks: list[str],
    *,
    client: OpenAI,
    model: str,
) -> dict[str, list[str]]:
    prompt = _build_prompt(
        "Schlage Kern-Skills (must_have) und optionale Skills (nice_to_have) als Listen vor.",
        [job_title, "\n".join(tasks)],
    )
    raw = call_llm(
        client,
        model=model,
        input=prompt,
        instructions=(
            "Return JSON with 'must_have' and 'nice_to_have' list keys."
        ),
        response_format={"type": "json_object"},
        max_output_tokens=520,
    )
    try:
        parsed = safe_parse_json(raw)
        if isinstance(parsed, dict):
            must_have = parsed.get("must_have")
            nice_to_have = parsed.get("nice_to_have")
            return {
                "must_have": [str(x).strip() for x in must_have or [] if str(x).strip()],
                "nice_to_have": [str(x).strip() for x in nice_to_have or [] if str(x).strip()],
            }
    except ValueError as exc:
        logger.warning("Could not parse skills JSON: %s", exc)
    return {"must_have": [], "nice_to_have": []}
