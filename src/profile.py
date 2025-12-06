from __future__ import annotations

import copy
import json
from datetime import date, datetime
from typing import Any, Literal

from .keys import REQUIRED_FIELDS

Provenance = Literal["extracted", "user", "ai_suggestion"]


def now_iso() -> str:
    return datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


def new_profile(ui_language: str = "de") -> dict[str, Any]:
    return {
        "meta": {
            "profile_schema": "NeedAnalysisProfile",
            "profile_schema_version": "1.0",
            "ui_language": ui_language,
            "source_language_detected": None,
            "created_at": now_iso(),
            "updated_at": now_iso(),
        },
        # Fields are stored as dot-path -> record
        "fields": {},
    }


def _jsonable(value: Any) -> Any:
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    return value


def get_record(profile: dict[str, Any], path: str) -> dict[str, Any] | None:
    return profile.get("fields", {}).get(path)


def get_value(profile: dict[str, Any], path: str, default: Any = None) -> Any:
    rec = get_record(profile, path)
    if not rec:
        return default
    return rec.get("value", default)


def set_field(
    profile: dict[str, Any],
    path: str,
    value: Any,
    provenance: Provenance,
    confidence: float | None = None,
    evidence: str | None = None,
) -> None:
    value = _jsonable(value)
    rec: dict[str, Any] = {
        "value": value,
        "provenance": provenance,
        "confidence": confidence,
        "evidence": evidence,
        "updated_at": now_iso(),
    }
    profile.setdefault("fields", {})[path] = rec
    profile.setdefault("meta", {})["updated_at"] = now_iso()


def clear_field(profile: dict[str, Any], path: str) -> None:
    profile.get("fields", {}).pop(path, None)
    profile.setdefault("meta", {})["updated_at"] = now_iso()


def upsert_field(
    profile: dict[str, Any],
    path: str,
    value: Any,
    provenance: Provenance,
    confidence: float | None = None,
    evidence: str | None = None,
    prefer_existing_user: bool = True,
) -> bool:
    """Set a field if it improves the profile.

    Returns True if an update was applied.
    """
    value = _jsonable(value)
    existing = get_record(profile, path)

    if existing and prefer_existing_user and existing.get("provenance") == "user" and provenance != "user":
        return False

    # If value is empty-ish, don't overwrite a filled field
    if existing and not is_missing_value(existing.get("value")) and is_missing_value(value):
        return False

    # If both have confidences, keep the higher-confidence value
    ex_conf = existing.get("confidence") if existing else None
    if existing and ex_conf is not None and confidence is not None and ex_conf >= confidence and provenance != "user":
        return False

    set_field(profile, path, value, provenance=provenance, confidence=confidence, evidence=evidence)
    return True


def is_missing_value(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str) and not value.strip():
        return True
    if isinstance(value, list) and len([v for v in value if str(v).strip()]) == 0:
        return True
    return False


def is_missing(profile: dict[str, Any], path: str) -> bool:
    rec = get_record(profile, path)
    if not rec:
        return True
    return is_missing_value(rec.get("value"))


def missing_required(profile: dict[str, Any]) -> list[str]:
    return [p for p in sorted(REQUIRED_FIELDS) if is_missing(profile, p)]


def flatten_values(profile: dict[str, Any], include_meta: bool = False) -> dict[str, Any]:
    out = {path: rec.get("value") for path, rec in profile.get("fields", {}).items()}
    if include_meta:
        out = {"_meta": copy.deepcopy(profile.get("meta", {})), **out}
    return out


def to_json(profile: dict[str, Any], indent: int = 2) -> str:
    return json.dumps(profile, ensure_ascii=False, indent=indent)


def update_source_language(profile: dict[str, Any], lang: str | None) -> None:
    profile.setdefault("meta", {})["source_language_detected"] = lang
    profile.setdefault("meta", {})["updated_at"] = now_iso()
