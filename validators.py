from __future__ import annotations

from typing import Any, Iterable

from src.i18n import t
from src.question_engine import question_bank, question_help, question_label
from state import (
    AppState,
    CompensationState,
    ProfileState,
    RoleState,
    SkillsState,
    app_state_from_profile,
    value_for_key,
)

_REQUIRED_PROFILE = (
    "company.name",
    "location.primary_city",
    "employment.employment_type",
    "employment.contract_type",
    "employment.start_date",
)
_REQUIRED_ROLE = (
    "position.job_title",
    "position.seniority_level",
    "team.department_name",
)
_REQUIRED_SKILLS = (
    "responsibilities.items",
    "requirements.hard_skills_required",
)
_REQUIRED_COMPENSATION = (
    "compensation.salary_min",
    "compensation.salary_max",
    "compensation.currency",
    "benefits.items",
)


def _non_empty(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, list):
        return any(_non_empty(v) for v in value)
    return True


def _build_error(path: str, lang: str) -> tuple[str, str]:
    questions = {q.path: q for q in question_bank()}
    question = questions.get(path)
    label = question_label(question, lang) if question else path
    hint = question_help(question, lang) if question else ""
    message = f"{label} — {t(lang, 'validation.required')}"
    if hint:
        message = f"{message} ({hint})"
    return path, message


def _collect_missing(
    required_paths: Iterable[str], state: AppState, *, lang: str
) -> list[tuple[str, str]]:
    missing: list[tuple[str, str]] = []
    for path in required_paths:
        value = value_for_key(state, path)
        if not _non_empty(value):
            missing.append(_build_error(path, lang))
    return missing


def validate_profile(profile: ProfileState, *, lang: str) -> list[tuple[str, str]]:
    state = AppState(profile=profile)
    return _collect_missing(_REQUIRED_PROFILE, state, lang=lang)


def validate_role(role: RoleState, *, lang: str) -> list[tuple[str, str]]:
    state = AppState(role=role)
    return _collect_missing(_REQUIRED_ROLE, state, lang=lang)


def validate_skills(skills: SkillsState, *, lang: str) -> list[tuple[str, str]]:
    state = AppState(skills=skills)
    return _collect_missing(_REQUIRED_SKILLS, state, lang=lang)


def validate_compensation(
    comp: CompensationState, *, lang: str
) -> list[tuple[str, str]]:
    state = AppState(compensation=comp)
    errors = _collect_missing(_REQUIRED_COMPENSATION, state, lang=lang)
    if (
        comp.salary_min is not None
        and comp.salary_max is not None
        and comp.salary_min > comp.salary_max
    ):
        errors.append(
            (
                "compensation.salary_min",
                t(lang, "validation.range"),
            )
        )
    return errors


def validate_app_step(app_state: AppState, step: str, *, lang: str) -> dict[str, str]:
    """Map a wizard step to validation errors keyed by profile path."""

    errors: list[tuple[str, str]]
    if step == "company":
        errors = validate_profile(app_state.profile, lang=lang)
    elif step in {"team", "framework", "tasks"}:
        errors = validate_role(app_state.role, lang=lang)
    elif step == "skills":
        errors = validate_skills(app_state.skills, lang=lang)
    elif step == "benefits":
        errors = validate_compensation(app_state.compensation, lang=lang)
    else:
        errors = []
    return {field: message for field, message in errors}


def validate_section(
    profile: dict[str, Any], step: str, *, lang: str
) -> dict[str, str]:
    """Compatibility wrapper to validate using the new AppState model."""

    app_state = app_state_from_profile(profile)
    return validate_app_step(app_state, step, lang=lang)
