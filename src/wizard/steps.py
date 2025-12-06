# src/wizard/steps.py
from enum import Enum


class StepId(str, Enum):
    IMPORT = "import"
    COMPANY = "company"
    TEAM = "team"
    CONDITIONS = "conditions"
    TASKS = "tasks"
    SKILLS = "skills"
    BENEFITS = "benefits"
    PROCESS = "process"
    SUMMARY = "summary"


STEP_ORDER: list[StepId] = [
    StepId.IMPORT,
    StepId.COMPANY,
    StepId.TEAM,
    StepId.CONDITIONS,
    StepId.TASKS,
    StepId.SKILLS,
    StepId.BENEFITS,
    StepId.PROCESS,
    StepId.SUMMARY,
]
