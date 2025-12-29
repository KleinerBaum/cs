"""Simple extractor adapters for raw inputs."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
import re
from typing import Dict, List, Protocol

from core.regex_fields import (
    clean_city,
    extract_company_name,
    extract_contract_type,
    extract_department,
    extract_desired_start_date,
    extract_employment_type,
    extract_job_title,
    extract_primary_city,
    extract_seniority,
)
from core.schemas import RawInput
from core.role_extractor import (
    clean_title,
    detect_seniority_level,
    extract_role_required_fields,
)
from src.keys import Keys

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class ExtractionResult:
    """Structured extraction output with minimal, deterministic fields."""

    job_title: str | None = None
    seniority: str | None = None
    department: str | None = None
    company: str | None = None
    location: str | None = None
    employment_type: str | None = None
    contract_type: str | None = None
    start_date: str | None = None
    responsibilities: List[str] = field(default_factory=list)
    must_have_skills: List[str] = field(default_factory=list)
    schema_fields: Dict[str, object] = field(default_factory=dict)


class BaseExtractor(Protocol):
    """Interface for extractor adapters."""

    def extract(
        self, raw: RawInput
    ) -> ExtractionResult:  # pragma: no cover - Protocol definition
        """Parse raw input into structured fields."""


def _set_schema_field(
    payload: Dict[str, object], key: str, value: object | None
) -> None:
    if value is None:
        return
    if isinstance(value, str) and not value.strip():
        return
    payload[key] = value


class TextExtractor:
    """Deterministic keyword-based extractor for plain text content."""

    _LOCATION_LABELS = (
        "Hauptstandort",
        "Stadt",
        "Ort",
        "Arbeitsort",
        "Standort",
        "Location",
        "Primary City",
    )
    _COMPANY_PATTERNS: tuple[re.Pattern[str], ...] = (
        re.compile(
            r"\b(?:bei|für|at|join(?:ing)?\s+)?([A-ZÄÖÜ][A-Za-zÄÖÜäöüß0-9&.\-\s]{2,})\s+(?:sucht|hire|hiring|stellt)"
        ),
        re.compile(r"\b([A-ZÄÖÜ][A-Za-zÄÖÜäöüß0-9&.\-]{2,})\s+(?:GmbH|AG|SE|KG|UG)\b"),
    )
    _COMPANY_SUFFIX = re.compile(
        r"\b(?:GmbH|AG|SE|KG|UG|Ltd\.?|Inc\.?|LLC|GmbH & Co\. KG)\b", re.IGNORECASE
    )
    _TITLE_KEYWORDS: tuple[str, ...] = (
        "engineer",
        "entwickler",
        "developer",
        "manager",
        "analyst",
        "consultant",
        "scientist",
        "architect",
        "specialist",
        "designer",
        "owner",
        "lead",
        "leiter",
    )
    _SENIORITY_CUES: tuple[tuple[str, str], ...] = (
        ("principal", "Principal"),
        ("lead", "Lead"),
        ("senior", "Senior"),
        ("jr", "Junior"),
        ("junior", "Junior"),
        ("werkstudent", "Working Student"),
        ("intern", "Intern"),
    )
    _EMPLOYMENT_TYPES: tuple[tuple[str, str], ...] = (
        ("full-time", "Full-time"),
        ("full time", "Full-time"),
        ("vollzeit", "Vollzeit"),
        ("part-time", "Part-time"),
        ("part time", "Part-time"),
        ("teilzeit", "Teilzeit"),
    )
    _LOCATION_LABEL_TERMS = {label.lower() for label in _LOCATION_LABELS}
    _LABELED_CITY_PATTERN = re.compile(
        r"(?im)^(?:" + "|".join(_LOCATION_LABELS) + r")[\s/:\-]*([A-ZÄÖÜ][^\n\r]*)"
    )
    _LOCATION_PATTERN = re.compile(
        r"(?im)(?:Standort|Location|Arbeitsort|based in|in)[:\s]+([A-ZÄÖÜ][^\n\r]*)",
    )
    _RESP_SECTION_PREFIXES: tuple[str, ...] = (
        "aufgaben",
        "deine aufgaben",
        "was dich erwartet",
        "responsibilities",
        "what you will do",
    )
    _SKILL_KEYWORDS: tuple[str, ...] = (
        "Python",
        "Pandas",
        "SQL",
        "Azure",
        "AWS",
        "Docker",
        "Kubernetes",
        "Java",
        "JavaScript",
        "Typescript",
        "Excel",
    )

    def extract(self, raw: RawInput) -> ExtractionResult:
        content = raw.content
        result = ExtractionResult()
        schema_fields: Dict[str, object] = {}

        lines = [line.strip() for line in content.splitlines() if line.strip()]
        lowered = content.lower()

        role_fields = extract_role_required_fields(content)
        result.job_title = role_fields.job_title
        result.seniority = role_fields.seniority_level
        result.department = role_fields.department

        result.company = extract_company_name(content) or self._extract_company(content)

        regex_seniority = extract_seniority(content)
        if regex_seniority:
            result.seniority = regex_seniority
        if not result.seniority:
            result.seniority = self._extract_seniority(lowered)
        if not result.seniority and result.job_title:
            result.seniority = detect_seniority_level(result.job_title)

        job_title_candidate = extract_job_title(content)
        if job_title_candidate:
            result.job_title = job_title_candidate
        if not result.job_title:
            result.job_title = self._extract_job_title(lines, result.seniority, content)
        if not result.job_title and role_fields.job_title:
            result.job_title = role_fields.job_title

        result.location = extract_primary_city(content)
        if not result.location:
            result.location = self._extract_location(content)

        result.employment_type = extract_employment_type(content)
        if not result.employment_type:
            result.employment_type = self._extract_employment_type(lowered)

        result.contract_type = extract_contract_type(content)

        start_date_info = extract_desired_start_date(content)
        if start_date_info:
            result.start_date = start_date_info.get(
                "normalized"
            ) or start_date_info.get("raw")

        department_candidate = extract_department(content)
        if department_candidate:
            result.department = department_candidate

        result.responsibilities = self._extract_responsibilities(lines)
        result.must_have_skills = self._extract_skills(lowered)

        if (
            result.seniority
            and result.job_title
            and result.seniority not in result.job_title
        ):
            result.job_title = f"{result.seniority} {result.job_title}"

        _set_schema_field(schema_fields, Keys.COMPANY_NAME, result.company)
        _set_schema_field(schema_fields, Keys.POSITION_TITLE, result.job_title)
        _set_schema_field(schema_fields, Keys.POSITION_SENIORITY, result.seniority)
        _set_schema_field(schema_fields, Keys.TEAM_DEPT, result.department)
        _set_schema_field(schema_fields, Keys.LOCATION_CITY, result.location)
        _set_schema_field(schema_fields, Keys.EMPLOYMENT_TYPE, result.employment_type)
        _set_schema_field(schema_fields, Keys.EMPLOYMENT_CONTRACT, result.contract_type)
        _set_schema_field(schema_fields, Keys.EMPLOYMENT_START, result.start_date)

        result.schema_fields = schema_fields

        return result

    def _extract_company(self, content: str) -> str | None:
        for pattern in self._COMPANY_PATTERNS:
            match = pattern.search(content)
            if match:
                candidate = match.group(1).strip()
                candidate = self._COMPANY_SUFFIX.sub("", candidate).strip()
                candidate = re.sub(
                    r"\b(?:ist|is)$", "", candidate, flags=re.IGNORECASE
                ).strip()
                if len(candidate) > 80:
                    continue
                if candidate:
                    return candidate
        return None

    def _extract_seniority(self, lowered: str) -> str | None:
        for cue, label in self._SENIORITY_CUES:
            if cue in lowered:
                return label
        return None

    def _extract_job_title(
        self, lines: list[str], seniority: str | None, raw_content: str
    ) -> str | None:
        title_candidates: list[str] = []
        title_pattern = re.compile(
            rf"(?i)(senior|lead|principal|junior)?\s*(?:(?:{'|'.join(self._TITLE_KEYWORDS)})[\w\s/\-()]{{0,60}})"
        )

        for line in lines:
            normalized = clean_title(line)
            lower_line = normalized.lower()
            if len(normalized) < 6 or len(normalized) > 120:
                continue
            if any(keyword in lower_line for keyword in self._TITLE_KEYWORDS):
                title_candidates.append(normalized)
                continue
            match = title_pattern.search(normalized)
            if match:
                title_candidates.append(match.group(0).strip())

        if title_candidates:
            best = title_candidates[0]
            if seniority and seniority not in best:
                return f"{seniority} {best}"
            return best
        match = re.search(
            r"(?:als|as)\s+([A-ZÄÖÜ][^.,\n]{5,80})", raw_content, re.IGNORECASE
        )
        if match:
            return match.group(1).strip()
        return None

    def _extract_location(self, content: str) -> str | None:
        lines = [line.strip() for line in content.splitlines() if line.strip()]

        for line in lines:
            labeled_match = self._LABELED_CITY_PATTERN.match(line)
            if labeled_match:
                candidate = clean_city(labeled_match.group(1))
                if candidate and candidate.lower() not in self._LOCATION_LABEL_TERMS:
                    return candidate

        match = self._LOCATION_PATTERN.search(content)
        if match:
            return clean_city(match.group(1))
        return None

    def _extract_employment_type(self, lowered: str) -> str | None:
        for cue, label in self._EMPLOYMENT_TYPES:
            if cue in lowered:
                return label
        return None

    def _extract_responsibilities(self, lines: list[str]) -> list[str]:
        responsibilities: list[str] = []
        capturing = False
        for line in lines:
            lower_line = line.lower()
            if any(
                lower_line.startswith(prefix) for prefix in self._RESP_SECTION_PREFIXES
            ):
                capturing = True
                continue
            if capturing:
                if not line.strip():
                    if responsibilities:
                        break
                    continue
                if line.startswith(("-", "•", "*")):
                    responsibilities.append(line.lstrip("-•* ").strip())
                    continue
                if responsibilities and len(line) < 160:
                    responsibilities.append(line.strip())
        if not responsibilities:
            for line in lines:
                if line.startswith(("-", "•", "*")) and len(line) < 160:
                    responsibilities.append(line.lstrip("-•* ").strip())
        return responsibilities[:10]

    def _extract_skills(self, lowered: str) -> list[str]:
        skills: list[str] = []
        for keyword in self._SKILL_KEYWORDS:
            if keyword.lower() in lowered:
                skills.append(keyword)
        return skills


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
