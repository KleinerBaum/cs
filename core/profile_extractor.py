from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict

from core.extractor import clean_city

# Allowed values align with UI expectations and validation helpers
ALLOWED_EMPLOYMENT_TYPES = {
    "full_time",
    "part_time",
    "contractor",
    "intern",
    "working_student",
    "freelance",
}
ALLOWED_CONTRACT_TYPES = {"permanent", "fixed_term"}

_COMPANY_SUFFIX = re.compile(
    r"\b(?:GmbH|AG|SE|KG|UG|GmbH & Co\. KG|Ltd\.?|Inc\.?|LLC)\b",
    re.IGNORECASE,
)


@dataclass(slots=True)
class ProfileRequiredExtraction:
    """Deterministic profile field extraction result."""

    company_name: str | None = None
    primary_city: str | None = None
    employment_type: str | None = None
    contract_type: str | None = None
    start_date: str | None = None
    evidence: Dict[str, str] = field(default_factory=dict)


_COMPANY_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(
        r"(?im)^\s*(?:unternehmensname|company)[:\s]+([A-ZÄÖÜ][A-Za-zÄÖÜäöüß0-9&.\-\s]{2,})$"
    ),
    re.compile(
        r"\b(?:bei|für|at|join(?:ing)?\s+)?([A-ZÄÖÜ][A-Za-zÄÖÜäöüß0-9&.\-\s]{2,})\s+(?:sucht|hire|hiring|stellt)"
    ),
    re.compile(r"(?i)über\s+uns\s+bei\s+([A-ZÄÖÜ][A-Za-zÄÖÜäöüß0-9&.\-\s]{2,})"),
    re.compile(r"\b([A-ZÄÖÜ][A-Za-zÄÖÜäöüß0-9&.\-]{2,})\s+(?:GmbH|AG|SE|KG|UG)\b"),
)

_LOCATION_LABELS = (
    "Hauptstandort",
    "Stadt",
    "Ort",
    "Arbeitsort",
    "Standort",
    "Location",
    "Primary City",
)
_LABELED_CITY_PATTERN = re.compile(
    r"(?im)^(?:" + "|".join(_LOCATION_LABELS) + r")[\s/:\-]*([A-ZÄÖÜ][^\n\r]*)"
)
_LOCATION_INLINE_PATTERN = re.compile(
    r"(?im)(?:Standort|Location|Arbeitsort|based in|in)[:\s]+([A-ZÄÖÜ][^\n\r]*)",
)

_EMPLOYMENT_MAP = {
    "vollzeit": "full_time",
    "full time": "full_time",
    "full-time": "full_time",
    "teilzeit": "part_time",
    "part time": "part_time",
    "part-time": "part_time",
    "werkstudent": "working_student",
    "working student": "working_student",
    "intern": "intern",
    "internship": "intern",
    "praktik": "intern",
    "freelance": "freelance",
    "freelancer": "freelance",
    "contractor": "contractor",
}

_CONTRACT_MAP = {
    "unbefrist": "permanent",
    "permanent": "permanent",
    "befrist": "fixed_term",
    "fixed-term": "fixed_term",
    "fixed term": "fixed_term",
    "zeitvertrag": "fixed_term",
}

_START_IMMEDIATE_PATTERN = re.compile(
    r"(?i)(ab\s+sofort|asap|a\.s\.a\.p\.|zum\s+nächstmöglichen\s+zeitpunkt|so\s+bald\s+wie\s+möglich)"
)
_START_DATE_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(
        r"(?i)(?:start|beginn|eintritt|startdatum)[:\s]*([0-9]{4}-[0-9]{2}-[0-9]{2})"
    ),
    re.compile(
        r"(?i)(?:start|beginn|eintritt|startdatum)[:\s]*([0-9]{1,2}\.[0-9]{1,2}\.[0-9]{2,4})"
    ),
    re.compile(
        r"(?i)(?:start|beginn|eintritt|startdatum)[:\s]*([0-9]{1,2}/[0-9]{1,2}/[0-9]{2,4})"
    ),
    re.compile(
        r"(?i)(?:start|beginn|eintritt|startdatum)[:\s]*([A-ZÄÖÜa-zäöü]+\s+[0-9]{1,2},?\s*[0-9]{4})"
    ),
)


def _normalize_company(raw: str | None) -> str | None:
    if not raw:
        return None
    cleaned = _COMPANY_SUFFIX.sub("", raw).strip()
    cleaned = re.sub(r"^(?:join|bei|für|at)\s+", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\b(?:ist|is)$", "", cleaned, flags=re.IGNORECASE).strip()
    if len(cleaned) < 2 or len(cleaned) > 120:
        return None
    return cleaned


def _extract_company(text: str, result: ProfileRequiredExtraction) -> None:
    for pattern in _COMPANY_PATTERNS:
        match = pattern.search(text)
        if match:
            candidate = _normalize_company(match.group(1))
            if candidate:
                result.company_name = candidate
                result.evidence["company_name"] = match.group(0).strip()
                return


def _extract_city(text: str, result: ProfileRequiredExtraction) -> None:
    for pattern in (_LABELED_CITY_PATTERN, _LOCATION_INLINE_PATTERN):
        match = pattern.search(text)
        if match:
            city_token = match.group(1).split(",", 1)[0]
            candidate = clean_city(city_token)
            if candidate:
                result.primary_city = candidate
                result.evidence["primary_city"] = match.group(0).strip()
                return


def _match_keyword(
    value: str, mapping: dict[str, str], allowed: set[str]
) -> str | None:
    lowered = value.lower()
    for key, mapped in mapping.items():
        if key in lowered and mapped in allowed:
            return mapped
    return None


def _extract_employment(text: str, result: ProfileRequiredExtraction) -> None:
    mapped = _match_keyword(text, _EMPLOYMENT_MAP, ALLOWED_EMPLOYMENT_TYPES)
    if mapped:
        result.employment_type = mapped
        result.evidence["employment_type"] = mapped


def _extract_contract(text: str, result: ProfileRequiredExtraction) -> None:
    mapped = _match_keyword(text, _CONTRACT_MAP, ALLOWED_CONTRACT_TYPES)
    if mapped:
        result.contract_type = mapped
        result.evidence["contract_type"] = mapped


def normalize_start_date(value: str) -> str | None:
    cleaned = value.strip().strip(".:, ")
    if not cleaned:
        return None
    immediate_match = _START_IMMEDIATE_PATTERN.search(cleaned)
    if immediate_match:
        return "ASAP"
    for pattern in _START_DATE_PATTERNS:
        match = pattern.search(cleaned)
        if match:
            return match.group(1).strip()
    # If input itself is a date-like token
    if re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", cleaned):
        return cleaned
    if re.fullmatch(r"[0-9]{1,2}\.[0-9]{1,2}\.[0-9]{2,4}", cleaned):
        return cleaned
    return None


def _extract_start_date(text: str, result: ProfileRequiredExtraction) -> None:
    immediate = _START_IMMEDIATE_PATTERN.search(text)
    if immediate:
        result.start_date = "ASAP"
        result.evidence["start_date"] = immediate.group(0).strip()
        return
    for pattern in _START_DATE_PATTERNS:
        match = pattern.search(text)
        if match:
            normalized = normalize_start_date(match.group(1))
            if normalized:
                result.start_date = normalized
                result.evidence["start_date"] = match.group(0).strip()
                return


def extract_profile_required_fields(text: str) -> ProfileRequiredExtraction:
    """Regex-first extractor for key profile fields."""

    result = ProfileRequiredExtraction()
    _extract_company(text, result)
    _extract_city(text, result)
    _extract_employment(text, result)
    _extract_contract(text, result)
    _extract_start_date(text, result)
    return result
