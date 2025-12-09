from __future__ import annotations

import json
from typing import Any

from src.llm_prompts import LLMClient, response_to_text, safe_parse_json


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

    client = LLMClient(api_key="sk-test", model="gpt-4o-mini")

    text = client.text("hi", instructions="return json", max_output_tokens=12)
    parsed = json.loads(text)

    assert parsed == {"ok": True}
    assert client.client.responses.last_kwargs is not None
    assert client.client.responses.last_kwargs.get("response_format") == {
        "type": "json_object"
    }
