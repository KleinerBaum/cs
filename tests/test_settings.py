from __future__ import annotations

import importlib.util
import sys
import types
from importlib.machinery import ModuleSpec
from typing import Callable

import pytest

from src import settings


def _mock_missing_streamlit(monkeypatch: pytest.MonkeyPatch) -> None:
    original_find_spec: Callable[[str, str | None], ModuleSpec | None] = (
        importlib.util.find_spec
    )

    def _missing(name: str, package: str | None = None) -> ModuleSpec | None:
        if name == "streamlit":
            return None
        return original_find_spec(name, package)

    monkeypatch.setattr(importlib.util, "find_spec", _missing)
    monkeypatch.delenv(settings.MODEL_ENV_KEY, raising=False)
    monkeypatch.delenv("OPENAI_MODEL", raising=False)
    monkeypatch.setitem(sys.modules, "streamlit", None)


def _mock_streamlit(monkeypatch: pytest.MonkeyPatch, secrets: dict[str, str]) -> None:
    original_find_spec: Callable[[str, str | None], ModuleSpec | None] = (
        importlib.util.find_spec
    )

    def _spec(name: str, package: str | None = None) -> ModuleSpec | None:
        if name == "streamlit":
            return ModuleSpec("streamlit", loader=None)
        return original_find_spec(name, package)

    module = types.ModuleType("streamlit")
    module.secrets = secrets  # type: ignore[attr-defined]
    module.__spec__ = ModuleSpec("streamlit", loader=None)

    monkeypatch.setattr(importlib.util, "find_spec", _spec)
    monkeypatch.setitem(sys.modules, "streamlit", module)


def test_configured_model_defaults_without_overrides(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _mock_missing_streamlit(monkeypatch)
    assert settings.configured_model(default_model="fallback-model") == "fallback-model"


def test_configured_model_uses_constant_default(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _mock_missing_streamlit(monkeypatch)
    assert settings.configured_model() == settings.DEFAULT_MODEL


def test_configured_model_prefers_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(settings.MODEL_ENV_KEY, "gpt-3.5-turbo")
    assert settings.configured_model(default_model="fallback-model") == "gpt-3.5-turbo"


def test_configured_model_reads_streamlit_secret(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv(settings.MODEL_ENV_KEY, raising=False)
    _mock_streamlit(monkeypatch, {settings.MODEL_ENV_KEY: "secret-model"})
    assert settings.configured_model(default_model="fallback-model") == "secret-model"


def test_env_override_beats_streamlit_secret(monkeypatch: pytest.MonkeyPatch) -> None:
    _mock_streamlit(monkeypatch, {settings.MODEL_ENV_KEY: "secret-model"})
    monkeypatch.setenv(settings.MODEL_ENV_KEY, "env-model")
    assert settings.configured_model(default_model="fallback-model") == "env-model"


def test_legacy_env_key_is_respected(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(settings.MODEL_ENV_KEY, raising=False)
    monkeypatch.setenv("OPENAI_MODEL", "legacy-env")
    assert settings.configured_model(default_model="fallback-model") == "legacy-env"


def test_legacy_secret_key_is_respected(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(settings.MODEL_ENV_KEY, raising=False)
    _mock_streamlit(monkeypatch, {"OPENAI_MODEL": "legacy-secret"})
    assert settings.configured_model(default_model="fallback-model") == "legacy-secret"
