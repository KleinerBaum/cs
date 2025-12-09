from __future__ import annotations

from core.enricher import enrich_esco, enrich_salary, run_enrichment
from core.extractor import ExtractionResult


def test_enrich_boolean_contains_skills():
    extraction = ExtractionResult(must_have_skills=["Python", "SQL"])

    result = run_enrichment(extraction)

    assert result.boolean_query == '("Python") AND ("SQL")'
    assert '("Python")' in result.boolean_query
    assert '("SQL")' in result.boolean_query


def test_run_enrichment_skips_when_no_skills():
    extraction = ExtractionResult()

    result = run_enrichment(extraction)

    assert result.esco_skills == []
    assert result.boolean_query == ""


def test_enrich_salary_based_on_seniority():
    extraction = ExtractionResult(seniority="Senior")

    result = run_enrichment(extraction)

    assert result.salary_range == (55000, 70000)


def test_enrich_salary_skips_for_junior():
    assert enrich_salary("Junior") is None
    assert enrich_salary(None) is None


def test_enrich_esco_limits_to_ten_items():
    skills = [f"Skill {index}" for index in range(15)]

    esco_skills = enrich_esco(skills)

    assert len(esco_skills) == 10
    assert esco_skills == skills[:10]
    assert isinstance(run_enrichment(ExtractionResult()).salary_range, (tuple, type(None)))
