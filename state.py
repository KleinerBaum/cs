from __future__ import annotations

from typing import Any, Mapping

import streamlit as st
from pydantic import BaseModel, ConfigDict, Field

from src.keys import Keys
from src.profile import get_value, new_profile, set_field


class ProfileState(BaseModel):
    """Company profile and contact details."""

    model_config = ConfigDict(validate_assignment=True)

    company_name: str | None = None
    company_website: str | None = None
    company_industry: str | None = None
    company_size: str | None = None
    company_hq: str | None = None
    description: str | None = None
    contact_name: str | None = None
    contact_email: str | None = None

    def is_complete(self) -> bool:
        return bool(_non_empty(self.company_name) and _non_empty(self.contact_email))


class RoleState(BaseModel):
    """Role-specific information including team and position context."""

    model_config = ConfigDict(validate_assignment=True)

    job_title: str | None = None
    job_title_en: str | None = None
    job_family: str | None = None
    seniority: str | None = None
    role_summary: str | None = None
    reports_to_title: str | None = None
    people_management: bool | None = None
    direct_reports: int | None = None
    department: str | None = None
    team_name: str | None = None
    reporting_line: str | None = None
    headcount_current: int | None = None
    headcount_target: int | None = None
    collaboration_tools: list[str] = Field(default_factory=list)
    employment_type: str | None = None
    contract_type: str | None = None
    start_date: str | None = None
    work_policy: str | None = None
    location_city: str | None = None
    remote_scope: str | None = None
    timezone_requirements: str | None = None
    travel_required: bool | None = None
    travel_percentage: float | None = None
    tasks: list[str] = Field(default_factory=list)

    def is_complete(self) -> bool:
        return bool(
            _non_empty(self.job_title)
            and _non_empty(self.seniority)
            and _non_empty(self.employment_type)
            and _non_empty(self.contract_type)
            and _non_empty(self.location_city)
            and _non_empty(self.start_date)
            and _non_empty(self.tasks)
        )


class SkillsState(BaseModel):
    """Skills and language requirements for the role."""

    model_config = ConfigDict(validate_assignment=True)

    must_have_skills: list[str] = Field(default_factory=list)
    must_have_skills_en: list[str] = Field(default_factory=list)
    soft_skills: list[str] = Field(default_factory=list)
    soft_skills_en: list[str] = Field(default_factory=list)
    nice_to_have_skills: list[str] = Field(default_factory=list)
    languages_required: list[str] = Field(default_factory=list)
    tools: list[str] = Field(default_factory=list)
    must_not_haves: list[str] = Field(default_factory=list)

    def is_complete(self) -> bool:
        return bool(
            _non_empty(self.must_have_skills)
            and _non_empty(self.soft_skills)
            and _non_empty(self.languages_required)
            and _non_empty(self.tools)
        )


class CompensationState(BaseModel):
    """Compensation expectations and benefits."""

    model_config = ConfigDict(validate_assignment=True)

    salary_provided: bool | None = None
    salary_min: float | None = None
    salary_max: float | None = None
    currency: str | None = None
    period: str | None = None
    benefits: list[str] = Field(default_factory=list)

    def is_complete(self) -> bool:
        return _non_empty(self.benefits)


class ForecastConfig(BaseModel):
    """Configuration for forecast/salary estimation."""

    model_config = ConfigDict(validate_assignment=True)

    apply_salary_forecast: bool = False
    selected_factors: list[str] = Field(default_factory=list)

    def is_complete(self) -> bool:  # noqa: D401 - short helper
        """Return True when forecast is enabled and has factors, or disabled."""

        if not self.apply_salary_forecast:
            return True
        return bool(self.selected_factors)


class ForecastState(BaseModel):
    """Forecast results and configuration."""

    model_config = ConfigDict(validate_assignment=True)

    config: ForecastConfig = Field(default_factory=ForecastConfig)
    result: Mapping[str, Any] | None = None
    narrative: str | None = None

    def is_complete(self) -> bool:
        return self.config.is_complete()


class AppState(BaseModel):
    """Aggregate application state across all wizard sections."""

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


def _non_empty(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, list):
        return any(_non_empty(v) for v in value)
    return True


_KEY_TO_STATE_PATH: dict[str, str] = {
    Keys.COMPANY_NAME: "profile.company_name",
    Keys.COMPANY_WEBSITE: "profile.company_website",
    Keys.COMPANY_INDUSTRY: "profile.company_industry",
    Keys.COMPANY_SIZE: "profile.company_size",
    Keys.COMPANY_HQ: "profile.company_hq",
    Keys.COMPANY_DESC: "profile.description",
    Keys.COMPANY_CONTACT_NAME: "profile.contact_name",
    Keys.COMPANY_CONTACT_EMAIL: "profile.contact_email",
    Keys.TEAM_DEPT: "role.department",
    Keys.TEAM_NAME: "role.team_name",
    Keys.TEAM_REPORTING_LINE: "role.reporting_line",
    Keys.TEAM_HEADCOUNT_CURRENT: "role.headcount_current",
    Keys.TEAM_HEADCOUNT_TARGET: "role.headcount_target",
    Keys.TEAM_TOOLS: "role.collaboration_tools",
    Keys.POSITION_TITLE: "role.job_title",
    Keys.POSITION_TITLE_EN: "role.job_title_en",
    Keys.POSITION_FAMILY: "role.job_family",
    Keys.POSITION_SENIORITY: "role.seniority",
    Keys.POSITION_SUMMARY: "role.role_summary",
    Keys.POSITION_REPORTS_TO_TITLE: "role.reports_to_title",
    Keys.POSITION_PEOPLE_MGMT: "role.people_management",
    Keys.POSITION_DIRECT_REPORTS: "role.direct_reports",
    Keys.LOCATION_WORK_POLICY: "role.work_policy",
    Keys.LOCATION_CITY: "role.location_city",
    Keys.LOCATION_REMOTE_SCOPE: "role.remote_scope",
    Keys.LOCATION_TZ: "role.timezone_requirements",
    Keys.LOCATION_TRAVEL_REQUIRED: "role.travel_required",
    Keys.LOCATION_TRAVEL_PCT: "role.travel_percentage",
    Keys.EMPLOYMENT_TYPE: "role.employment_type",
    Keys.EMPLOYMENT_CONTRACT: "role.contract_type",
    Keys.EMPLOYMENT_START: "role.start_date",
    Keys.RESPONSIBILITIES: "role.tasks",
    Keys.HARD_REQ: "skills.must_have_skills",
    Keys.HARD_REQ_EN: "skills.must_have_skills_en",
    Keys.SOFT_REQ: "skills.soft_skills",
    Keys.SOFT_REQ_EN: "skills.soft_skills_en",
    Keys.HARD_OPT: "skills.nice_to_have_skills",
    Keys.LANG_REQ: "skills.languages_required",
    Keys.TOOLS: "skills.tools",
    Keys.MUST_NOT: "skills.must_not_haves",
    Keys.SALARY_PROVIDED: "compensation.salary_provided",
    Keys.SALARY_MIN: "compensation.salary_min",
    Keys.SALARY_MAX: "compensation.salary_max",
    Keys.SALARY_CURRENCY: "compensation.currency",
    Keys.SALARY_PERIOD: "compensation.period",
    Keys.BENEFITS_ITEMS: "compensation.benefits",
}


def value_for_key(state: AppState, key: str) -> Any:
    """Return the value for a canonical key from the current AppState."""

    path = _KEY_TO_STATE_PATH.get(key)
    if not path:
        return None
    return _get_nested(state, path.split("."))


def app_state_from_profile(profile: Mapping[str, Any]) -> AppState:
    """Build an AppState instance from the existing profile mapping."""

    data: dict[str, Any] = {}
    for key, state_path in _KEY_TO_STATE_PATH.items():
        value = get_value(profile, key)
        if value is None:
            continue
        _assign_nested(data, state_path.split("."), value)
    return AppState(**data)


def apply_app_state_to_profile(
    state: AppState, profile: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Write AppState values back into a profile dictionary."""

    profile = profile or new_profile()
    for key, state_path in _KEY_TO_STATE_PATH.items():
        value = _get_nested(state, state_path.split("."))
        if value is None:
            continue
        set_field(profile, key, value, provenance="user", confidence=1.0)
    return profile


def get_app_state() -> AppState:
    """Fetch the AppState from Streamlit session state, syncing from profile."""

    profile = st.session_state.get("profile") or new_profile()
    state = app_state_from_profile(profile)
    st.session_state["app_state"] = state
    return state


def set_app_state(state: AppState) -> None:
    """Persist an AppState into session state and mirror it to the profile."""

    st.session_state["app_state"] = state
    st.session_state["profile"] = apply_app_state_to_profile(
        state, st.session_state.get("profile")
    )


def _assign_nested(target: dict[str, Any], path: list[str], value: Any) -> None:
    current: dict[str, Any] = target
    for part in path[:-1]:
        current = current.setdefault(part, {})
    current[path[-1]] = value


def _get_nested(state: AppState, path: list[str]) -> Any:
    current: Any = state
    for part in path:
        current = getattr(current, part)
    return current
