from __future__ import annotations

import pytest
from pydantic import ValidationError

from core.schemas import Enrichment, RawInput, VacancyCore, VacancyValidated


def test_default_values_are_empty_lists():
    raw = RawInput(text="example")
    core = VacancyCore()
    validated = VacancyValidated()
    enrichment = Enrichment()

    assert raw.model_dump()["text"] == "example"
    assert raw.model_dump()["source_type"] == "text"
    assert core.model_dump() == {
        "title": None,
        "company": None,
        "location": None,
        "responsibilities": [],
        "requirements": [],
        "benefits": [],
        "languages": [],
        "tools": [],
    }
    assert validated.model_dump() == {
        "title": None,
        "company": None,
        "location": None,
        "responsibilities": [],
        "requirements": [],
        "benefits": [],
        "languages": [],
        "tools": [],
        "validation_notes": [],
        "validated": False,
    }
    assert enrichment.model_dump() == {
        "tags": [],
        "esco_skills": [],
        "suggestions": [],
        "warnings": [],
    }


def test_list_fields_are_not_shared():
    core_one = VacancyCore()
    core_two = VacancyCore()
    core_one.responsibilities.append("a")
    assert core_two.responsibilities == []

    validated_one = VacancyValidated()
    validated_two = VacancyValidated()
    validated_one.validation_notes.append("checked")
    assert validated_two.validation_notes == []

    enrichment_one = Enrichment()
    enrichment_two = Enrichment()
    enrichment_one.tags.append("tag1")
    assert enrichment_two.tags == []


def test_raw_input_requires_text():
    with pytest.raises(ValidationError):
        RawInput()  # type: ignore[call-arg]
