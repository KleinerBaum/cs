# fields.py - Define schema field constants and their keys
# --- Company
COMPANY_NAME = "company.name"  # (Pflicht)
COMPANY_WEBSITE = "company.website"
COMPANY_INDUSTRY = "company.industry"
COMPANY_SIZE = "company.size"
COMPANY_HQ = "company.hq_location"
COMPANY_DESC = "company.description"
COMPANY_CONTACT_NAME = "company.contact_name"
COMPANY_CONTACT_EMAIL = "company.contact_email"  # (Pflicht)

# --- Position / Team
POSITION_TITLE = "position.job_title"  # (Pflicht)
POSITION_FAMILY = "position.job_family"
POSITION_SENIORITY = "position.seniority_level"  # (Pflicht)
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
LOCATION_CITY = "location.primary_city"  # (Pflicht)
LOCATION_REMOTE_SCOPE = "location.remote_scope"
LOCATION_TZ = "location.timezone_requirements"
LOCATION_TRAVEL_REQUIRED = "location.travel_required"
LOCATION_TRAVEL_PCT = "location.travel_percentage"

EMPLOYMENT_TYPE = "employment.employment_type"  # (Pflicht)
EMPLOYMENT_CONTRACT = "employment.contract_type"  # (Pflicht)
EMPLOYMENT_START = "employment.start_date"  # (Pflicht)
EMPLOYMENT_VISA = "employment.visa_sponsorship"

# --- Compensation / Benefits
SALARY_PROVIDED = "compensation.salary_provided"
SALARY_MIN = "compensation.salary_min"
SALARY_MAX = "compensation.salary_max"
SALARY_CURRENCY = "compensation.currency"
SALARY_PERIOD = "compensation.period"
BENEFITS_ITEMS = "benefits.items"  # (Pflicht)

# --- Responsibilities / Requirements
RESPONSIBILITIES = "responsibilities.items"  # (Pflicht)
HARD_REQ = "requirements.hard_skills_required"  # (Pflicht)
HARD_OPT = "requirements.hard_skills_optional"
SOFT_REQ = "requirements.soft_skills_required"  # (Pflicht)
LANG_REQ = "requirements.languages_required"  # (Pflicht)
TOOLS = "requirements.tools_and_technologies"  # (Pflicht)
MUST_NOT = "requirements.must_not_haves"

# --- Recruiting process
PROCESS_STAGES = "recruiting_process.interview_stages"
PROCESS_INSTRUCTIONS = "recruiting_process.application_instructions"
PROCESS_CONTACT = "recruiting_process.contact_email"
PROCESS_TIMELINE = "recruiting_process.timeline"
