"""Simple extractor adapters for raw inputs."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
import re
from typing import Dict, List, Protocol

from core.schemas import RawInput

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class ExtractionResult:
    """Structured extraction output with minimal, deterministic fields."""

    seniority: str | None = None
    company: str | None = None
    must_have_skills: List[str] = field(default_factory=list)


class BaseExtractor(Protocol):
    """Interface for extractor adapters."""

    def extract(
        self, raw: RawInput
    ) -> ExtractionResult:  # pragma: no cover - Protocol definition
        """Parse raw input into structured fields."""


class TextExtractor:
    """Deterministic keyword-based extractor for plain text content."""

    _COMPANY_PATTERN = re.compile(r"\b([A-Z][A-Za-z0-9&.-]*)\s+AG\b")
    _SKILL_KEYWORDS: tuple[str, ...] = ("Python", "Pandas")

    def extract(self, raw: RawInput) -> ExtractionResult:
        content = raw.content
        result = ExtractionResult()

        if "Senior" in content:
            result.seniority = "Senior"

        company_match = self._COMPANY_PATTERN.search(content)
        if company_match:
            result.company = f"{company_match.group(1)} AG"

        lowered = content.lower()
        for keyword in self._SKILL_KEYWORDS:
            if keyword.lower() in lowered:
                result.must_have_skills.append(keyword)

        return result


EXTRACTORS: Dict[str, BaseExtractor] = {"text": TextExtractor()}


def run_extraction(raw_input: RawInput) -> ExtractionResult:
    """Dispatch raw input to the registered extractor based on source type."""
    logger.debug("Running extraction for source_type=%s", raw_input.source_type)

    try:
        extractor = EXTRACTORS[raw_input.source_type]
    except KeyError as exc:  # pragma: no cover - trivial guard
        raise ValueError(f"Unsupported source type: {raw_input.source_type}") from exc

    result = extractor.extract(raw_input)
    logger.debug("Extraction result: %s", result)
    return result
