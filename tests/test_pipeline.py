from __future__ import annotations

from core.validator import REQUIRED
from core.schemas import RawInput, VacancyValidated
from pipeline import run_pipeline


def test_pipeline_skips_enrichment_when_missing_fields():
    raw = RawInput(content="Senior Data Scientist at ACME AG using Python and Pandas")

    result = run_pipeline(raw, payload={})

    assert isinstance(result["validated"], VacancyValidated)
    assert result["validated"].validated is False
    assert result["validated"].validation_notes
    assert result["enrichment"] is None


def test_pipeline_runs_enrichment_when_all_required_present():
    raw = RawInput(content="Senior Data Scientist at ACME AG using Python and Pandas")
    full_payload = {field: "value" for field in REQUIRED}

    result = run_pipeline(raw, payload=full_payload)

    assert result["validated"].validated is True
    assert result["validated"].validation_notes == []
    assert result["enrichment"] is not None
    assert result["enrichment"].esco_skills == ["Python", "Pandas"]
    assert result["enrichment"].tags
