from __future__ import annotations

from app import _autofill_from_source
from core.extractor import TextExtractor
from core.schemas import RawInput
from src.ingest import SourceDocument
from state import AppState


def test_text_extractor_handles_german_job_ad() -> None:
    text = (
        "Rheinbahn sucht Senior Data Engineer (m/w/d) in Düsseldorf.\n"
        "Arbeitszeit: Vollzeit\n"
        "Deine Aufgaben:\n"
        "- Aufbau von Datenpipelines\n"
        "- Betreuung von BI-Tools\n"
        "- Zusammenarbeit mit Data Scientists\n"
        "Dein Profil:\n"
        "- Erfahrung mit Python und SQL\n"
        "- Kenntnisse in Azure"
    )
    extractor = TextExtractor()

    result = extractor.extract(RawInput(text=text))

    assert result.company == "Rheinbahn"
    assert result.job_title and "Data Engineer" in result.job_title
    assert result.seniority == "Senior"
    assert result.location == "Düsseldorf"
    assert result.employment_type == "Vollzeit"
    assert len(result.responsibilities) >= 2
    assert {"Python", "SQL"}.issubset(set(result.must_have_skills))


def test_autofill_updates_multiple_wizard_fields() -> None:
    text = (
        "Acme Ltd is hiring Junior Software Engineer.\n"
        "Location: Berlin\n"
        "Employment: Full-time\n"
        "Responsibilities:\n"
        "- Build APIs\n"
        "- Maintain AWS infrastructure\n"
        "Must have: Python, Docker"
    )
    source_doc = SourceDocument(source_type="text", name="sample", text=text, meta={})
    state = AppState()

    updated = _autofill_from_source(state, source_doc)

    assert state.profile.company_name == "Acme"
    assert state.role.job_title and "Software Engineer" in state.role.job_title
    assert state.role.seniority == "Junior"
    assert state.profile.primary_city == "Berlin"
    assert state.profile.employment_type == "Full-time"
    assert len(state.skills.tasks) >= 2
    assert {"Python", "Docker"}.issubset(set(state.skills.must_have))
    assert len(updated) >= 4
