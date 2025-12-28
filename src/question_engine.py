from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from src.field_registry import FieldSpec, field_specs

from .i18n import LANG_DE
from .profile import is_missing
from .settings import MAX_PRIMARY_QUESTIONS_PER_STEP

ShowIf = Callable[[dict[str, Any]], bool]


@dataclass(frozen=True)
class Question:
    id: str
    path: str
    step: str
    input_type: str  # e.g. text|textarea|email|bool|number|date|select|multiselect|list
    required: bool = False
    advanced: bool = False
    label_de: str = ""
    label_en: str = ""
    help_de: str = ""
    help_en: str = ""
    options_group: str | None = None
    options_values: tuple[str, ...] | None = None
    show_if: ShowIf | None = None


STEPS: tuple[str, ...] = (
    "intake",
    "company",
    "team",
    "framework",
    "tasks",
    "skills",
    "benefits",
    "process",
    "review",
)


def _spec_to_question(spec: FieldSpec) -> Question:
    return Question(
        id=spec.question_id or spec.key,
        path=spec.key,
        step=spec.step,
        input_type=spec.input_type or "text",
        required=spec.required,
        advanced=spec.advanced,
        label_de=spec.label_de,
        label_en=spec.label_en,
        help_de=spec.help_de,
        help_en=spec.help_en,
        options_group=spec.options_group,
        options_values=spec.options_values,
        show_if=spec.show_if,
    )


def question_bank() -> list[Question]:
    """Single source of truth for all questions (DE/EN)."""

    return [_spec_to_question(spec) for spec in field_specs() if spec.input_type]


def select_questions_for_step(profile: dict[str, Any], step: str) -> tuple[list[Question], list[Question]]:
    """Return (primary, advanced) question lists for a given step."""
    qs = [
        q
        for q in question_bank()
        if q.step == step and (not q.show_if or q.show_if(profile))
    ]
    primary: list[Question] = []
    advanced: list[Question] = []
    for q in qs:
        if q.advanced or q.id.startswith("intake_"):
            advanced.append(q)
        else:
            primary.append(q)
    # Limit primary questions to avoid overwhelming the user
    if len(primary) > MAX_PRIMARY_QUESTIONS_PER_STEP:
        primary = primary[:MAX_PRIMARY_QUESTIONS_PER_STEP]
        advanced = [q for q in qs if q not in primary]
    return primary, advanced


def missing_required_for_step(profile: dict[str, Any], step: str) -> list[str]:
    """Return list of required field labels missing in the current step."""
    labels: list[str] = []
    for q in question_bank():
        if q.step == step and q.required and is_missing(profile, q.path):
            # Return the label in UI language (German by default)
            labels.append(
                q.label_de
                if profile.get("meta", {}).get("ui_language") == LANG_DE
                else q.label_en
            )
    return labels


def iter_missing_optional(profile: dict[str, Any], questions: list[Question]) -> list[str]:
    """Return list of paths for optional questions (in given list) that are currently empty."""
    out: list[str] = []
    for q in questions:
        if q.required:
            continue
        if is_missing(profile, q.path):
            out.append(q.path)
    return out


def question_label(q: Question, lang: str) -> str:
    return q.label_de if lang == LANG_DE else q.label_en or q.label_de


def question_help(q: Question, lang: str) -> str:
    return q.help_de if lang == LANG_DE else q.help_en or q.help_de
