from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Iterable

from src.keys import (
    CONTRACT_TYPE_VALUES,
    EMPLOYMENT_TYPE_VALUES,
    SENIORITY_VALUES,
    SALARY_PERIOD_VALUES,
    WORK_POLICY_VALUES,
    Keys,
)

ShowIf = Callable[[dict[str, Any]], bool]
Postprocessor = Callable[[Any], Any]
ValidatorHook = Callable[[Any], bool]


@dataclass(frozen=True)
class FieldSpec:
    """Canonical specification for a single profile field."""

    key: str
    step: str
    required: bool
    label_de: str
    label_en: str
    regex_patterns: tuple[str, ...] = ()
    postprocessor: Postprocessor | None = None
    validator: ValidatorHook | None = None
    # UI wiring (kept optional to separate schema vs. rendering concerns)
    question_id: str | None = None
    input_type: str | None = None
    help_de: str = ""
    help_en: str = ""
    advanced: bool = False
    options_group: str | None = None
    options_values: tuple[str, ...] | None = None
    show_if: ShowIf | None = None


def _is_remote(profile: dict[str, Any]) -> bool:
    from src.profile import get_value as _get_value

    return _get_value(profile, Keys.LOCATION_WORK_POLICY) == "remote"


def _travel_required(profile: dict[str, Any]) -> bool:
    from src.profile import get_value as _get_value

    return bool(_get_value(profile, Keys.LOCATION_TRAVEL_REQUIRED))


def _people_management(profile: dict[str, Any]) -> bool:
    from src.profile import get_value as _get_value

    return bool(_get_value(profile, Keys.POSITION_PEOPLE_MGMT))


FIELD_SPECS: tuple[FieldSpec, ...] = (
    # --- Company
    FieldSpec(
        key=Keys.COMPANY_NAME,
        question_id="company_name",
        step="company",
        input_type="text",
        required=True,
        label_de="Unternehmensname*",
        label_en="Company name*",
        help_de="Wie heißt das Unternehmen?",
        help_en="What is the company name?",
    ),
    FieldSpec(
        key=Keys.COMPANY_WEBSITE,
        question_id="company_website",
        step="company",
        input_type="text",
        required=False,
        label_de="Website",
        label_en="Website",
    ),
    FieldSpec(
        key=Keys.COMPANY_INDUSTRY,
        question_id="company_industry",
        step="company",
        input_type="text",
        required=False,
        label_de="Branche",
        label_en="Industry",
    ),
    FieldSpec(
        key=Keys.COMPANY_SIZE,
        question_id="company_size",
        step="company",
        input_type="text",
        required=False,
        label_de="Unternehmensgröße",
        label_en="Company size",
        help_de="z.B. 50–200 Mitarbeitende",
        help_en="e.g. 50–200 employees",
        advanced=True,
    ),
    FieldSpec(
        key=Keys.COMPANY_HQ,
        question_id="company_hq",
        step="company",
        input_type="text",
        required=False,
        label_de="HQ/Standort",
        label_en="HQ location",
        advanced=True,
    ),
    FieldSpec(
        key=Keys.COMPANY_DESC,
        question_id="company_desc",
        step="company",
        input_type="textarea",
        required=False,
        label_de="Kurzbeschreibung",
        label_en="Short description",
        advanced=True,
    ),
    FieldSpec(
        key=Keys.COMPANY_CONTACT_NAME,
        question_id="company_contact_name",
        step="company",
        input_type="text",
        required=False,
        label_de="Kontaktperson (Name)",
        label_en="Contact person (name)",
        advanced=True,
    ),
    FieldSpec(
        key=Keys.COMPANY_CONTACT_EMAIL,
        question_id="company_contact_email",
        step="company",
        input_type="email",
        required=False,
        label_de="Kontaktperson (E-Mail)",
        label_en="Contact email",
    ),
    # --- Team
    FieldSpec(
        key=Keys.TEAM_DEPT,
        question_id="team_dept",
        step="team",
        input_type="text",
        required=True,
        label_de="Abteilung*",
        label_en="Department*",
    ),
    FieldSpec(
        key=Keys.TEAM_NAME,
        question_id="team_name",
        step="team",
        input_type="text",
        required=False,
        label_de="Teamname",
        label_en="Team name",
        advanced=True,
    ),
    FieldSpec(
        key=Keys.TEAM_REPORTING_LINE,
        question_id="team_reporting_line",
        step="team",
        input_type="text",
        required=False,
        label_de="Reporting Line",
        label_en="Reporting line",
        advanced=True,
    ),
    FieldSpec(
        key=Keys.TEAM_HEADCOUNT_CURRENT,
        question_id="team_headcount_current",
        step="team",
        input_type="number",
        required=False,
        label_de="Headcount aktuell",
        label_en="Current headcount",
        advanced=True,
    ),
    FieldSpec(
        key=Keys.TEAM_HEADCOUNT_TARGET,
        question_id="team_headcount_target",
        step="team",
        input_type="number",
        required=False,
        label_de="Headcount Ziel",
        label_en="Target headcount",
        advanced=True,
    ),
    FieldSpec(
        key=Keys.TEAM_TOOLS,
        question_id="team_tools",
        step="team",
        input_type="list",
        required=False,
        label_de="Kollaborationstools",
        label_en="Collaboration tools",
        advanced=True,
    ),
    # --- Position
    FieldSpec(
        key=Keys.POSITION_TITLE,
        question_id="position_title",
        step="team",
        input_type="text",
        required=True,
        label_de="Jobtitel*",
        label_en="Job title*",
    ),
    FieldSpec(
        key=Keys.POSITION_TITLE_EN,
        question_id="position_title_en",
        step="team",
        input_type="text",
        required=False,
        label_de="Jobtitel (englische Version, optional)",
        label_en="Job title (English version, optional)",
        help_de="Optional, aber hilfreich für internationale Anzeigen.",
        help_en="Optional, but useful for English postings.",
        advanced=True,
    ),
    FieldSpec(
        key=Keys.POSITION_FAMILY,
        question_id="position_family",
        step="team",
        input_type="text",
        required=False,
        label_de="Job-Familie",
        label_en="Job family",
    ),
    FieldSpec(
        key=Keys.POSITION_SENIORITY,
        question_id="position_seniority",
        step="team",
        input_type="select",
        required=True,
        label_de="Seniority Level*",
        label_en="Seniority level*",
        options_group="seniority",
        options_values=SENIORITY_VALUES,
    ),
    FieldSpec(
        key=Keys.POSITION_SUMMARY,
        question_id="position_summary",
        step="framework",
        input_type="textarea",
        required=False,
        label_de="Zusammenfassung der Rolle",
        label_en="Role summary",
        advanced=True,
    ),
    FieldSpec(
        key=Keys.POSITION_REPORTS_TO_TITLE,
        question_id="position_reports_to_title",
        step="framework",
        input_type="text",
        required=False,
        label_de="Direkte/r Vorgesetzte/r (Titel)",
        label_en="Reports to (job title)",
        advanced=True,
    ),
    FieldSpec(
        key=Keys.POSITION_PEOPLE_MGMT,
        question_id="position_people_mgmt",
        step="framework",
        input_type="bool",
        required=False,
        label_de="Hat Führungsverantwortung?",
        label_en="Includes people management?",
        advanced=True,
    ),
    FieldSpec(
        key=Keys.POSITION_DIRECT_REPORTS,
        question_id="position_direct_reports",
        step="framework",
        input_type="number",
        required=False,
        label_de="Anzahl direkte Reports",
        label_en="Number of direct reports",
        show_if=_people_management,
        advanced=True,
    ),
    # --- Framework (Location/Employment)
    FieldSpec(
        key=Keys.LOCATION_WORK_POLICY,
        question_id="location_work_policy",
        step="framework",
        input_type="select",
        required=False,
        label_de="Arbeitsmodell",
        label_en="Work policy",
        options_group="work_policy",
        options_values=WORK_POLICY_VALUES,
    ),
    FieldSpec(
        key=Keys.LOCATION_CITY,
        question_id="location_city",
        step="framework",
        input_type="text",
        required=True,
        label_de="Hauptstandort/Stadt*",
        label_en="Primary location (city)*",
    ),
    FieldSpec(
        key=Keys.LOCATION_REMOTE_SCOPE,
        question_id="location_remote_scope",
        step="framework",
        input_type="text",
        required=False,
        label_de="Remote-Anteil / -Region",
        label_en="Remote scope / region",
        show_if=_is_remote,
        advanced=True,
    ),
    FieldSpec(
        key=Keys.LOCATION_TZ,
        question_id="location_tz",
        step="framework",
        input_type="text",
        required=False,
        label_de="Zeitzone(n)",
        label_en="Timezone(s)",
        show_if=_is_remote,
        advanced=True,
    ),
    FieldSpec(
        key=Keys.LOCATION_TRAVEL_REQUIRED,
        question_id="location_travel_required",
        step="framework",
        input_type="bool",
        required=False,
        label_de="Reisetätigkeit erforderlich?",
        label_en="Travel required?",
        advanced=True,
    ),
    FieldSpec(
        key=Keys.LOCATION_TRAVEL_PCT,
        question_id="location_travel_pct",
        step="framework",
        input_type="number",
        required=False,
        label_de="Reisetätigkeit (% Arbeitszeit)",
        label_en="Approx. travel (% of time)",
        show_if=_travel_required,
        advanced=True,
    ),
    FieldSpec(
        key=Keys.EMPLOYMENT_TYPE,
        question_id="employment_type",
        step="framework",
        input_type="select",
        required=True,
        label_de="Anstellungsart*",
        label_en="Employment type*",
        options_group="employment_type",
        options_values=EMPLOYMENT_TYPE_VALUES,
    ),
    FieldSpec(
        key=Keys.EMPLOYMENT_CONTRACT,
        question_id="employment_contract",
        step="framework",
        input_type="select",
        required=True,
        label_de="Vertragsart*",
        label_en="Contract type*",
        options_group="contract_type",
        options_values=CONTRACT_TYPE_VALUES,
    ),
    FieldSpec(
        key=Keys.EMPLOYMENT_START,
        question_id="employment_start",
        step="framework",
        input_type="date",
        required=True,
        label_de="Gewünschtes Startdatum*",
        label_en="Desired start date*",
    ),
    FieldSpec(
        key=Keys.EMPLOYMENT_VISA,
        question_id="employment_visa",
        step="framework",
        input_type="bool",
        required=False,
        label_de="Visa-Sponsoring möglich?",
        label_en="Visa sponsorship possible?",
        advanced=True,
    ),
    # --- Compensation
    FieldSpec(
        key=Keys.SALARY_CURRENCY,
        question_id="salary_currency",
        step="benefits",
        input_type="text",
        required=True,
        label_de="Währung*",
        label_en="Currency*",
        help_de="z.B. EUR, USD",
        help_en="e.g. EUR, USD",
    ),
    FieldSpec(
        key=Keys.SALARY_MIN,
        question_id="salary_min",
        step="benefits",
        input_type="number",
        required=True,
        label_de="Gehalt Minimum*",
        label_en="Salary minimum*",
    ),
    FieldSpec(
        key=Keys.SALARY_MAX,
        question_id="salary_max",
        step="benefits",
        input_type="number",
        required=True,
        label_de="Gehalt Maximum*",
        label_en="Salary maximum*",
    ),
    FieldSpec(
        key=Keys.SALARY_PERIOD,
        question_id="salary_period",
        step="benefits",
        input_type="select",
        required=False,
        label_de="Auszahlungsrhythmus",
        label_en="Compensation period",
        options_group="salary_period",
        options_values=SALARY_PERIOD_VALUES,
        advanced=True,
    ),
    FieldSpec(
        key=Keys.COMPENSATION_VARIABLE,
        question_id="compensation_variable",
        step="benefits",
        input_type="number",
        required=False,
        label_de="Variable Vergütung (%)",
        label_en="Variable compensation (%)",
        advanced=True,
    ),
    FieldSpec(
        key=Keys.COMPENSATION_RELOCATION,
        question_id="compensation_relocation",
        step="benefits",
        input_type="bool",
        required=False,
        label_de="Umzugsunterstützung",
        label_en="Relocation support",
        advanced=True,
    ),
    # --- Tasks & Responsibilities
    FieldSpec(
        key=Keys.RESPONSIBILITIES,
        question_id="responsibilities",
        step="tasks",
        input_type="list",
        required=True,
        label_de="Aufgaben/Pakete*",
        label_en="Key responsibilities*",
    ),
    # --- Skills Requirements
    FieldSpec(
        key=Keys.HARD_REQ,
        question_id="hard_req",
        step="skills",
        input_type="list",
        required=True,
        label_de="Hard Skills (Pflicht)*",
        label_en="Hard skills (required)*",
    ),
    FieldSpec(
        key=Keys.HARD_REQ_EN,
        question_id="hard_req_en",
        step="skills",
        input_type="list",
        required=False,
        label_de="Hard Skills (englische Version, optional)",
        label_en="Hard skills (English version, optional)",
        advanced=True,
    ),
    FieldSpec(
        key=Keys.HARD_OPT,
        question_id="hard_opt",
        step="skills",
        input_type="list",
        required=False,
        label_de="Hard Skills (optional)",
        label_en="Hard skills (optional)",
    ),
    FieldSpec(
        key=Keys.SOFT_REQ,
        question_id="soft_req",
        step="skills",
        input_type="list",
        required=False,
        label_de="Soft Skills",
        label_en="Soft skills",
    ),
    FieldSpec(
        key=Keys.SOFT_REQ_EN,
        question_id="soft_req_en",
        step="skills",
        input_type="list",
        required=False,
        label_de="Soft Skills (englische Version, optional)",
        label_en="Soft skills (English version, optional)",
        advanced=True,
    ),
    FieldSpec(
        key=Keys.LANG_REQ,
        question_id="lang_req",
        step="skills",
        input_type="list",
        required=False,
        label_de="Sprachen",
        label_en="Languages",
    ),
    FieldSpec(
        key=Keys.TOOLS,
        question_id="tools",
        step="skills",
        input_type="list",
        required=False,
        label_de="Tools & Technologien",
        label_en="Tools & technologies",
    ),
    FieldSpec(
        key=Keys.TOOLS_EN,
        question_id="tools_en",
        step="skills",
        input_type="list",
        required=False,
        label_de="Tools & Technologien (englische Version, optional)",
        label_en="Tools & technologies (English version, optional)",
        advanced=True,
    ),
    FieldSpec(
        key=Keys.MUST_NOT,
        question_id="must_not",
        step="skills",
        input_type="list",
        required=False,
        label_de="No-Gos (Ausschlusskriterien)",
        label_en="Must-not-haves",
        advanced=True,
    ),
    # --- Benefits
    FieldSpec(
        key=Keys.BENEFITS_ITEMS,
        question_id="benefits_items",
        step="benefits",
        input_type="list",
        required=True,
        label_de="Benefits & Angebote*",
        label_en="Benefits & perks*",
    ),
    # --- Recruiting Process
    FieldSpec(
        key=Keys.PROCESS_STAGES,
        question_id="process_stages",
        step="process",
        input_type="list",
        required=False,
        label_de="Interview-Stufen",
        label_en="Interview stages",
    ),
    FieldSpec(
        key=Keys.PROCESS_TIMELINE,
        question_id="process_timeline",
        step="process",
        input_type="text",
        required=False,
        label_de="Voraussichtlicher Prozessablauf",
        label_en="Expected timeline",
        advanced=True,
    ),
    FieldSpec(
        key=Keys.PROCESS_INSTRUCTIONS,
        question_id="process_instructions",
        step="process",
        input_type="textarea",
        required=False,
        label_de="Hinweise zur Bewerbung",
        label_en="Application instructions",
        advanced=True,
    ),
    FieldSpec(
        key=Keys.PROCESS_CONTACT,
        question_id="process_contact",
        step="process",
        input_type="email",
        required=False,
        label_de="Kontakt-E-Mail für Bewerbung",
        label_en="Contact email for application",
        help_de="Falls unterschiedlich von obiger Kontaktperson.",
        help_en="If different from the contact person above.",
        advanced=True,
    ),
)

_FIELD_SPECS_BY_KEY: dict[str, FieldSpec] = {spec.key: spec for spec in FIELD_SPECS}


def field_specs() -> tuple[FieldSpec, ...]:
    return FIELD_SPECS


def field_specs_by_step(step: str) -> tuple[FieldSpec, ...]:
    return tuple(spec for spec in FIELD_SPECS if spec.step == step)


def get_field_spec(key: str) -> FieldSpec | None:
    return _FIELD_SPECS_BY_KEY.get(key)


def all_field_keys() -> set[str]:
    return set(_FIELD_SPECS_BY_KEY)


def required_field_keys() -> set[str]:
    return {spec.key for spec in FIELD_SPECS if spec.required}


def required_field_keys_by_step(step: str) -> tuple[str, ...]:
    return tuple(spec.key for spec in field_specs_by_step(step) if spec.required)


def iter_required_specs() -> Iterable[FieldSpec]:
    return (spec for spec in FIELD_SPECS if spec.required)


__all__ = [
    "FieldSpec",
    "field_specs",
    "field_specs_by_step",
    "get_field_spec",
    "all_field_keys",
    "required_field_keys",
    "required_field_keys_by_step",
    "iter_required_specs",
]
