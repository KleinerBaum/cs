"""Regex-first role extraction with optional LLM fallback."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, Iterable

from src.llm_prompts import LLMClient, safe_parse_json
from src.settings import MAX_SOURCE_TEXT_CHARS


@dataclass(slots=True)
class RoleExtraction:
    """Structured role fields extracted from a job ad."""

    job_title: str | None = None
    seniority_level: str | None = None
    department: str | None = None
    evidence: Dict[str, str] = field(default_factory=dict)


_TITLE_HINTS = (
    "engineer",
    "entwickler",
    "developer",
    "manager",
    "leiter",
    "owner",
    "analyst",
    "consultant",
    "designer",
    "scientist",
    "architect",
    "specialist",
    "product",
    "marketing",
    "sales",
    "hr",
)

_TITLE_LABEL_PATTERN = re.compile(
    r"(?im)^(?:position|rolle|role|title|jobtitel)\s*[:\-–—]\s*(.+)$"
)
_HIRING_PATTERN = re.compile(
    r"(?im)wir\s+suchen\s+(?:einen|eine|ein|a|an)?\s*(?P<title>[^\n\r.,]{3,140}?)(?=(?:\s+(?:für|for|in)\b|[.,\n]))"
)
_HEADER_PATTERN = re.compile(r"(?im)^[#*\-•\s]*(?P<title>[A-ZÄÖÜ][^\n\r]{3,140})$")
_DEPARTMENT_PATTERN = re.compile(
    r"(?im)^(?:abteilung|team|bereich|department)[\s:=-]+(.{3,120})$"
)
_SENIORITY_MAP: tuple[tuple[str, str], ...] = (
    (r"\bprincipal\b", "Principal"),
    (r"\blead\b", "Lead"),
    (r"\bteamleiter\b", "Lead"),
    (r"\bleitung\b", "Lead"),
    (r"\bsenior\b", "Senior"),
    (r"\bmid\b", "Mid"),
    (r"\bmedior\b", "Mid"),
    (r"\bjunior\b", "Junior"),
)

_ROLE_SCHEMA = {
    "type": "json_schema",
    "json_schema": {
        "name": "RoleExtraction",
        "schema": {
            "type": "object",
            "properties": {
                "job_title": {"type": "string"},
                "seniority_level": {"type": "string"},
                "department": {"type": "string"},
                "evidence": {
                    "type": "object",
                    "additionalProperties": {"type": "string"},
                },
            },
            "required": [],
            "additionalProperties": False,
        },
        "strict": True,
    },
}


def clean_title(raw: str) -> str:
    """Normalize a raw title string by trimming and removing noise."""

    cleaned = " ".join(raw.split()).strip("\t ")
    cleaned = cleaned.strip("-•* ")
    cleaned = re.sub(r"^(?:ein|eine|einen|a|an)\s+", "", cleaned, flags=re.IGNORECASE)
    cleaned = cleaned.rstrip(".,;:–—- ")
    return cleaned.strip()


def detect_seniority_level(text: str) -> str | None:
    lowered = text.lower()
    for pattern, label in _SENIORITY_MAP:
        if re.search(pattern, lowered):
            return label
    return None


def _looks_like_title(candidate: str) -> bool:
    lowered = candidate.lower()
    return any(hint in lowered for hint in _TITLE_HINTS) or "m/w/d" in lowered


def _strip_bullet(line: str) -> str:
    return line.strip().strip("-•*# ")


def _extract_job_title(lines: Iterable[str]) -> tuple[str | None, str | None]:
    for line in lines:
        match = _TITLE_LABEL_PATTERN.search(line)
        if match:
            candidate = clean_title(match.group(1))
            if candidate:
                return candidate, match.group(0).strip()

    for line in lines:
        match = _HIRING_PATTERN.search(line)
        if match:
            candidate = clean_title(match.group("title"))
            if candidate:
                return candidate, match.group(0).strip()

    for line in lines:
        stripped = _strip_bullet(line)
        header_match = _HEADER_PATTERN.match(stripped)
        if header_match:
            candidate = clean_title(header_match.group("title"))
            if candidate and _looks_like_title(candidate):
                return candidate, stripped

    return None, None


def _extract_department(lines: Iterable[str]) -> tuple[str | None, str | None]:
    for line in lines:
        match = _DEPARTMENT_PATTERN.search(line)
        if match:
            candidate = clean_title(match.group(1))
            if candidate:
                return candidate, match.group(0).strip()
    return None, None


def extract_role_required_fields(text: str) -> RoleExtraction:
    """Regex-first extractor for role step fields."""

    result = RoleExtraction()
    lines = [line.strip() for line in text.splitlines() if line.strip()]

    job_title, title_evidence = _extract_job_title(lines)
    if job_title:
        result.job_title = job_title
    if title_evidence:
        result.evidence["job_title"] = title_evidence

    department, dept_evidence = _extract_department(lines)
    if department:
        result.department = department
    if dept_evidence:
        result.evidence["department"] = dept_evidence

    seniority = detect_seniority_level(text)
    if seniority:
        result.seniority_level = seniority
        result.evidence["seniority_level"] = seniority
    elif job_title:
        seniority_from_title = detect_seniority_level(job_title)
        if seniority_from_title:
            result.seniority_level = seniority_from_title
            result.evidence["seniority_level"] = job_title

    return result


def _role_prompt(source_text: str) -> str:
    return (
        "Extract ONLY the role fields from the job ad. Return JSON with"
        " job_title, seniority_level (Junior, Mid, Senior, Lead, Principal),"
        " department, and an evidence map with short quotes."
        f" Source text:\n---\n{source_text}\n---"
    )


def llm_fill_role_fields(
    text: str, *, client: LLMClient, missing_fields: set[str] | None = None
) -> RoleExtraction:
    """LLM fallback to recover role fields when regex fails."""

    target_fields = missing_fields or {"job_title", "seniority_level", "department"}
    prompt = _role_prompt(text[:MAX_SOURCE_TEXT_CHARS])
    raw = client.text(
        prompt,
        instructions=(
            "Use structured JSON output only. Leave fields empty when unsure;"
            " never invent companies or departments unrelated to the text."
        ),
        max_output_tokens=480,
        response_format=_ROLE_SCHEMA,
    )
    parsed = safe_parse_json(raw) if raw else {}

    result = RoleExtraction()
    if not isinstance(parsed, dict):
        return result

    evidence_map = (
        parsed.get("evidence") if isinstance(parsed.get("evidence"), dict) else {}
    )

    if "job_title" in target_fields:
        title_val = parsed.get("job_title")
        if isinstance(title_val, str):
            cleaned = clean_title(title_val)
            if cleaned:
                result.job_title = cleaned
                if isinstance(evidence_map, dict) and evidence_map.get("job_title"):
                    result.evidence["job_title"] = str(evidence_map["job_title"])

    if "seniority_level" in target_fields:
        seniority_val = parsed.get("seniority_level")
        if isinstance(seniority_val, str):
            seniority = detect_seniority_level(seniority_val) or seniority_val.strip()
            if seniority and seniority.capitalize() in {
                "Junior",
                "Mid",
                "Senior",
                "Lead",
                "Principal",
            }:
                result.seniority_level = seniority.capitalize()
                if isinstance(evidence_map, dict) and evidence_map.get(
                    "seniority_level"
                ):
                    result.evidence["seniority_level"] = str(
                        evidence_map["seniority_level"]
                    )

    if "department" in target_fields:
        dept_val = parsed.get("department")
        if isinstance(dept_val, str):
            cleaned = clean_title(dept_val)
            if cleaned:
                result.department = cleaned
                if isinstance(evidence_map, dict) and evidence_map.get("department"):
                    result.evidence["department"] = str(evidence_map["department"])

    return result
