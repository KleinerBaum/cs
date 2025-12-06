# src/schema/profile_document.py
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, HttpUrl


# =========================
# Enums / shared primitives
# =========================


class LanguageCode(str, Enum):
    """UI / output language selection."""

    DE = "de"
    EN = "en"


class DetectedLanguage(str, Enum):
    """Language detected from the imported job ad."""

    DE = "de"
    EN = "en"
    MIXED = "mixed"
    UNKNOWN = "unknown"


class FieldSource(str, Enum):
    """Where a specific field value came from."""

    EXTRACTED = "extracted"  # from URL/file parsing + extraction
    USER = "user"  # human confirmed / edited
    AI_SUGGESTION = "ai_suggestion"  # AI enrichment (not yet confirmed)


class WorkPolicy(str, Enum):
    ONSITE = "onsite"
    HYBRID = "hybrid"
    REMOTE = "remote"
    FLEXIBLE = "flexible"
    UNKNOWN = "unknown"


class EmploymentType(str, Enum):
    PERMANENT = "permanent"
    TEMPORARY = "temporary"
    CONTRACTOR = "contractor"
    FREELANCE = "freelance"
    INTERNSHIP = "internship"
    APPRENTICESHIP = "apprenticeship"
    WORKING_STUDENT = "working_student"
    OTHER = "other"
    UNKNOWN = "unknown"


class ContractType(str, Enum):
    FULL_TIME = "full_time"
    PART_TIME = "part_time"
    MINI_JOB = "mini_job"
    OTHER = "other"
    UNKNOWN = "unknown"


class SalaryPeriod(str, Enum):
    YEAR = "year"
    MONTH = "month"
    WEEK = "week"
    DAY = "day"
    HOUR = "hour"
    PROJECT = "project"
    OTHER = "other"
    UNKNOWN = "unknown"


# =========================
# Provenance
# =========================


class FieldProvenance(BaseModel):
    """
    Metadata per profile field (keyed by canonical dot-path).

    This is the 'lever' for your dynamic question-engine:
      - missing value -> ask
      - low confidence -> ask/confirm
      - user-confirmed -> do not ask again
    """

    model_config = ConfigDict(extra="forbid")

    source: FieldSource
    confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)

    # Optional technical trace (“rules”, “llm:gpt-5.1”, “import:url”, …)
    extractor: Optional[str] = None

    # References into your extraction output (block ids, offsets, etc.)
    evidence: List[str] = Field(default_factory=list)

    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    notes: Optional[str] = None


# =========================
# Profile schema (industry-agnostic)
# =========================


class Company(BaseModel):
    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    name: Optional[str] = None
    legal_name: Optional[str] = None
    industry: Optional[str] = None
    sub_industry: Optional[str] = None
    description: Optional[str] = None

    website: Optional[str] = None
    hq_location: Optional[str] = None
    locations: List[str] = Field(default_factory=list)
    size: Optional[str] = None  # "1-10", "11-50", ...

    mission: Optional[str] = None
    values: List[str] = Field(default_factory=list)
    culture: Optional[str] = None

    contact_name: Optional[str] = None
    contact_email: Optional[EmailStr] = None
    contact_phone: Optional[str] = None

    # optional branding
    brand_name: Optional[str] = None
    claim: Optional[str] = None
    brand_keywords: List[str] = Field(default_factory=list)
    brand_color: Optional[str] = None  # "#0055FF"
    logo_url: Optional[HttpUrl] = None


class TeamContext(BaseModel):
    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    department_name: Optional[str] = None
    department_function: Optional[str] = None
    department_lead_name: Optional[str] = None

    team_name: Optional[str] = None
    team_mission: Optional[str] = None
    reporting_line: Optional[str] = None

    headcount_current: Optional[int] = Field(default=None, ge=0)
    headcount_target: Optional[int] = Field(default=None, ge=0)

    collaboration_tools: List[str] = Field(default_factory=list)
    team_locations: List[str] = Field(default_factory=list)


class Position(BaseModel):
    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    job_title: Optional[str] = None
    job_family: Optional[str] = None  # Sales/HR/Engineering/Manufacturing/...
    seniority_level: Optional[str] = None  # Junior/Senior/Lead/Head/...
    employment_level: Optional[str] = None  # IC/Manager/Director/Exec (free text)

    reason_for_hire: Optional[str] = None  # growth, replacement, ...
    role_summary: Optional[str] = None

    key_objectives: List[str] = Field(default_factory=list)
    key_projects: List[str] = Field(default_factory=list)
    performance_indicators: List[str] = Field(default_factory=list)
    decision_authority: Optional[str] = None

    reports_to_title: Optional[str] = None
    reports_to_name: Optional[str] = None
    people_management: Optional[bool] = None
    direct_reports: Optional[int] = Field(default=None, ge=0)


class Location(BaseModel):
    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    primary_city: Optional[str] = None
    region: Optional[str] = None
    country: Optional[str] = None

    work_policy: WorkPolicy = WorkPolicy.UNKNOWN
    onsite_ratio: Optional[str] = None  # "3 days/week", "50%", ...

    remote_scope: Optional[str] = None  # "Germany only", "EU", "Worldwide"
    timezone_requirements: Optional[str] = None  # "CET ±2h"

    travel_required: Optional[bool] = None
    travel_percentage: Optional[int] = Field(default=None, ge=0, le=100)

    relocation_support: Optional[bool] = None
    relocation_details: Optional[str] = None


class Employment(BaseModel):
    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    employment_type: EmploymentType = EmploymentType.UNKNOWN
    contract_type: ContractType = ContractType.UNKNOWN

    start_date: Optional[str] = None
    contract_end_date: Optional[str] = None

    working_hours_per_week: Optional[int] = Field(default=None, ge=0, le=80)
    work_schedule: Optional[str] = None  # shift patterns, flex, ...
    shift_work: Optional[bool] = None
    weekend_work: Optional[bool] = None

    probation_period: Optional[str] = None
    overtime_expected: Optional[bool] = None
    union_or_tariff: Optional[str] = None

    visa_sponsorship: Optional[bool] = None
    work_permit_required: Optional[bool] = None
    security_clearance_required: Optional[bool] = None


class Compensation(BaseModel):
    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    salary_provided: Optional[bool] = None
    salary_min: Optional[float] = Field(default=None, ge=0)
    salary_max: Optional[float] = Field(default=None, ge=0)
    currency: Optional[str] = None  # "EUR", "USD"
    period: SalaryPeriod = SalaryPeriod.UNKNOWN

    variable_pay: Optional[bool] = None
    bonus_percentage: Optional[float] = Field(default=None, ge=0, le=100)
    commission_structure: Optional[str] = None
    equity_offered: Optional[bool] = None

    notes: Optional[str] = None


class Benefits(BaseModel):
    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    items: List[str] = Field(default_factory=list)
    notes: Optional[str] = None


class Responsibilities(BaseModel):
    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    items: List[str] = Field(default_factory=list)


class Requirements(BaseModel):
    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    education_level: Optional[str] = None
    degree_fields: List[str] = Field(default_factory=list)

    experience_years_min: Optional[int] = Field(default=None, ge=0, le=60)
    experience_years_preferred: Optional[int] = Field(default=None, ge=0, le=60)
    domain_experience: List[str] = Field(default_factory=list)

    hard_skills_required: List[str] = Field(default_factory=list)
    hard_skills_optional: List[str] = Field(default_factory=list)
    soft_skills_required: List[str] = Field(default_factory=list)
    soft_skills_optional: List[str] = Field(default_factory=list)
    tools_and_technologies: List[str] = Field(default_factory=list)

    languages_required: List[str] = Field(default_factory=list)
    languages_optional: List[str] = Field(default_factory=list)
    language_levels: Dict[str, str] = Field(default_factory=dict)  # {"English": "C1"}

    certifications: List[str] = Field(default_factory=list)
    licenses: List[str] = Field(default_factory=list)

    portfolio_required: Optional[bool] = None
    background_check_required: Optional[bool] = None
    reference_check_required: Optional[bool] = None
    assessments_required: Optional[bool] = None

    physical_requirements: Optional[str] = None  # lifting, standing, PPE
    must_not_haves: List[str] = Field(default_factory=list)  # dealbreakers


class Stakeholder(BaseModel):
    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    name: Optional[str] = None
    role: Optional[str] = None  # Hiring Manager, HR, Peer, ...
    email: Optional[EmailStr] = None
    primary: bool = False


class Phase(BaseModel):
    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    name: str
    interview_format: Optional[str] = None
    participants: List[str] = Field(default_factory=list)
    duration: Optional[str] = None
    assessment: Optional[str] = None
    notes: Optional[str] = None


class RecruitingProcess(BaseModel):
    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    interview_stages: Optional[int] = Field(default=None, ge=0, le=20)
    phases: List[Phase] = Field(default_factory=list)
    stakeholders: List[Stakeholder] = Field(default_factory=list)

    timeline: Optional[str] = None
    application_instructions: Optional[str] = None
    contact_email: Optional[EmailStr] = None
    onboarding: Optional[str] = None


class GeneratedContent(BaseModel):
    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    content_language: Optional[LanguageCode] = None
    job_ad_markdown: Optional[str] = None
    interview_guide_markdown: Optional[str] = None
    boolean_search_string: Optional[str] = None


CURRENT_SCHEMA_VERSION = 1


class NeedAnalysisProfile(BaseModel):
    """
    Industry-agnostic, bilingual-friendly structured profile.
    Store *content* in whichever language you imported/edited; UI i18n is separate.
    """

    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    schema_version: int = Field(default=CURRENT_SCHEMA_VERSION, ge=1)

    company: Company = Field(default_factory=Company)
    team: TeamContext = Field(default_factory=TeamContext)
    position: Position = Field(default_factory=Position)
    location: Location = Field(default_factory=Location)
    employment: Employment = Field(default_factory=Employment)
    compensation: Compensation = Field(default_factory=Compensation)
    benefits: Benefits = Field(default_factory=Benefits)
    responsibilities: Responsibilities = Field(default_factory=Responsibilities)
    requirements: Requirements = Field(default_factory=Requirements)
    recruiting_process: RecruitingProcess = Field(default_factory=RecruitingProcess)
    generated: GeneratedContent = Field(default_factory=GeneratedContent)

    # escape hatch for niche cases without breaking validation
    custom_fields: Dict[str, Any] = Field(default_factory=dict)


# =========================
# Root document: profile + provenance + import context
# =========================


class InputKind(str, Enum):
    URL = "url"
    FILE = "file"
    TEXT = "text"


class InputSource(BaseModel):
    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    kind: InputKind
    url: Optional[str] = None
    filename: Optional[str] = None
    content_type: Optional[str] = None
    imported_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    content_hash: Optional[str] = None  # sha256(text-or-bytes)
    note: Optional[str] = None


class NeedAnalysisProfileDocument(BaseModel):
    """
    This is the single object you pass around in your Streamlit app.
    """

    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    id: str = Field(default_factory=lambda: __import__("uuid").uuid4().hex)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    ui_language: LanguageCode = LanguageCode.DE
    source_language: DetectedLanguage = DetectedLanguage.UNKNOWN

    profile: NeedAnalysisProfile = Field(default_factory=NeedAnalysisProfile)

    # Canonical dot-path -> provenance
    provenance: Dict[str, FieldProvenance] = Field(default_factory=dict)

    # What was imported (URL/file/text). Multiple inputs allowed.
    inputs: List[InputSource] = Field(default_factory=list)


# =========================
# Dot-path helpers + update API (keeps profile & provenance in sync)
# =========================


def _split_path(path: str) -> List[str]:
    return [p for p in path.split(".") if p]


def get_value_by_path(model: BaseModel, path: str) -> Any:
    current: Any = model
    for part in _split_path(path):
        if isinstance(current, BaseModel):
            if not hasattr(current, part):
                raise AttributeError(
                    f"Unknown field '{part}' on {type(current).__name__} while reading '{path}'"
                )
            current = getattr(current, part)
        elif isinstance(current, dict):
            current = current.get(part)
        else:
            raise TypeError(
                f"Cannot traverse into {type(current).__name__} at '{part}' while reading '{path}'"
            )
    return current


def set_value_by_path(model: BaseModel, path: str, value: Any) -> None:
    parts = _split_path(path)
    if not parts:
        raise ValueError("Empty path")
    current: Any = model
    for part in parts[:-1]:
        if isinstance(current, BaseModel):
            if not hasattr(current, part):
                raise AttributeError(
                    f"Unknown field '{part}' on {type(current).__name__} while writing '{path}'"
                )
            nxt = getattr(current, part)
            if nxt is None:
                raise ValueError(
                    f"Cannot traverse through None at '{part}' while writing '{path}'"
                )
            current = nxt
        elif isinstance(current, dict):
            if part not in current or current[part] is None:
                current[part] = {}
            current = current[part]
        else:
            raise TypeError(
                f"Cannot traverse into {type(current).__name__} at '{part}' while writing '{path}'"
            )
    last = parts[-1]
    if isinstance(current, BaseModel):
        if not hasattr(current, last):
            raise AttributeError(
                f"Unknown field '{last}' on {type(current).__name__} while writing '{path}'"
            )
        setattr(current, last, value)
    elif isinstance(current, dict):
        current[last] = value
    else:
        raise TypeError(
            f"Cannot set on {type(current).__name__} at '{last}' while writing '{path}'"
        )


def update_field(
    doc: NeedAnalysisProfileDocument,
    path: str,
    value: Any,
    *,
    source: FieldSource,
    confidence: float | None = None,
    extractor: str | None = None,
    evidence: List[str] | None = None,
    notes: str | None = None,
) -> None:
    """
    Update a profile field and its provenance in one call (use this everywhere in UI/pipeline).
    """
    set_value_by_path(doc.profile, path, value)
    doc.provenance[path] = FieldProvenance(
        source=source,
        confidence=confidence,
        extractor=extractor,
        evidence=evidence or [],
        notes=notes,
    )
    doc.updated_at = datetime.now(timezone.utc)


def needs_question(
    doc: NeedAnalysisProfileDocument,
    path: str,
    *,
    min_confidence: float = 0.65,
    treat_user_as_certain: bool = True,
) -> bool:
    """
    Core heuristic for dynamic questions.
    - Ask when value is missing/empty.
    - Ask when provenance is missing (unknown origin).
    - Ask when confidence is below a threshold (unless user-confirmed).
    """
    value = get_value_by_path(doc.profile, path)
    prov = doc.provenance.get(path)

    if value is None:
        return True
    if isinstance(value, str) and not value.strip():
        return True
    if isinstance(value, list) and len(value) == 0:
        return True

    if prov is None:
        return True

    if treat_user_as_certain and prov.source == FieldSource.USER:
        return False

    if prov.confidence is None:
        return False

    return prov.confidence < min_confidence


# Robust even in dynamic loading contexts (notebooks/exec)
NeedAnalysisProfile.model_rebuild()
NeedAnalysisProfileDocument.model_rebuild()
