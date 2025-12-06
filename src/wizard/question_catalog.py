# src/wizard/question_catalog.py
from __future__ import annotations

from cogstaff.constants.profile_paths import P
from cogstaff.schema.profile_document import NeedAnalysisProfileDocument
from cogstaff.wizard.question_engine import I18nText, NeedEval, QuestionSpec, evaluate_paths
from cogstaff.wizard.steps import StepId


def wp(doc: NeedAnalysisProfileDocument) -> str:
    # work_policy is an Enum in the profile; it serializes to ".value"
    val = doc.profile.location.work_policy
    return getattr(val, "value", str(val))


def show_city(doc: NeedAnalysisProfileDocument) -> bool:
    return wp(doc) != "remote"


def show_remote_related(doc: NeedAnalysisProfileDocument) -> bool:
    return wp(doc) in ("remote", "hybrid", "flexible")


def show_travel_pct(doc: NeedAnalysisProfileDocument) -> bool:
    return bool(doc.profile.location.travel_required)


def show_salary_fields(doc: NeedAnalysisProfileDocument) -> bool:
    return bool(doc.profile.compensation.salary_provided)


def ask_salary_provided(doc: NeedAnalysisProfileDocument) -> NeedEval:
    # tri-state: unknown(None) => ask
    return evaluate_paths(doc, (P.SALARY_PROVIDED.value,), min_confidence=0.7)


CATALOG: list[QuestionSpec] = [
    # ---------------- COMPANY ----------------
    QuestionSpec(
        id="company.name",
        step=StepId.COMPANY,
        paths=(P.COMPANY_NAME.value,),
        label=I18nText("Unternehmensname", "Company name"),
        help=I18nText("Wie heißt das Unternehmen/der Arbeitgeber?", "What is the employer/company name?"),
        widget="text",
        required=True,
        level="core",
    ),
    QuestionSpec(
        id="company.website",
        step=StepId.COMPANY,
        paths=(P.COMPANY_WEBSITE.value,),
        label=I18nText("Website", "Website"),
        widget="text",
        required=False,
        level="standard",
    ),
    QuestionSpec(
        id="company.industry",
        step=StepId.COMPANY,
        paths=(P.COMPANY_INDUSTRY.value,),
        label=I18nText("Branche", "Industry"),
        widget="text",
        level="standard",
    ),
    QuestionSpec(
        id="company.size",
        step=StepId.COMPANY,
        paths=(P.COMPANY_SIZE.value,),
        label=I18nText("Unternehmensgröße", "Company size"),
        widget="select",
        options=("1-10", "11-50", "51-200", "201-1000", "1000+", "unknown"),
        level="detail",
    ),
    QuestionSpec(
        id="company.hq",
        step=StepId.COMPANY,
        paths=(P.COMPANY_HQ.value,),
        label=I18nText("Hauptsitz", "HQ location"),
        widget="text",
        level="detail",
    ),

    # ---------------- TEAM ----------------
    QuestionSpec(
        id="team.department",
        step=StepId.TEAM,
        paths=(P.TEAM_DEPT.value,),
        label=I18nText("Abteilung", "Department"),
        widget="text",
        level="core",
    ),
    QuestionSpec(
        id="team.name",
        step=StepId.TEAM,
        paths=(P.TEAM_NAME.value,),
        label=I18nText("Teamname", "Team name"),
        widget="text",
        level="standard",
    ),
    QuestionSpec(
        id="team.reporting_line",
        step=StepId.TEAM,
        paths=(P.TEAM_REPORTING_LINE.value,),
        label=I18nText("Einordnung/Reporting Line", "Reporting line"),
        widget="textarea",
        level="detail",
    ),
    QuestionSpec(
        id="pos.people_mgmt",
        step=StepId.TEAM,
        paths=(P.POSITION_PEOPLE_MGMT.value,),
        label=I18nText("Führungsverantwortung?", "People management?"),
        widget="tri_bool",
        required=True,
        level="core",
    ),
    QuestionSpec(
        id="pos.direct_reports",
        step=StepId.TEAM,
        paths=(P.POSITION_DIRECT_REPORTS.value,),
        label=I18nText("Anzahl direkter Reports", "Number of direct reports"),
        widget="number",
        required=False,
        level="standard",
        show_if=lambda doc: bool(doc.profile.position.people_management),
    ),

    # ---------------- CONDITIONS (Vacancy frame) ----------------
    QuestionSpec(
        id="position.title",
        step=StepId.CONDITIONS,
        paths=(P.POSITION_TITLE.value,),
        label=I18nText("Jobtitel", "Job title"),
        widget="text",
        required=True,
        level="core",
    ),
    QuestionSpec(
        id="location.work_policy",
        step=StepId.CONDITIONS,
        paths=(P.LOCATION_WORK_POLICY.value,),
        label=I18nText("Arbeitsmodell", "Work policy"),
        help=I18nText("Onsite / Hybrid / Remote / Flexibel", "Onsite / Hybrid / Remote / Flexible"),
        widget="select",
        required=True,
        level="core",
        options=("onsite", "hybrid", "remote", "flexible", "unknown"),
    ),
    QuestionSpec(
        id="location.city",
        step=StepId.CONDITIONS,
        paths=(P.LOCATION_CITY.value,),
        label=I18nText("Einsatzort (Stadt)", "Primary city"),
        widget="text",
        required=True,
        level="core",
        show_if=show_city,
    ),
    QuestionSpec(
        id="location.remote_scope",
        step=StepId.CONDITIONS,
        paths=(P.LOCATION_REMOTE_SCOPE.value,),
        label=I18nText("Remote-Geltungsbereich", "Remote scope"),
        help=I18nText("z.B. Deutschland / EU / weltweit", "e.g. Germany only / EU / worldwide"),
        widget="text",
        level="standard",
        show_if=show_remote_related,
    ),
    QuestionSpec(
        id="location.timezone",
        step=StepId.CONDITIONS,
        paths=(P.LOCATION_TZ.value,),
        label=I18nText("Zeitzonen-Anforderung", "Timezone requirements"),
        help=I18nText("z.B. CET ±2h", "e.g. CET ±2h"),
        widget="text",
        level="detail",
        show_if=show_remote_related,
    ),
    QuestionSpec(
        id="employment.type",
        step=StepId.CONDITIONS,
        paths=(P.EMPLOYMENT_TYPE.value,),
        label=I18nText("Beschäftigungsart", "Employment type"),
        widget="select",
        options=("permanent", "temporary", "contractor", "freelance", "internship", "apprenticeship", "other", "unknown"),
        level="standard",
    ),
    QuestionSpec(
        id="employment.contract",
        step=StepId.CONDITIONS,
        paths=(P.EMPLOYMENT_CONTRACT.value,),
        label=I18nText("Arbeitszeitmodell", "Contract type"),
        widget="select",
        options=("full_time", "part_time", "mini_job", "other", "unknown"),
        level="standard",
    ),
    QuestionSpec(
        id="travel.required",
        step=StepId.CONDITIONS,
        paths=(P.LOCATION_TRAVEL_REQUIRED.value,),
        label=I18nText("Reisebereitschaft erforderlich?", "Travel required?"),
        widget="tri_bool",
        level="detail",
    ),
    QuestionSpec(
        id="travel.pct",
        step=StepId.CONDITIONS,
        paths=(P.LOCATION_TRAVEL_PCT.value,),
        label=I18nText("Reiseanteil (%)", "Travel percentage (%)"),
        widget="number",
        level="detail",
        show_if=show_travel_pct,
    ),
    QuestionSpec(
        id="salary.provided",
        step=StepId.CONDITIONS,
        paths=(P.SALARY_PROVIDED.value,),
        label=I18nText("Gehaltsspanne verfügbar?", "Salary range available?"),
        widget="tri_bool",
        level="standard",
        ask_override=ask_salary_provided,
    ),
    QuestionSpec(
        id="salary.min",
        step=StepId.CONDITIONS,
        paths=(P.SALARY_MIN.value,),
        label=I18nText("Gehalt Min", "Salary min"),
        widget="number",
        level="detail",
        show_if=show_salary_fields,
    ),
    QuestionSpec(
        id="salary.max",
        step=StepId.CONDITIONS,
        paths=(P.SALARY_MAX.value,),
        label=I18nText("Gehalt Max", "Salary max"),
        widget="number",
        level="detail",
        show_if=show_salary_fields,
    ),
    QuestionSpec(
        id="salary.currency",
        step=StepId.CONDITIONS,
        paths=(P.SALARY_CURRENCY.value,),
        label=I18nText("Währung", "Currency"),
        widget="select",
        options=("EUR", "USD", "CHF", "GBP", "other"),
        level="detail",
        show_if=show_salary_fields,
    ),
    QuestionSpec(
        id="salary.period",
        step=StepId.CONDITIONS,
        paths=(P.SALARY_PERIOD.value,),
        label=I18nText("Zeitraum", "Period"),
        widget="select",
        options=("year", "month", "hour", "day", "project", "unknown"),
        level="detail",
        show_if=show_salary_fields,
    ),

    # ---------------- TASKS ----------------
    QuestionSpec(
        id="position.summary",
        step=StepId.TASKS,
        paths=(P.POSITION_SUMMARY.value,),
        label=I18nText("Kurzbeschreibung der Rolle", "Role summary"),
        widget="textarea",
        level="standard",
    ),
    QuestionSpec(
        id="responsibilities",
        step=StepId.TASKS,
        paths=(P.RESPONSIBILITIES.value,),
        label=I18nText("Top Aufgaben (Bulletpoints)", "Key responsibilities (bullets)"),
        help=I18nText("Eine Aufgabe pro Zeile", "One bullet per line"),
        widget="list_text",
        required=True,
        level="core",
    ),

    # ---------------- SKILLS ----------------
    QuestionSpec(
        id="skills.hard_req",
        step=StepId.SKILLS,
        paths=(P.HARD_REQ.value,),
        label=I18nText("Muss-Hard-Skills", "Must-have hard skills"),
        widget="list_text",
        required=True,
        level="core",
    ),
    QuestionSpec(
        id="skills.soft_req",
        step=StepId.SKILLS,
        paths=(P.SOFT_REQ.value,),
        label=I18nText("Muss-Soft-Skills", "Must-have soft skills"),
        widget="list_text",
        level="standard",
    ),
    QuestionSpec(
        id="skills.tools",
        step=StepId.SKILLS,
        paths=(P.TOOLS.value,),
        label=I18nText("Tools/Technologien/Methoden", "Tools/technologies/methods"),
        widget="list_text",
        level="standard",
    ),
    QuestionSpec(
        id="skills.lang_req",
        step=StepId.SKILLS,
        paths=(P.LANG_REQ.value,),
        label=I18nText("Sprachen (erforderlich)", "Languages (required)"),
        widget="list_text",
        level="detail",
    ),
    QuestionSpec(
        id="skills.must_not",
        step=StepId.SKILLS,
        paths=(P.MUST_NOT.value,),
        label=I18nText("Ausschlusskriterien (Dealbreaker)", "Dealbreakers (must-not-haves)"),
        widget="list_text",
        level="detail",
    ),

    # ---------------- BENEFITS ----------------
    QuestionSpec(
        id="benefits.items",
        step=StepId.BENEFITS,
        paths=(P.BENEFITS_ITEMS.value,),
        label=I18nText("Benefits", "Benefits"),
        widget="list_text",
        level="standard",
    ),

    # ---------------- PROCESS ----------------
    QuestionSpec(
        id="process.stages",
        step=StepId.PROCESS,
        paths=(P.PROCESS_STAGES.value,),
        label=I18nText("Anzahl Interview-Stufen", "Number of interview stages"),
        widget="number",
        level="standard",
    ),
    QuestionSpec(
        id="process.instructions",
        step=StepId.PROCESS,
        paths=(P.PROCESS_INSTRUCTIONS.value,),
        label=I18nText("Bewerbungshinweise", "Application instructions"),
        widget="textarea",
        level="standard",
    ),
    QuestionSpec(
        id="process.timeline",
        step=StepId.PROCESS,
        paths=(P.PROCESS_TIMELINE.value,),
        label=I18nText("Zeitplan/Startziel", "Timeline/target start"),
        widget="text",
        level="detail",
    ),
    QuestionSpec(
        id="process.contact",
        step=StepId.PROCESS,
        paths=(P.PROCESS_CONTACT.value,),
        label=I18nText("Kontakt-E-Mail im Prozess", "Process contact email"),
        widget="text",
        level="detail",
    ),
]
