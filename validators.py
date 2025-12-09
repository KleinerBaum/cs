from __future__ import annotations

from typing import Any

from src.i18n import t
from src.question_engine import question_help, question_label, question_bank
from state import SectionState


def validate_section(
    profile: dict[str, Any], step: str, *, lang: str
) -> dict[str, str]:
    """Validate a wizard section and return field-level errors."""

    state = SectionState.from_profile(profile, step)
    required_questions = {
        q.path: q for q in question_bank() if q.step == step and q.required
    }
    errors: dict[str, str] = {}
    for path in state.missing_fields():
        question = required_questions.get(path)
        label = question_label(question, lang) if question else str(path)
        hint = question_help(question, lang) if question else None
        base = t(lang, "validation.required")
        errors[path] = f"{label} — {base}" + (f" ({hint})" if hint else "")
    return errors
