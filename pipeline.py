"""Deterministic pipeline orchestrator for vacancy processing."""

from __future__ import annotations

import logging
from typing import Any, Dict

from core.enricher import EnrichmentResult, run_enrichment
from core.extractor import ExtractionResult, run_extraction
from core.schemas import Enrichment, RawInput, VacancyCore, VacancyValidated
from core.validator import ValidationResult, validate_required_fields
from src.keys import Keys

logger = logging.getLogger(__name__)

PipelineOutput = Dict[str, VacancyCore | VacancyValidated | Enrichment | str | None]


def _build_validation_notes(validation: ValidationResult) -> list[str]:
    if not validation["missing_required"]:
        return []
    missing = ", ".join(validation["missing_required"])
    return [f"Missing required fields: {missing}"]


def _to_enrichment_model(result: EnrichmentResult) -> Enrichment:
    tags = [result.boolean_query] if result.boolean_query else []
    suggestions: list[str] = []

    if result.salary_range:
        lower, upper = result.salary_range
        suggestions.append(f"Salary range: {lower}-{upper}")

    return Enrichment(
        tags=tags,
        esco_skills=result.esco_skills,
        suggestions=suggestions,
    )


def run_pipeline(raw_input: RawInput, payload: dict[str, Any] | None = None) -> PipelineOutput:
    """Run extraction, validation, and optional enrichment for a vacancy."""
    logger.debug("Starting pipeline for source_type=%s", raw_input.source_type)

    output: PipelineOutput = {"core": None, "validated": None, "enrichment": None}

    try:
        extraction: ExtractionResult = run_extraction(raw_input)
        logger.debug("Extraction completed: %s", extraction)

        core = VacancyCore(
            company=extraction.company,
            requirements=list(extraction.must_have_skills),
            tools=list(extraction.must_have_skills),
        )

        validation_payload = payload or {}
        validation: ValidationResult = validate_required_fields(validation_payload)
        validated = VacancyValidated(
            **core.model_dump(),
            validation_notes=_build_validation_notes(validation),
            validated=not validation["missing_required"],
        )

        enrichment_model: Enrichment | None = None
        if not validation["missing_required"]:
            enrichment_result = run_enrichment(extraction)
            enrichment_model = _to_enrichment_model(enrichment_result)
            logger.debug("Enrichment completed: %s", enrichment_result)

        output.update({"core": core, "validated": validated, "enrichment": enrichment_model})
        logger.debug("Pipeline finished successfully")
        return output
    except Exception as exc:  # pragma: no cover - defensive guard
        logger.exception("Pipeline failed: %s", exc)
        output["error"] = str(exc)
        return output


if __name__ == "__main__":  # pragma: no cover - manual smoke test
    sample_raw = RawInput(content="Senior Data Scientist at ACME AG using Python and Pandas")
    sample_payload = {
        Keys.COMPANY_NAME: "ACME AG",
        Keys.POSITION_TITLE: "Data Scientist",
        Keys.EMPLOYMENT_CONTRACT: "Full-time",
        Keys.EMPLOYMENT_TYPE: "Permanent",
        Keys.EMPLOYMENT_START: "2024-09-01",
        Keys.LOCATION_CITY: "Berlin",
    }

    result = run_pipeline(sample_raw, sample_payload)
    print(result)
