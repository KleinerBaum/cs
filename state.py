"""Centralized application state for the Need-Analysis wizard."""

from __future__ import annotations

from typing import Any

import streamlit as st
from pydantic import BaseModel, ConfigDict, Field

from src.keys import Keys


STATE_SESSION_KEY = "app_state"


class ProfileState(BaseModel):
    """Company profile and employment basics."""

    model_config = ConfigDict(validate_assignment=True)

    company_name: str | None = None
    primary_city: str | None = None
    employment_type: str | None = None
    contract_type: str | None = None
    start_date: str | None = None
    remote_policy: str | None = None

    def is_complete(self) -> bool:
        return all(
            [
                _non_empty(self.company_name),
                _non_empty(self.primary_city),
                _non_empty(self.employment_type),
                _non_empty(self.contract_type),
                _non_empty(self.start_date),
            ]
        )


class RoleState(BaseModel):
    """Role information for the vacancy."""

    model_config = ConfigDict(validate_assignment=True)

    job_title: str | None = None
    seniority: str | None = None
    department: str | None = None
    direct_reports: int | None = None
    work_schedule: str | None = None
    summary: str | None = None

    def is_complete(self) -> bool:
        return all(
            [
                _non_empty(self.job_title),
                _non_empty(self.seniority),
                _non_empty(self.department),
            ]
        )


class SkillsState(BaseModel):
    """Skills, tasks, and expectations."""

    model_config = ConfigDict(validate_assignment=True)

    tasks: list[str] = Field(default_factory=list)
    must_have: list[str] = Field(default_factory=list)
    nice_to_have: list[str] = Field(default_factory=list)

    def is_complete(self) -> bool:
        return _non_empty(self.tasks) and _non_empty(self.must_have)


class CompensationState(BaseModel):
    """Compensation expectations and benefits."""

    model_config = ConfigDict(validate_assignment=True)

    currency: str | None = None
    salary_min: float | None = None
    salary_max: float | None = None
    benefits: list[str] = Field(default_factory=list)
    variable_pct: float | None = None
    relocation: bool | None = None
    visa: bool | None = None

    def is_complete(self) -> bool:
        return all(
            [
                _non_empty(self.currency),
                self.salary_min is not None,
                self.salary_max is not None,
                _non_empty(self.benefits),
            ]
        )


class ForecastConfig(BaseModel):
    """Configuration inputs for forecasting."""

    model_config = ConfigDict(validate_assignment=True)

    budget_total: float | None = None
    conv_top_to_screen: float | None = None
    conv_screen_to_offer: float | None = None
    conv_offer_to_hire: float | None = None
    ttf_mean_days: float | None = None
    ttf_std_days: float | None = None

    def is_ready(self) -> bool:
        return all(
            value is not None
            for value in (
                self.budget_total,
                self.conv_top_to_screen,
                self.conv_screen_to_offer,
                self.conv_offer_to_hire,
                self.ttf_mean_days,
                self.ttf_std_days,
            )
        )


class ForecastResult(BaseModel):
    """Result of a forecast simulation."""

    model_config = ConfigDict(validate_assignment=True)

    expected_days: float
    optimistic_days: float
    pessimistic_days: float
    hires_possible: float
    samples: list[float] = Field(default_factory=list)


class ForecastState(BaseModel):
    """Forecast config plus most recent result."""

    model_config = ConfigDict(validate_assignment=True)

    config: ForecastConfig = Field(default_factory=ForecastConfig)
    result: ForecastResult | None = None

    def is_complete(self) -> bool:
        return self.config.is_ready()


class AppState(BaseModel):
    """Aggregated wizard state across all pages."""

    model_config = ConfigDict(validate_assignment=True)

    profile: ProfileState = Field(default_factory=ProfileState)
    role: RoleState = Field(default_factory=RoleState)
    skills: SkillsState = Field(default_factory=SkillsState)
    compensation: CompensationState = Field(default_factory=CompensationState)
    forecast: ForecastState = Field(default_factory=ForecastState)

    def is_complete(self) -> bool:
        return (
            self.profile.is_complete()
            and self.role.is_complete()
            and self.skills.is_complete()
            and self.compensation.is_complete()
            and self.forecast.is_complete()
        )


_KEY_TO_STATE_PATH: dict[str, str] = {
    Keys.COMPANY_NAME: "profile.company_name",
    Keys.LOCATION_CITY: "profile.primary_city",
    Keys.EMPLOYMENT_TYPE: "profile.employment_type",
    Keys.EMPLOYMENT_CONTRACT: "profile.contract_type",
    Keys.EMPLOYMENT_START: "profile.start_date",
    Keys.LOCATION_WORK_POLICY: "profile.remote_policy",
    Keys.POSITION_TITLE: "role.job_title",
    Keys.POSITION_SENIORITY: "role.seniority",
    Keys.TEAM_DEPT: "role.department",
    Keys.POSITION_DIRECT_REPORTS: "role.direct_reports",
    Keys.POSITION_SUMMARY: "role.summary",
    Keys.EMPLOYMENT_SCHEDULE: "role.work_schedule",
    Keys.RESPONSIBILITIES: "skills.tasks",
    Keys.HARD_REQ: "skills.must_have",
    Keys.HARD_OPT: "skills.nice_to_have",
    Keys.SALARY_MIN: "compensation.salary_min",
    Keys.SALARY_MAX: "compensation.salary_max",
    Keys.SALARY_CURRENCY: "compensation.currency",
    Keys.BENEFITS_ITEMS: "compensation.benefits",
    Keys.COMPENSATION_VARIABLE: "compensation.variable_pct",
    Keys.COMPENSATION_RELOCATION: "compensation.relocation",
    Keys.EMPLOYMENT_VISA: "compensation.visa",
}


def get_app_state() -> AppState:
    """Return the current AppState from Streamlit session_state."""

    stored = st.session_state.get(STATE_SESSION_KEY)
    if isinstance(stored, AppState):
        return stored
    state = AppState()
    st.session_state[STATE_SESSION_KEY] = state
    return state


def set_app_state(state: AppState) -> None:
    """Persist the given AppState into session_state."""

    st.session_state[STATE_SESSION_KEY] = state


def apply_app_state_to_profile(state: AppState) -> dict[str, Any]:
    """Export AppState values into a NeedAnalysisProfile mapping."""

    profile: dict[str, Any] = {}
    for key, path in _KEY_TO_STATE_PATH.items():
        try:
            value = _get_nested(state, path.split("."))
        except AttributeError:
            continue
        if value is None:
            continue
        _assign_nested(profile, key.split("."), value)
    return profile


def value_for_key(state: AppState, key: str) -> Any:
    """Return a value from AppState using canonical Keys.* constants."""

    path = _KEY_TO_STATE_PATH.get(key)
    if not path:
        return None
    try:
        return _get_nested(state, path.split("."))
    except AttributeError:
        return None


def _assign_nested(target: dict[str, Any], path: list[str], value: Any) -> None:
    current = target
    for part in path[:-1]:
        current = current.setdefault(part, {})
    current[path[-1]] = value


def _get_nested(state: AppState, path: list[str]) -> Any:
    current: Any = state
    for part in path:
        current = getattr(current, part)
    if isinstance(current, BaseModel):
        return current.model_dump()
    return current


def _non_empty(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, list):
        return any(_non_empty(v) for v in value)
    return True


__all__ = [
    "AppState",
    "ProfileState",
    "RoleState",
    "SkillsState",
    "CompensationState",
    "ForecastConfig",
    "ForecastResult",
    "ForecastState",
    "get_app_state",
    "set_app_state",
    "apply_app_state_to_profile",
    "value_for_key",
]
