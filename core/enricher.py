"""Enrichment helpers for extracted vacancy data."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Tuple

from core.extractor import ExtractionResult


@dataclass(slots=True, frozen=True)
class EnrichmentResult:
    """Structured enrichment payload returned by ``run_enrichment``."""

    esco_skills: List[str] = field(default_factory=list)
    boolean_query: str = ""
    salary_range: Tuple[int, int] | None = None


def enrich_esco(must_have_skills: List[str]) -> List[str]:
    """Return up to the first 10 ESCO skills from the provided list."""

    return must_have_skills[:10]


def enrich_boolean(must_have_skills: List[str]) -> str:
    """Create a boolean search string from the given skills."""

    if not must_have_skills:
        return ""

    return " AND ".join(f'("{skill}")' for skill in must_have_skills)


def enrich_salary(seniority: str | None) -> Tuple[int, int] | None:
    """Return a salary band based on seniority level when applicable."""

    if seniority in {"Mid", "Senior"}:
        return (55000, 70000)

    return None


def run_enrichment(extraction: ExtractionResult) -> EnrichmentResult:
    """Combine enrichment helpers for an ``ExtractionResult`` instance."""

    esco_skills = enrich_esco(extraction.must_have_skills)
    boolean_query = enrich_boolean(extraction.must_have_skills)
    salary_range = enrich_salary(extraction.seniority)

    return EnrichmentResult(
        esco_skills=esco_skills, boolean_query=boolean_query, salary_range=salary_range
    )
