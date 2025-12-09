from __future__ import annotations

from typing import Any, ClassVar

from pydantic import BaseModel, ConfigDict

from src.profile import get_value
from src.question_engine import question_bank


class SectionState(BaseModel):
    """Container for the required fields of a wizard section."""

    model_config = ConfigDict(arbitrary_types_allowed=True, frozen=True)

    step: str
    required_paths: tuple[str, ...]
    values: dict[str, Any]

    @classmethod
    def from_profile(cls, profile: dict[str, Any], step: str) -> "SectionState":
        required = tuple(
            q.path for q in question_bank() if q.step == step and q.required
        )
        values = {path: get_value(profile, path) for path in required}
        state_cls = SECTION_STATE_MAP.get(step, cls)
        return state_cls(step=step, required_paths=required, values=values)

    def missing_fields(self) -> list[str]:
        missing: list[str] = []
        for path in self.required_paths:
            value = self.values.get(path)
            if value in (None, "", [], {}):
                missing.append(path)
        return missing

    def is_complete(self) -> bool:
        return not self.missing_fields()


class CompanyState(SectionState):
    step_id: ClassVar[str] = "company"


class TeamState(SectionState):
    step_id: ClassVar[str] = "team"


class FrameworkState(SectionState):
    step_id: ClassVar[str] = "framework"


class TasksState(SectionState):
    step_id: ClassVar[str] = "tasks"


class SkillsState(SectionState):
    step_id: ClassVar[str] = "skills"


class BenefitsState(SectionState):
    step_id: ClassVar[str] = "benefits"


class ProcessState(SectionState):
    step_id: ClassVar[str] = "process"


SECTION_STATE_MAP: dict[str, type[SectionState]] = {
    cls.step_id: cls
    for cls in (
        CompanyState,
        TeamState,
        FrameworkState,
        TasksState,
        SkillsState,
        BenefitsState,
        ProcessState,
    )
}
