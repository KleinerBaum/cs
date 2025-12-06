from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Iterable

from .i18n import LANG_DE
from .keys import (
    CONTRACT_TYPE_VALUES,
    EMPLOYMENT_TYPE_VALUES,
    REQUIRED_FIELDS,
    SALARY_PERIOD_VALUES,
    SENIORITY_VALUES,
    WORK_POLICY_VALUES,
    Keys,
)
from .profile import get_record, get_value, is_missing
from .settings import LOW_CONFIDENCE_THRESHOLD, MAX_PRIMARY_QUESTIONS_PER_STEP

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

# Show/hide logic for conditional questions
def _is_remote(profile: dict[str, Any]) -> bool:
    return get_value(profile, Keys.LOCATION_WORK_POLICY) == "remote"

def _travel_required(profile: dict[str, Any]) -> bool:
    return bool(get_value(profile, Keys.LOCATION_TRAVEL_REQUIRED))

def _salary_provided(profile: dict[str, Any]) -> bool:
    return bool(get_value(profile, Keys.SALARY_PROVIDED))

def _people_mgmt(profile: dict[str, Any]) -> bool:
    return bool(get_value(profile, Keys.POSITION_PEOPLE_MGMT))

def question_bank() -> list[Question]:
    """Single source of truth for all questions (DE/EN)."""
    return [
        # --- Company
        Question(
            id="company_name",
            path=Keys.COMPANY_NAME,
            step="company",
            input_type="text",
            required=True,
            label_de="Unternehmensname*",
            label_en="Company name*",
            help_de="Wie heißt das Unternehmen?",
            help_en="What is the company name?",
        ),
        Question(
            id="company_website",
            path=Keys.COMPANY_WEBSITE,
            step="company",
            input_type="text",
            label_de="Website",
            label_en="Website",
            advanced=True,
        ),
        Question(
            id="company_industry",
            path=Keys.COMPANY_INDUSTRY,
            step="company",
            input_type="text",
            label_de="Branche",
            label_en="Industry",
        ),
        Question(
            id="company_size",
            path=Keys.COMPANY_SIZE,
            step="company",
            input_type="text",
            label_de="Unternehmensgröße",
            label_en="Company size",
            help_de="z.B. 50–200 Mitarbeitende",
            help_en="e.g. 50–200 employees",
            advanced=True,
        ),
        Question(
            id="company_hq",
            path=Keys.COMPANY_HQ,
            step="company",
            input_type="text",
            label_de="HQ/Standort",
            label_en="HQ location",
            advanced=True,
        ),
        Question(
            id="company_desc",
            path=Keys.COMPANY_DESC,
            step="company",
            input_type="textarea",
            label_de="Kurzbeschreibung",
            label_en="Short description",
            advanced=True,
        ),
        Question(
            id="company_contact_name",
            path=Keys.COMPANY_CONTACT_NAME,
            step="company",
            input_type="text",
            label_de="Kontaktperson (Name)",
            label_en="Contact person (name)",
            advanced=True,
        ),
        Question(
            id="company_contact_email",
            path=Keys.COMPANY_CONTACT_EMAIL,
            step="company",
            input_type="email",
            required=True,
            label_de="Kontaktperson (E-Mail)*",
            label_en="Contact email*",
        ),
        # --- Team
        Question(
            id="team_dept",
            path=Keys.TEAM_DEPT,
            step="team",
            input_type="text",
            label_de="Abteilung",
            label_en="Department",
        ),
        Question(
            id="team_name",
            path=Keys.TEAM_NAME,
            step="team",
            input_type="text",
            label_de="Teamname",
            label_en="Team name",
            advanced=True,
        ),
        Question(
            id="team_reporting_line",
            path=Keys.TEAM_REPORTING_LINE,
            step="team",
            input_type="text",
            label_de="Reporting Line",
            label_en="Reporting line",
            advanced=True,
        ),
        Question(
            id="team_headcount_current",
            path=Keys.TEAM_HEADCOUNT_CURRENT,
            step="team",
            input_type="number",
            label_de="Headcount aktuell",
            label_en="Current headcount",
            advanced=True,
        ),
        Question(
            id="team_headcount_target",
            path=Keys.TEAM_HEADCOUNT_TARGET,
            step="team",
            input_type="number",
            label_de="Headcount Ziel",
            label_en="Target headcount",
            advanced=True,
        ),
        Question(
            id="team_tools",
            path=Keys.TEAM_TOOLS,
            step="team",
            input_type="list",
            label_de="Kollaborationstools",
            label_en="Collaboration tools",
            advanced=True,
        ),
        # --- Position
        Question(
            id="position_title",
            path=Keys.POSITION_TITLE,
            step="team",
            input_type="text",
            required=True,
            label_de="Jobtitel*",
            label_en="Job title*",
        ),
        Question(
            id="position_title_en",
            path=Keys.POSITION_TITLE_EN,
            step="team",
            input_type="text",
            label_de="Jobtitel (englische Version, optional)",
            label_en="Job title (English version, optional)",
            help_de="Optional, aber hilfreich für internationale Anzeigen.",
            help_en="Optional, but useful for English postings.",
            advanced=True,
        ),
        Question(
            id="position_family",
            path=Keys.POSITION_FAMILY,
            step="team",
            input_type="text",
            label_de="Job-Familie",
            label_en="Job family",
        ),
        Question(
            id="position_seniority",
            path=Keys.POSITION_SENIORITY,
            step="team",
            input_type="select",
            required=True,
            label_de="Seniority Level*",
            label_en="Seniority level*",
            options_group="seniority",
            options_values=SENIORITY_VALUES,
        ),
        Question(
            id="position_summary",
            path=Keys.POSITION_SUMMARY,
            step="framework",
            input_type="textarea",
            label_de="Zusammenfassung der Rolle",
            label_en="Role summary",
            advanced=True,
        ),
        Question(
            id="position_reports_to_title",
            path=Keys.POSITION_REPORTS_TO_TITLE,
            step="framework",
            input_type="text",
            label_de="Direkte/r Vorgesetzte/r (Titel)",
            label_en="Reports to (job title)",
            advanced=True,
        ),
        Question(
            id="position_people_mgmt",
            path=Keys.POSITION_PEOPLE_MGMT,
            step="framework",
            input_type="bool",
            label_de="Hat Führungsverantwortung?",
            label_en="Includes people management?",
            advanced=True,
        ),
        Question(
            id="position_direct_reports",
            path=Keys.POSITION_DIRECT_REPORTS,
            step="framework",
            input_type="number",
            label_de="Anzahl direkte Reports",
            label_en="Number of direct reports",
            show_if=_people_mgmt,
            advanced=True,
        ),
        # --- Framework (Location/Employment)
        Question(
            id="location_work_policy",
            path=Keys.LOCATION_WORK_POLICY,
            step="framework",
            input_type="select",
            label_de="Arbeitsmodell",
            label_en="Work policy",
            options_group="work_policy",
            options_values=WORK_POLICY_VALUES,
        ),
        Question(
            id="location_city",
            path=Keys.LOCATION_CITY,
            step="framework",
            input_type="text",
            required=True,
            label_de="Hauptstandort/Stadt*",
            label_en="Primary location (city)*",
        ),
        Question(
            id="location_remote_scope",
            path=Keys.LOCATION_REMOTE_SCOPE,
            step="framework",
            input_type="text",
            label_de="Remote-Anteil / -Region",
            label_en="Remote scope / region",
            show_if=_is_remote,
            advanced=True,
        ),
        Question(
            id="location_tz",
            path=Keys.LOCATION_TZ,
            step="framework",
            input_type="text",
            label_de="Zeitzone(n)",
            label_en="Timezone(s)",
            show_if=_is_remote,
            advanced=True,
        ),
        Question(
            id="location_travel_required",
            path=Keys.LOCATION_TRAVEL_REQUIRED,
            step="framework",
            input_type="bool",
            label_de="Reisetätigkeit erforderlich?",
            label_en="Travel required?",
            advanced=True,
        ),
        Question(
            id="location_travel_pct",
            path=Keys.LOCATION_TRAVEL_PCT,
            step="framework",
            input_type="number",
            label_de="Reisetätigkeit (% Arbeitszeit)",
            label_en="Approx. travel (% of time)",
            show_if=_travel_required,
            advanced=True,
        ),
        Question(
            id="employment_type",
            path=Keys.EMPLOYMENT_TYPE,
            step="framework",
            input_type="select",
            required=True,
            label_de="Anstellungsart*",
            label_en="Employment type*",
            options_group="employment_type",
            options_values=EMPLOYMENT_TYPE_VALUES,
        ),
        Question(
            id="employment_contract",
            path=Keys.EMPLOYMENT_CONTRACT,
            step="framework",
            input_type="select",
            required=True,
            label_de="Vertragsart*",
            label_en="Contract type*",
            options_group="contract_type",
            options_values=CONTRACT_TYPE_VALUES,
        ),
        Question(
            id="employment_start",
            path=Keys.EMPLOYMENT_START,
            step="framework",
            input_type="date",
            required=True,
            label_de="Gewünschtes Startdatum*",
            label_en="Desired start date*",
        ),
        Question(
            id="employment_visa",
            path=Keys.EMPLOYMENT_VISA,
            step="framework",
            input_type="bool",
            label_de="Visa-Sponsoring möglich?",
            label_en="Visa sponsorship possible?",
            advanced=True,
        ),
        # --- Tasks & Responsibilities
        Question(
            id="responsibilities",
            path=Keys.RESPONSIBILITIES,
            step="tasks",
            input_type="list",
            required=True,
            label_de="Aufgaben/Pakete*",
            label_en="Key responsibilities*",
        ),
        # --- Skills Requirements
        Question(
            id="hard_req",
            path=Keys.HARD_REQ,
            step="skills",
            input_type="list",
            required=True,
            label_de="Hard Skills (Pflicht)*",
            label_en="Hard skills (required)*",
        ),
        Question(
            id="hard_req_en",
            path=Keys.HARD_REQ_EN,
            step="skills",
            input_type="list",
            label_de="Hard Skills (englische Version, optional)",
            label_en="Hard skills (English version, optional)",
            advanced=True,
        ),
        Question(
            id="hard_opt",
            path=Keys.HARD_OPT,
            step="skills",
            input_type="list",
            label_de="Hard Skills (optional)",
            label_en="Hard skills (optional)",
        ),
        Question(
            id="soft_req",
            path=Keys.SOFT_REQ,
            step="skills",
            input_type="list",
            required=True,
            label_de="Soft Skills (Pflicht)*",
            label_en="Soft skills (required)*",
        ),
        Question(
            id="soft_req_en",
            path=Keys.SOFT_REQ_EN,
            step="skills",
            input_type="list",
            label_de="Soft Skills (englische Version, optional)",
            label_en="Soft skills (English version, optional)",
            advanced=True,
        ),
        Question(
            id="lang_req",
            path=Keys.LANG_REQ,
            step="skills",
            input_type="list",
            required=True,
            label_de="Sprachen (Pflicht)*",
            label_en="Languages (required)*",
        ),
        Question(
            id="tools",
            path=Keys.TOOLS,
            step="skills",
            input_type="list",
            required=True,
            label_de="Tools & Technologien (Pflicht)*",
            label_en="Tools & technologies (required)*",
        ),
        Question(
            id="tools_en",
            path=Keys.TOOLS_EN,
            step="skills",
            input_type="list",
            label_de="Tools & Technologien (englische Version, optional)",
            label_en="Tools & technologies (English version, optional)",
            advanced=True,
        ),
        Question(
            id="must_not",
            path=Keys.MUST_NOT,
            step="skills",
            input_type="list",
            label_de="No-Gos (Ausschlusskriterien)",
            label_en="Must-not-haves",
            advanced=True,
        ),
        # --- Benefits
        Question(
            id="benefits_items",
            path=Keys.BENEFITS_ITEMS,
            step="benefits",
            input_type="list",
            required=True,
            label_de="Benefits & Angebote*",
            label_en="Benefits & perks*",
        ),
        # --- Recruiting Process
        Question(
            id="process_stages",
            path=Keys.PROCESS_STAGES,
            step="process",
            input_type="list",
            label_de="Interview-Stufen",
            label_en="Interview stages",
        ),
        Question(
            id="process_timeline",
            path=Keys.PROCESS_TIMELINE,
            step="process",
            input_type="text",
            label_de="Voraussichtlicher Prozessablauf",
            label_en="Expected timeline",
            advanced=True,
        ),
        Question(
            id="process_instructions",
            path=Keys.PROCESS_INSTRUCTIONS,
            step="process",
            input_type="textarea",
            label_de="Hinweise zur Bewerbung",
            label_en="Application instructions",
            advanced=True,
        ),
        Question(
            id="process_contact",
            path=Keys.PROCESS_CONTACT,
            step="process",
            input_type="email",
            label_de="Kontakt-E-Mail für Bewerbung",
            label_en="Contact email for application",
            help_de="Falls unterschiedlich von obiger Kontaktperson.",
            help_en="If different from the contact person above.",
            advanced=True,
        ),
    ]

def select_questions_for_step(profile: dict[str, Any], step: str) -> tuple[list[Question], list[Question]]:
    """Return (primary, advanced) question lists for a given step."""
    qs = [q for q in question_bank() if q.step == step and (not q.show_if or q.show_if(profile))]
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
            labels.append(q.label_de if profile.get("meta", {}).get("ui_language") == LANG_DE else q.label_en)
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
