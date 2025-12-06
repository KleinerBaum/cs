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
    input_type: str  # text|textarea|email|bool|number|date|select|multiselect|list
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


def _is_remote(profile: dict[str, Any]) -> bool:
    return get_value(profile, Keys.LOCATION_WORK_POLICY) == "remote"


def _travel_required(profile: dict[str, Any]) -> bool:
    return bool(get_value(profile, Keys.LOCATION_TRAVEL_REQUIRED))


def _salary_provided(profile: dict[str, Any]) -> bool:
    return bool(get_value(profile, Keys.SALARY_PROVIDED))


def _people_mgmt(profile: dict[str, Any]) -> bool:
    return bool(get_value(profile, Keys.POSITION_PEOPLE_MGMT))


def question_bank() -> list[Question]:
    """Single source of truth for all questions."""
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
            label_de="Jobtitel (EN)",
            label_en="Job title (EN)",
            help_de="Optional, aber hilfreich für internationale Anzeigen.",
            help_en="Optional, but useful for English postings.",
            advanced=True,
        ),
        Question(
            id="position_family",
            path=Keys.POSITION_FAMILY,
            step="team",
            input_type="text",
            label_de="Jobfamilie",
            label_en="Job family",
            advanced=True,
        ),
        Question(
            id="position_seniority",
            path=Keys.POSITION_SENIORITY,
            step="team",
            input_type="select",
            required=True,
            options_group="seniority",
            options_values=SENIORITY_VALUES,
            label_de="Senioritätslevel*",
            label_en="Seniority level*",
        ),
        Question(
            id="position_summary",
            path=Keys.POSITION_SUMMARY,
            step="team",
            input_type="textarea",
            label_de="Rollen-Übersicht",
            label_en="Role summary",
        ),
        Question(
            id="position_reports_to",
            path=Keys.POSITION_REPORTS_TO_TITLE,
            step="team",
            input_type="text",
            label_de="Reports to (Titel)",
            label_en="Reports to (title)",
            advanced=True,
        ),
        Question(
            id="position_people_mgmt",
            path=Keys.POSITION_PEOPLE_MGMT,
            step="team",
            input_type="bool",
            label_de="Disziplinarische Führung?",
            label_en="People management?",
            advanced=True,
        ),
        Question(
            id="position_direct_reports",
            path=Keys.POSITION_DIRECT_REPORTS,
            step="team",
            input_type="number",
            label_de="Direkte Reports (#)",
            label_en="Direct reports (#)",
            advanced=True,
            show_if=_people_mgmt,
        ),
        # --- Framework: location & employment
        Question(
            id="work_policy",
            path=Keys.LOCATION_WORK_POLICY,
            step="framework",
            input_type="select",
            options_group="work_policy",
            options_values=WORK_POLICY_VALUES,
            label_de="Arbeitsmodell",
            label_en="Work policy",
        ),
        Question(
            id="location_city",
            path=Keys.LOCATION_CITY,
            step="framework",
            input_type="text",
            required=True,
            label_de="Primärer Standort / Stadt*",
            label_en="Primary city / location*",
            help_de="Auch bei Remote: bevorzugter Hub / Hauptstandort.",
            help_en="For remote: preferred hub / primary location.",
        ),
        Question(
            id="remote_scope",
            path=Keys.LOCATION_REMOTE_SCOPE,
            step="framework",
            input_type="text",
            label_de="Remote Scope",
            label_en="Remote scope",
            help_de="z.B. Deutschland, EU, global",
            help_en="e.g. Germany, EU, global",
            advanced=True,
            show_if=_is_remote,
        ),
        Question(
            id="timezone_req",
            path=Keys.LOCATION_TZ,
            step="framework",
            input_type="text",
            label_de="Zeitzonen-Anforderungen",
            label_en="Timezone requirements",
            help_de="z.B. 4h Overlap mit CET",
            help_en="e.g. 4h overlap with CET",
            advanced=True,
            show_if=_is_remote,
        ),
        Question(
            id="travel_required",
            path=Keys.LOCATION_TRAVEL_REQUIRED,
            step="framework",
            input_type="bool",
            label_de="Reisen erforderlich?",
            label_en="Travel required?",
            advanced=True,
        ),
        Question(
            id="travel_pct",
            path=Keys.LOCATION_TRAVEL_PCT,
            step="framework",
            input_type="number",
            label_de="Reiseanteil (%)",
            label_en="Travel percentage (%)",
            advanced=True,
            show_if=_travel_required,
        ),
        Question(
            id="employment_type",
            path=Keys.EMPLOYMENT_TYPE,
            step="framework",
            input_type="select",
            required=True,
            options_group="employment_type",
            options_values=EMPLOYMENT_TYPE_VALUES,
            label_de="Anstellungsart*",
            label_en="Employment type*",
        ),
        Question(
            id="contract_type",
            path=Keys.EMPLOYMENT_CONTRACT,
            step="framework",
            input_type="select",
            required=True,
            options_group="contract_type",
            options_values=CONTRACT_TYPE_VALUES,
            label_de="Vertragsart*",
            label_en="Contract type*",
        ),
        Question(
            id="start_date",
            path=Keys.EMPLOYMENT_START,
            step="framework",
            input_type="date",
            required=True,
            label_de="Startdatum*",
            label_en="Start date*",
        ),
        Question(
            id="visa",
            path=Keys.EMPLOYMENT_VISA,
            step="framework",
            input_type="bool",
            label_de="Visa Sponsorship möglich?",
            label_en="Visa sponsorship available?",
            advanced=True,
        ),
        # --- Benefits / Compensation
        Question(
            id="salary_provided",
            path=Keys.SALARY_PROVIDED,
            step="benefits",
            input_type="bool",
            label_de="Gehaltsspanne angeben?",
            label_en="Provide salary range?",
            advanced=True,
        ),
        Question(
            id="salary_min",
            path=Keys.SALARY_MIN,
            step="benefits",
            input_type="number",
            label_de="Gehalt min",
            label_en="Salary min",
            advanced=True,
            show_if=_salary_provided,
        ),
        Question(
            id="salary_max",
            path=Keys.SALARY_MAX,
            step="benefits",
            input_type="number",
            label_de="Gehalt max",
            label_en="Salary max",
            advanced=True,
            show_if=_salary_provided,
        ),
        Question(
            id="salary_currency",
            path=Keys.SALARY_CURRENCY,
            step="benefits",
            input_type="text",
            label_de="Währung",
            label_en="Currency",
            advanced=True,
            show_if=_salary_provided,
        ),
        Question(
            id="salary_period",
            path=Keys.SALARY_PERIOD,
            step="benefits",
            input_type="select",
            options_group="salary_period",
            options_values=SALARY_PERIOD_VALUES,
            label_de="Zeitraum",
            label_en="Period",
            advanced=True,
            show_if=_salary_provided,
        ),
        Question(
            id="benefits_items",
            path=Keys.BENEFITS_ITEMS,
            step="benefits",
            input_type="list",
            required=True,
            label_de="Benefits* (je Zeile 1 Punkt)",
            label_en="Benefits* (one per line)",
        ),
        # --- Responsibilities
        Question(
            id="responsibilities_items",
            path=Keys.RESPONSIBILITIES,
            step="tasks",
            input_type="list",
            required=True,
            label_de="Aufgaben* (je Zeile 1 Punkt)",
            label_en="Responsibilities* (one per line)",
        ),
        # --- Requirements
        Question(
            id="hard_req",
            path=Keys.HARD_REQ,
            step="skills",
            input_type="list",
            required=True,
            label_de="Hard Skills* (must-have)",
            label_en="Hard skills* (must-have)",
        ),
        Question(
            id="hard_req_en",
            path=Keys.HARD_REQ_EN,
            step="skills",
            input_type="list",
            label_de="Hard Skills (EN)",
            label_en="Hard skills (EN)",
            advanced=True,
        ),
        Question(
            id="hard_opt",
            path=Keys.HARD_OPT,
            step="skills",
            input_type="list",
            label_de="Hard Skills (optional/nice-to-have)",
            label_en="Hard skills (optional/nice-to-have)",
            advanced=True,
        ),
        Question(
            id="soft_req",
            path=Keys.SOFT_REQ,
            step="skills",
            input_type="list",
            required=True,
            label_de="Soft Skills*",
            label_en="Soft skills*",
        ),
        Question(
            id="soft_req_en",
            path=Keys.SOFT_REQ_EN,
            step="skills",
            input_type="list",
            label_de="Soft Skills (EN)",
            label_en="Soft skills (EN)",
            advanced=True,
        ),
        Question(
            id="lang_req",
            path=Keys.LANG_REQ,
            step="skills",
            input_type="list",
            required=True,
            label_de="Sprachen*",
            label_en="Languages*",
            help_de="z.B. Deutsch C1, Englisch B2",
            help_en="e.g. German C1, English B2",
        ),
        Question(
            id="tools",
            path=Keys.TOOLS,
            step="skills",
            input_type="list",
            required=True,
            label_de="Tools/Technologien*",
            label_en="Tools/technologies*",
        ),
        Question(
            id="tools_en",
            path=Keys.TOOLS_EN,
            step="skills",
            input_type="list",
            label_de="Tools/Technologien (EN)",
            label_en="Tools/technologies (EN)",
            advanced=True,
        ),
        Question(
            id="must_not",
            path=Keys.MUST_NOT,
            step="skills",
            input_type="list",
            label_de="Must-not-haves",
            label_en="Must-not-haves",
            advanced=True,
        ),
        # --- Recruiting process
        Question(
            id="process_stages",
            path=Keys.PROCESS_STAGES,
            step="process",
            input_type="list",
            label_de="Interview-Stages",
            label_en="Interview stages",
            help_de="z.B. HR Call, Fachgespräch, Case, Final",
            help_en="e.g. HR call, technical interview, case, final",
            advanced=True,
        ),
        Question(
            id="process_timeline",
            path=Keys.PROCESS_TIMELINE,
            step="process",
            input_type="text",
            label_de="Timeline",
            label_en="Timeline",
            advanced=True,
        ),
        Question(
            id="process_instructions",
            path=Keys.PROCESS_INSTRUCTIONS,
            step="process",
            input_type="textarea",
            label_de="Bewerbungsanweisungen",
            label_en="Application instructions",
            advanced=True,
        ),
        Question(
            id="process_contact",
            path=Keys.PROCESS_CONTACT,
            step="process",
            input_type="email",
            label_de="Recruiting Kontakt E-Mail",
            label_en="Recruiting contact email",
            advanced=True,
        ),
    ]


def question_label(q: Question, lang: str) -> str:
    return q.label_de if lang == LANG_DE else q.label_en


def question_help(q: Question, lang: str) -> str:
    return q.help_de if lang == LANG_DE else q.help_en


def _is_low_conf(profile: dict[str, Any], path: str) -> bool:
    rec = get_record(profile, path)
    if not rec:
        return False
    conf = rec.get("confidence")
    prov = rec.get("provenance")
    if prov == "user":
        return False
    return conf is not None and conf < LOW_CONFIDENCE_THRESHOLD


def select_questions_for_step(
    profile: dict[str, Any], step: str
) -> tuple[list[Question], list[Question]]:
    """Return (primary, more_details) questions for a step."""
    qs = [q for q in question_bank() if q.step == step]

    filtered: list[Question] = []
    for q in qs:
        if q.show_if is None:
            filtered.append(q)
        else:
            try:
                if q.show_if(profile):
                    filtered.append(q)
            except Exception:
                filtered.append(q)

    def score(q: Question) -> tuple[int, int, str]:
        missing = is_missing(profile, q.path)
        low_conf = _is_low_conf(profile, q.path)
        if q.required and missing:
            primary_rank = 0
        elif q.required and low_conf:
            primary_rank = 1
        elif missing:
            primary_rank = 2
        elif low_conf:
            primary_rank = 3
        else:
            primary_rank = 4
        adv_rank = 1 if q.advanced else 0
        return (primary_rank, adv_rank, q.id)

    filtered.sort(key=score)

    primary: list[Question] = []
    more: list[Question] = []
    for q in filtered:
        if len(primary) < MAX_PRIMARY_QUESTIONS_PER_STEP and not q.advanced:
            primary.append(q)
        else:
            more.append(q)

    while len(primary) < min(MAX_PRIMARY_QUESTIONS_PER_STEP, len(filtered)) and more:
        primary.append(more.pop(0))

    return primary, more


def required_fields_for_step(step: str) -> set[str]:
    mapping = {
        "company": {Keys.COMPANY_NAME, Keys.COMPANY_CONTACT_EMAIL},
        "team": {Keys.POSITION_TITLE, Keys.POSITION_SENIORITY},
        "framework": {
            Keys.LOCATION_CITY,
            Keys.EMPLOYMENT_TYPE,
            Keys.EMPLOYMENT_CONTRACT,
            Keys.EMPLOYMENT_START,
        },
        "benefits": {Keys.BENEFITS_ITEMS},
        "tasks": {Keys.RESPONSIBILITIES},
        "skills": {Keys.HARD_REQ, Keys.SOFT_REQ, Keys.LANG_REQ, Keys.TOOLS},
        "process": set(),
        "intake": set(),
        "review": set(),
    }
    return mapping.get(step, set())


def missing_required_for_step(profile: dict[str, Any], step: str) -> list[str]:
    reqs = required_fields_for_step(step)
    return [p for p in sorted(reqs) if is_missing(profile, p)]


def iter_missing_optional(
    profile: dict[str, Any], candidates: Iterable[Question]
) -> list[str]:
    out: list[str] = []
    for q in candidates:
        if q.path in REQUIRED_FIELDS:
            continue
        if is_missing(profile, q.path) or _is_low_conf(profile, q.path):
            out.append(q.path)
    seen = set()
    uniq: list[str] = []
    for p in out:
        if p in seen:
            continue
        seen.add(p)
        uniq.append(p)
    return uniq
