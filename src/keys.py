from __future__ import annotations

# Central place for ALL dot-path keys.
# Any UI label, prompt, rule, or export must reference these constants.

class Keys:
    # --- Company
    COMPANY_NAME = "company.name"  # required
    COMPANY_WEBSITE = "company.website"
    COMPANY_INDUSTRY = "company.industry"
    COMPANY_SIZE = "company.size"
    COMPANY_HQ = "company.hq_location"
    COMPANY_DESC = "company.description"
    COMPANY_CONTACT_NAME = "company.contact_name"
    COMPANY_CONTACT_EMAIL = "company.contact_email"  # required

    # --- Position / Team
    POSITION_TITLE = "position.job_title"  # required
    POSITION_TITLE_EN = "position.job_title_en"  # optional (English version)
    POSITION_FAMILY = "position.job_family"
    POSITION_SENIORITY = "position.seniority_level"  # required
    POSITION_SUMMARY = "position.role_summary"
    POSITION_REPORTS_TO_TITLE = "position.reports_to_title"
    POSITION_PEOPLE_MGMT = "position.people_management"
    POSITION_DIRECT_REPORTS = "position.direct_reports"

    TEAM_DEPT = "team.department_name"
    TEAM_NAME = "team.team_name"
    TEAM_REPORTING_LINE = "team.reporting_line"
    TEAM_HEADCOUNT_CURRENT = "team.headcount_current"
    TEAM_HEADCOUNT_TARGET = "team.headcount_target"
    TEAM_TOOLS = "team.collaboration_tools"

    # --- Location / Employment
    LOCATION_WORK_POLICY = "location.work_policy"
    LOCATION_CITY = "location.primary_city"  # required
    LOCATION_REMOTE_SCOPE = "location.remote_scope"
    LOCATION_TZ = "location.timezone_requirements"
    LOCATION_TRAVEL_REQUIRED = "location.travel_required"
    LOCATION_TRAVEL_PCT = "location.travel_percentage"

    EMPLOYMENT_TYPE = "employment.employment_type"  # required
    EMPLOYMENT_CONTRACT = "employment.contract_type"  # required
    EMPLOYMENT_START = "employment.start_date"  # required
    EMPLOYMENT_VISA = "employment.visa_sponsorship"
    EMPLOYMENT_SCHEDULE = "employment.work_schedule"

    # --- Compensation / Benefits
    SALARY_PROVIDED = "compensation.salary_provided"
    SALARY_MIN = "compensation.salary_min"
    SALARY_MAX = "compensation.salary_max"
    SALARY_CURRENCY = "compensation.currency"
    SALARY_PERIOD = "compensation.period"
    BENEFITS_ITEMS = "benefits.items"  # required
    COMPENSATION_VARIABLE = "compensation.variable_pct"
    COMPENSATION_RELOCATION = "compensation.relocation"

    # --- Responsibilities / Requirements
    RESPONSIBILITIES = "responsibilities.items"  # required
    HARD_REQ = "requirements.hard_skills_required"  # required
    HARD_REQ_EN = "requirements.hard_skills_required_en"  # optional (English version)
    HARD_OPT = "requirements.hard_skills_optional"
    SOFT_REQ = "requirements.soft_skills_required"  # required
    SOFT_REQ_EN = "requirements.soft_skills_required_en"  # optional (English version)
    LANG_REQ = "requirements.languages_required"  # required
    TOOLS = "requirements.tools_and_technologies"  # required
    TOOLS_EN = "requirements.tools_and_technologies_en"  # optional (English version)
    MUST_NOT = "requirements.must_not_haves"

    # --- Recruiting process
    PROCESS_STAGES = "recruiting_process.interview_stages"
    PROCESS_INSTRUCTIONS = "recruiting_process.application_instructions"
    PROCESS_CONTACT = "recruiting_process.contact_email"
    PROCESS_TIMELINE = "recruiting_process.timeline"

    # --- Optional: ESCO enrichment
    ESCO_OCCUPATION_URI = "position.esco_occupation_uri"
    ESCO_OCCUPATION_LABEL = "position.esco_occupation_label"
    ESCO_SUGGESTED_SKILLS = "position.esco_suggested_skills"


# Required fields (Pflichtfelder)
REQUIRED_FIELDS: set[str] = {
    Keys.COMPANY_NAME,
    Keys.POSITION_TITLE,
    Keys.POSITION_SENIORITY,
    Keys.TEAM_DEPT,
    Keys.LOCATION_CITY,
    Keys.EMPLOYMENT_TYPE,
    Keys.EMPLOYMENT_CONTRACT,
    Keys.EMPLOYMENT_START,
    Keys.RESPONSIBILITIES,
    Keys.HARD_REQ,
    Keys.SALARY_CURRENCY,
    Keys.SALARY_MIN,
    Keys.SALARY_MAX,
}

# All known fields (including optional enrichment)
ALL_FIELDS: set[str] = {
    value for name, value in Keys.__dict__.items()
    if name.isupper() and isinstance(value, str)
}

# Enumerations (stored as stable machine values in the profile)
WORK_POLICY_VALUES = ("onsite", "hybrid", "remote")
EMPLOYMENT_TYPE_VALUES = ("full_time", "part_time", "contractor", "intern")
CONTRACT_TYPE_VALUES = ("permanent", "fixed_term")
SENIORITY_VALUES = ("junior", "mid", "senior", "lead", "head", "c_level")
SALARY_PERIOD_VALUES = ("year", "month", "hour")
COMMON_CURRENCIES = ("EUR", "USD", "GBP", "CHF")
