from __future__ import annotations

from typing import cast

from core.role_extractor import (
    clean_title,
    extract_role_required_fields,
    llm_fill_role_fields,
)
from src.llm_prompts import LLMClient


class DummyLLMClient:
    def __init__(self, payload: str):
        self.payload = payload

    def text(self, *args, **kwargs) -> str:  # noqa: ANN001
        return self.payload


def test_clean_title_strips_articles_and_punctuation() -> None:
    raw = "eine Senior Data Engineer."

    cleaned = clean_title(raw)

    assert cleaned == "Senior Data Engineer"


def test_extracts_job_title_from_header_line() -> None:
    text = "Senior Backend Engineer (m/w/d)\nAcme GmbH baut APIs"

    result = extract_role_required_fields(text)

    assert result.job_title == "Senior Backend Engineer (m/w/d)"
    assert result.seniority_level == "Senior"


def test_extracts_job_title_from_wir_suchen_phrase() -> None:
    text = "Wir suchen einen Product Manager (all genders) für unser Team."

    result = extract_role_required_fields(text)

    assert result.job_title == "Product Manager (all genders)"


def test_extracts_job_title_from_position_label() -> None:
    text = "Position: Marketing Specialist\nBericht an: VP Marketing"

    result = extract_role_required_fields(text)

    assert result.job_title == "Marketing Specialist"


def test_detects_department_from_label() -> None:
    text = "Team: Data Platform\nAbteilung: Vertrieb & Marketing"

    result = extract_role_required_fields(text)

    assert result.department == "Data Platform"


def test_detects_seniority_from_german_variant() -> None:
    text = "Wir suchen eine Teamleiter Softwareentwicklung (gn)."

    result = extract_role_required_fields(text)

    assert result.seniority_level == "Lead"


def test_llm_fallback_populates_missing_fields() -> None:
    payload = (
        '{"job_title": "Senior UX Designer",'
        ' "seniority_level": "Senior",'
        ' "department": "Design",'
        ' "evidence": {"job_title": "header"}}'
    )
    client = DummyLLMClient(payload)

    result = llm_fill_role_fields("irrelevant", client=cast(LLMClient, client))

    assert result.job_title == "Senior UX Designer"
    assert result.seniority_level == "Senior"
    assert result.department == "Design"
    assert result.evidence["job_title"] == "header"


def test_llm_fallback_limits_to_requested_fields() -> None:
    payload = (
        '{"job_title": "Lead Accountant",'
        ' "seniority_level": "Lead",'
        ' "department": "Finance"}'
    )
    client = DummyLLMClient(payload)

    result = llm_fill_role_fields(
        "irrelevant",
        client=cast(LLMClient, client),
        missing_fields={"department"},
    )

    assert result.department == "Finance"
    assert result.job_title is None
    assert result.seniority_level is None
