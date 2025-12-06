from __future__ import annotations

import json
import re
from typing import Any

from openai import OpenAI

from .settings import DEFAULT_MAX_OUTPUT_TOKENS, DEFAULT_MODEL, DEFAULT_TEMPERATURE
from .utils import clamp_str

_CODE_FENCE_RE = re.compile(r"^```(?:json)?\s*|\s*```$", re.IGNORECASE | re.MULTILINE)


class LLMClient:
    def __init__(self, api_key: str, model: str = DEFAULT_MODEL):
        self.client = OpenAI(api_key=api_key)
        self.model = model

    def text(
        self,
        input_text: str,
        *,
        instructions: str | None = None,
        temperature: float = DEFAULT_TEMPERATURE,
        max_output_tokens: int = DEFAULT_MAX_OUTPUT_TOKENS,
    ) -> str:
        resp = self.client.responses.create(
            model=self.model,
            input=input_text,
            instructions=instructions,
            temperature=temperature,
            max_output_tokens=max_output_tokens,
        )
        return response_to_text(resp)


def response_to_text(resp: Any) -> str:
    """Best-effort extraction of assistant text from a Responses API response."""
    # Most common path (as in the OpenAI cookbook)
    try:
        return resp.output[0].content[0].text  # type: ignore[attr-defined]
    except Exception:
        pass

    output = getattr(resp, "output", None)
    if output is None and isinstance(resp, dict):
        output = resp.get("output")

    if not output:
        maybe = getattr(resp, "output_text", None)
        if isinstance(maybe, str) and maybe.strip():
            return maybe
        return ""

    texts: list[str] = []
    for item in output:
        item_type = getattr(item, "type", None) if not isinstance(item, dict) else item.get("type")
        if item_type != "message":
            continue
        content = getattr(item, "content", None) if not isinstance(item, dict) else item.get("content")
        if not content:
            continue
        for c in content:
            c_type = getattr(c, "type", None) if not isinstance(c, dict) else c.get("type")
            if c_type in {"output_text", "text"}:
                txt = getattr(c, "text", None) if not isinstance(c, dict) else c.get("text")
                if txt:
                    texts.append(txt)
    return "".join(texts).strip()


def safe_parse_json(raw: str) -> Any:
    """Parse JSON from a model response with very defensive cleanup."""
    if raw is None:
        raise ValueError("No content to parse as JSON")

    s = raw.strip()
    s = _CODE_FENCE_RE.sub("", s).strip()

    try:
        return json.loads(s)
    except Exception:
        pass

    candidates: list[str] = []
    for open_ch, close_ch in [("{", "}"), ("[", "]")]:
        start = s.find(open_ch)
        end = s.rfind(close_ch)
        if start != -1 and end != -1 and end > start:
            candidates.append(s[start : end + 1])

    last_error: Exception | None = None
    for cand in candidates:
        try:
            return json.loads(cand)
        except Exception as e:
            last_error = e

    preview = clamp_str(s, 500)
    raise ValueError(f"Could not parse JSON from model output. Preview: {preview}\nError: {last_error}")
