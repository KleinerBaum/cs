from __future__ import annotations

import re
from datetime import datetime
from typing import Iterable

from core.role_extractor import clean_title

_STOPWORDS_TRAILING = {
    "eine",
    "einen",
    "einem",
    "einer",
    "der",
    "die",
    "das",
    "und",
    "oder",
    "a",
    "an",
    "the",
}
_CONNECTOR_WORDS = {
    "am",
    "an",
    "im",
    "in",
    "bei",
    "der",
    "die",
    "das",
    "de",
    "del",
    "della",
    "da",
    "do",
    "dos",
    "du",
    "van",
    "von",
    "of",
    "la",
    "le",
}
_SEPARATORS = [",", ";", "|", "\n", " - ", " / ", "("]
_CITY_ALLOWED_CHARS = re.compile(r"[^A-Za-zÄÖÜäöüß\- ]+")

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
_COMPANY_SUFFIX = re.compile(
    r"\b(?:GmbH|AG|SE|KG|UG|GmbH & Co\. KG|Ltd\.?|Inc\.?|LLC)\b", re.IGNORECASE
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
_LOCATION_LABEL_TERMS = {label.lower() for label in _LOCATION_LABELS}
_LABELED_CITY_PATTERN = re.compile(
    r"(?im)^(?:" + "|".join(_LOCATION_LABELS) + r")[\s/:\-]*([^\n\r]+)"
)
_INLINE_CITY_PATTERN = re.compile(
    r"(?im)\b(?:Standort|Location|Arbeitsort|based in|in)\s+([A-ZÄÖÜ][^\n\r]*)"
)

_EMPLOYMENT_CUES: tuple[tuple[str, str], ...] = (
    ("vollzeit", "Vollzeit"),
    ("full-time", "Full-time"),
    ("full time", "Full-time"),
    ("teilzeit", "Teilzeit"),
    ("part-time", "Teilzeit"),
    ("part time", "Teilzeit"),
    ("werkstudent", "Werkstudent"),
    ("working student", "Werkstudent"),
    ("praktik", "Praktikum"),
    ("intern", "Intern"),
    ("freelance", "Freelance"),
    ("contractor", "Contractor"),
)
_CONTRACT_CUES: tuple[tuple[str, str], ...] = (
    ("unbefrist", "Unbefristet"),
    ("permanent", "Unbefristet"),
    ("befrist", "Befristet"),
    ("fixed term", "Befristet"),
    ("fixed-term", "Befristet"),
)

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

_JOB_TITLE_PATTERN = re.compile(r"(?im)^(?:jobtitel|job title|title)[:\s]+(.+)$")
_DEPARTMENT_PATTERN = re.compile(r"(?im)^(?:abteilung|department)[:\s]+(.+)$")
_SENIORITY_CUES: tuple[tuple[str, str], ...] = (
    ("principal", "Principal"),
    ("lead", "Lead"),
    ("senior", "Senior"),
    ("jr", "Junior"),
    ("junior", "Junior"),
    ("werkstudent", "Working Student"),
    ("intern", "Intern"),
)


def _strip_separators(value: str) -> str:
    cleaned = value
    for sep in _SEPARATORS:
        if sep in cleaned:
            cleaned = cleaned.split(sep, 1)[0]
    return cleaned


def clean_city(candidate: str) -> str:
    """Sanitize a raw city candidate string."""

    if not candidate:
        return ""

    cleaned = _strip_separators(candidate).strip().strip(",;:|•")
    cleaned = _CITY_ALLOWED_CHARS.sub("", cleaned)
    tokens = cleaned.split()

    normalized_tokens: list[str] = []
    for token in tokens:
        if not token:
            continue
        if token[0].isupper() or token[0] in "ÄÖÜ":
            normalized_tokens.append(token)
            continue
        if token.lower() in _CONNECTOR_WORDS:
            normalized_tokens.append(token)
            continue
        break

    while normalized_tokens and normalized_tokens[-1].lower() in _STOPWORDS_TRAILING:
        normalized_tokens.pop()

    cleaned_city = " ".join(normalized_tokens)
    return cleaned_city


def _normalize_company(raw: str | None, preserve_suffix: bool = False) -> str | None:
    if not raw:
        return None
    cleaned = raw.strip()
    cleaned = re.sub(r"^(?:join|bei|für|at)\s+", "", cleaned, flags=re.IGNORECASE)
    if not preserve_suffix:
        cleaned = _COMPANY_SUFFIX.sub("", cleaned).strip()
    cleaned = re.sub(r"\b(?:ist|is)$", "", cleaned, flags=re.IGNORECASE).strip()
    if len(cleaned) < 2 or len(cleaned) > 120:
        return None
    return cleaned


def extract_company_name(text: str) -> str | None:
    for idx, pattern in enumerate(_COMPANY_PATTERNS):
        match = pattern.search(text)
        if match:
            candidate = _normalize_company(match.group(1), preserve_suffix=idx == 0)
            if candidate:
                return candidate
    return None


def extract_primary_city(text: str) -> str | None:
    for pattern in (_LABELED_CITY_PATTERN, _INLINE_CITY_PATTERN):
        match = pattern.search(text)
        if match:
            candidate = clean_city(match.group(1))
            lowered = candidate.lower()
            tokens = candidate.split()
            while tokens and tokens[0].lower() in _LOCATION_LABEL_TERMS:
                tokens.pop(0)
            candidate = " ".join(tokens)
            lowered = candidate.lower()
            if candidate and lowered not in _LOCATION_LABEL_TERMS:
                return candidate
    return None


def _match_mapping(value: str, mapping: Iterable[tuple[str, str]]) -> str | None:
    lowered = value.lower()
    best: tuple[int, str] | None = None
    for cue, label in mapping:
        index = lowered.find(cue)
        if index != -1:
            if best is None or index < best[0]:
                best = (index, label)
    if best:
        return best[1]
    return None


def extract_employment_type(text: str) -> str | None:
    return _match_mapping(text, _EMPLOYMENT_CUES)


def extract_contract_type(text: str) -> str | None:
    return _match_mapping(text, _CONTRACT_CUES)


def _normalize_date_token(token: str) -> str | None:
    token = token.strip()
    for fmt in (
        "%Y-%m-%d",
        "%d.%m.%Y",
        "%d.%m.%y",
        "%d/%m/%Y",
        "%d/%m/%y",
        "%B %d %Y",
        "%d %B %Y",
    ):
        try:
            return datetime.strptime(token, fmt).date().isoformat()
        except ValueError:
            continue
    return None


def extract_desired_start_date(text: str) -> dict | None:
    immediate = _START_IMMEDIATE_PATTERN.search(text)
    if immediate:
        raw_value = immediate.group(0).strip()
        return {"raw": raw_value, "normalized": "ASAP"}

    for pattern in _START_DATE_PATTERNS:
        match = pattern.search(text)
        if match:
            raw_value = match.group(1).strip()
            normalized = _normalize_date_token(raw_value)
            payload = {"raw": raw_value}
            if normalized:
                payload["normalized"] = normalized
            return payload
    return None


def extract_job_title(text: str) -> str | None:
    match = _JOB_TITLE_PATTERN.search(text)
    if match:
        return clean_title(match.group(1))
    match = re.search(r"(?:als|as)\s+([A-ZÄÖÜ][^.,\n]{5,80})", text, re.IGNORECASE)
    if match:
        return clean_title(match.group(1))
    return None


def extract_seniority(text: str) -> str | None:
    lowered = text.lower()
    for cue, label in _SENIORITY_CUES:
        if cue in lowered:
            return label
    return None


def extract_department(text: str) -> str | None:
    match = _DEPARTMENT_PATTERN.search(text)
    if match:
        return match.group(1).strip()
    return None
