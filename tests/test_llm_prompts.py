from __future__ import annotations

import json
from typing import Any

from src.llm_prompts import (
    EXTRACTION_RESPONSE_FORMAT,
    LLMClient,
    parse_structured_response,
    response_to_text,
    safe_parse_json,
)
from src.settings import DEFAULT_MODEL


class _DummyContent:
    def __init__(self, *, type: str, text: str | None = None, json_payload: Any = None):
        self.type = type
        self.text = text
        self.json = json_payload


class _DummyMessage:
    def __init__(self, content: list[_DummyContent]):
        self.type = "message"
        self.content = content


class _DummyResponse:
    def __init__(self, output: list[_DummyMessage]):
        self.output = output


class _FakeResponses:
    def __init__(self) -> None:
        self.last_kwargs: dict[str, Any] | None = None

    def create(self, **kwargs: Any) -> _DummyResponse:
        self.last_kwargs = kwargs
        return _DummyResponse(
            [
                _DummyMessage(
                    [_DummyContent(type="output_json", json_payload={"ok": True})]
                )
            ]
        )


class _FakeOpenAI:
    def __init__(self, *, api_key: str):
        self.api_key = api_key
        self.responses = _FakeResponses()


def test_response_to_text_handles_output_json() -> None:
    payload = {"fields": ["a", "b"], "detected_language": "de"}
    response = _DummyResponse(
        [_DummyMessage([_DummyContent(type="output_json", json_payload=payload)])]
    )

    raw_text = response_to_text(response)

    assert json.loads(raw_text) == payload
    assert safe_parse_json(raw_text) == payload


def test_llm_client_requests_structured_output(monkeypatch: Any) -> None:
    monkeypatch.setattr("src.llm_prompts.OpenAI", _FakeOpenAI)

    client = LLMClient(api_key="sk-test", model=DEFAULT_MODEL)

    text = client.text("hi", instructions="return json", max_output_tokens=12)
    parsed = json.loads(text)

    assert parsed == {"ok": True}
    assert client.client.responses.last_kwargs is not None
    assert client.client.responses.last_kwargs.get("text") == {
        "format": {"type": "json_object", "name": "StructuredResponse"}
    }


def test_llm_client_uses_schema_name_for_format(monkeypatch: Any) -> None:
    monkeypatch.setattr("src.llm_prompts.OpenAI", _FakeOpenAI)

    client = LLMClient(api_key="sk-test", model=DEFAULT_MODEL)

    text = client.text("hi", instructions="return json", response_format=EXTRACTION_RESPONSE_FORMAT)
    parsed = json.loads(text)

    assert parsed == {"ok": True}
    assert client.client.responses.last_kwargs is not None
    assert client.client.responses.last_kwargs.get("text") == {
        "format": {
            "type": "json_schema",
            "name": "PrimaryExtraction",
            "json_schema": EXTRACTION_RESPONSE_FORMAT["json_schema"],
        }
    }


def test_llm_client_intake_call_path_does_not_raise_type_error(
    monkeypatch: Any,
) -> None:
    class _StrictResponses:
        def __init__(self) -> None:
            self.last_kwargs: dict[str, Any] | None = None

        def create(
            self,
            *,
            model: str,
            input: str,
            instructions: str | None = None,
            max_output_tokens: int | None = None,
            text: dict[str, Any] | None = None,
        ) -> _DummyResponse:
            self.last_kwargs = {
                "model": model,
                "input": input,
                "instructions": instructions,
                "max_output_tokens": max_output_tokens,
                "text": text,
            }
            return _DummyResponse(
                [
                    _DummyMessage(
                        [_DummyContent(type="output_json", json_payload={"ok": True})]
                    )
                ]
            )

    class _StrictOpenAI:
        def __init__(self, *, api_key: str):
            self.api_key = api_key
            self.responses = _StrictResponses()

    monkeypatch.setattr("src.llm_prompts.OpenAI", _StrictOpenAI)

    client = LLMClient(api_key="sk-test", model=DEFAULT_MODEL)

    text = client.text(
        "intake prompt", instructions="return json", max_output_tokens=64
    )

    assert json.loads(text) == {"ok": True}
    assert client.client.responses.last_kwargs == {
        "model": DEFAULT_MODEL,
        "input": "intake prompt",
        "instructions": "return json",
        "max_output_tokens": 64,
        "text": {"format": {"type": "json_object", "name": "StructuredResponse"}},
    }


def test_parse_structured_response_rejects_invalid_payload() -> None:
    raw = json.dumps({"fields": [{"path": "x"}]})

    parsed, ok = parse_structured_response(
        raw, response_format=EXTRACTION_RESPONSE_FORMAT, context="invalid_extraction"
    )

    assert not ok
    assert parsed == {}
