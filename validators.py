from __future__ import annotations

from typing import Any, Iterable

from src.field_registry import required_field_keys_by_step
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

_PAGE_REQUIRED_STEPS = {
    "profile": ("company", "framework"),
    "role": ("team",),
    "skills": ("tasks", "skills"),
    "compensation": ("benefits",),
}


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


def _required_paths_for_steps(steps: Iterable[str]) -> tuple[str, ...]:
    required: list[str] = []
    for step in steps:
        required.extend(required_field_keys_by_step(step))
    # Preserve ordering while removing duplicates
    seen: set[str] = set()
    ordered: list[str] = []
    for path in required:
        if path in seen:
            continue
        seen.add(path)
        ordered.append(path)
    return tuple(ordered)


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
    state = app_state_from_profile(profile)
    return _collect_missing(
        _required_paths_for_steps(_PAGE_REQUIRED_STEPS["profile"]), state, lang=lang
    )


def validate_role(role: RoleState, *, lang: str) -> list[tuple[str, str]]:
    state = app_state_from_profile(role)
    return _collect_missing(
        _required_paths_for_steps(_PAGE_REQUIRED_STEPS["role"]), state, lang=lang
    )


def validate_skills(skills: SkillsState, *, lang: str) -> list[tuple[str, str]]:
    state = app_state_from_profile(skills)
    return _collect_missing(
        _required_paths_for_steps(_PAGE_REQUIRED_STEPS["skills"]), state, lang=lang
    )


def validate_compensation(
    comp: CompensationState, *, lang: str
) -> list[tuple[str, str]]:
    state = app_state_from_profile(comp)
    errors = _collect_missing(
        _required_paths_for_steps(_PAGE_REQUIRED_STEPS["compensation"]),
        state,
        lang=lang,
    )
    errors.extend(_range_errors(comp, lang))
    return errors


def _range_errors(
    comp: CompensationState, lang: str
) -> list[tuple[str, str]]:
    errors: list[tuple[str, str]] = []
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

    required_paths = _required_paths_for_steps((step,))
    errors = _collect_missing(required_paths, app_state, lang=lang)
    if step == "benefits":
        errors.extend(_range_errors(app_state.compensation, lang))
    return {field: message for field, message in errors}


def validate_section(
    profile: dict[str, Any], step: str, *, lang: str
) -> dict[str, str]:
    """Compatibility wrapper to validate using the new AppState model."""

    app_state = app_state_from_profile(profile)
    return validate_app_step(app_state, step, lang=lang)
