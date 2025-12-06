from __future__ import annotations

import io
from typing import Any, Iterable

from docx import Document

from .i18n import LANG_DE, option_label
from .keys import Keys
from .profile import get_value, is_missing
from .utils import list_to_multiline, multiline_to_list, normalize_space


def _as_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(x).strip() for x in value if str(x).strip()]
    if isinstance(value, str):
        return multiline_to_list(value)
    return [str(value).strip()] if str(value).strip() else []


def _title_for_lang(profile: dict, lang: str) -> str:
    if lang != LANG_DE:
        v = get_value(profile, Keys.POSITION_TITLE_EN)
        if isinstance(v, str) and v.strip():
            return v.strip()
    v = get_value(profile, Keys.POSITION_TITLE) or ""
    return str(v).strip()


def _list_for_lang(profile: dict, lang: str, preferred_path: str, fallback_path: str) -> list[str]:
    if lang != LANG_DE:
        v = get_value(profile, preferred_path)
        if v is not None and not is_missing(profile, preferred_path):
            return _as_list(v)
    return _as_list(get_value(profile, fallback_path))


def render_job_ad_markdown(profile: dict, lang: str) -> str:
    company = str(get_value(profile, Keys.COMPANY_NAME) or "").strip()
    website = str(get_value(profile, Keys.COMPANY_WEBSITE) or "").strip()
    industry = str(get_value(profile, Keys.COMPANY_INDUSTRY) or "").strip()
    size = str(get_value(profile, Keys.COMPANY_SIZE) or "").strip()
    hq = str(get_value(profile, Keys.COMPANY_HQ) or "").strip()
    company_desc = str(get_value(profile, Keys.COMPANY_DESC) or "").strip()

    title = _title_for_lang(profile, lang)
    seniority = get_value(profile, Keys.POSITION_SENIORITY)
    seniority_lbl = option_label(lang, "seniority", str(seniority)) if seniority else ""
    role_summary = str(get_value(profile, Keys.POSITION_SUMMARY) or "").strip()

    work_policy = get_value(profile, Keys.LOCATION_WORK_POLICY)
    work_policy_lbl = option_label(lang, "work_policy", str(work_policy)) if work_policy else ""
    city = str(get_value(profile, Keys.LOCATION_CITY) or "").strip()
    remote_scope = str(get_value(profile, Keys.LOCATION_REMOTE_SCOPE) or "").strip()
    tz = str(get_value(profile, Keys.LOCATION_TZ) or "").strip()

    emp_type = get_value(profile, Keys.EMPLOYMENT_TYPE)
    emp_type_lbl = option_label(lang, "employment_type", str(emp_type)) if emp_type else ""
    contract = get_value(profile, Keys.EMPLOYMENT_CONTRACT)
    contract_lbl = option_label(lang, "contract_type", str(contract)) if contract else ""
    start_date = str(get_value(profile, Keys.EMPLOYMENT_START) or "").strip()

    salary_provided = bool(get_value(profile, Keys.SALARY_PROVIDED))
    salary_min = get_value(profile, Keys.SALARY_MIN)
    salary_max = get_value(profile, Keys.SALARY_MAX)
    currency = str(get_value(profile, Keys.SALARY_CURRENCY) or "").strip() or "EUR"
    period = get_value(profile, Keys.SALARY_PERIOD)
    period_lbl = option_label(lang, "salary_period", str(period)) if period else ""

    benefits = _as_list(get_value(profile, Keys.BENEFITS_ITEMS))
    resp_items = _as_list(get_value(profile, Keys.RESPONSIBILITIES))

    hard = _list_for_lang(profile, lang, Keys.HARD_REQ_EN, Keys.HARD_REQ)
    hard_opt = _as_list(get_value(profile, Keys.HARD_OPT))
    soft = _list_for_lang(profile, lang, Keys.SOFT_REQ_EN, Keys.SOFT_REQ)
    languages = _as_list(get_value(profile, Keys.LANG_REQ))
    tools = _list_for_lang(profile, lang, Keys.TOOLS_EN, Keys.TOOLS)
    must_not = _as_list(get_value(profile, Keys.MUST_NOT))

    stages = _as_list(get_value(profile, Keys.PROCESS_STAGES))
    timeline = str(get_value(profile, Keys.PROCESS_TIMELINE) or "").strip()
    instructions = str(get_value(profile, Keys.PROCESS_INSTRUCTIONS) or "").strip()
    contact = str(get_value(profile, Keys.PROCESS_CONTACT) or "").strip() or str(get_value(profile, Keys.COMPANY_CONTACT_EMAIL) or "").strip()

    if lang == LANG_DE:
        h_company = "Über das Unternehmen"
        h_role = "Die Rolle"
        h_tasks = "Deine Aufgaben"
        h_req = "Dein Profil"
        h_benefits = "Benefits"
        h_process = "Recruiting Prozess"
        h_apply = "Bewerbung"
        apply_line = f"Bitte sende deine Bewerbung an: {contact}" if contact else ""
    else:
        h_company = "About the company"
        h_role = "The role"
        h_tasks = "Responsibilities"
        h_req = "Requirements"
        h_benefits = "Benefits"
        h_process = "Recruiting process"
        h_apply = "How to apply"
        apply_line = f"Please send your application to: {contact}" if contact else ""

    md: list[str] = []
    md.append(f"# {title}".strip())
    if seniority_lbl:
        md.append(f"**{seniority_lbl}**")
    md.append("")

    if company:
        md.append(f"## {h_company}")
        if company_desc:
            md.append(company_desc)
        else:
            line = company
            details: list[str] = []
            if industry:
                details.append(industry)
            if size:
                details.append(size)
            if hq:
                details.append(hq)
            if details:
                line += " (" + ", ".join(details) + ")"
            md.append(line)
        if website:
            md.append(f"- {website}")
        md.append("")

    md.append(f"## {h_role}")
    facts: list[str] = []
    if city:
        facts.append(city)
    if work_policy_lbl:
        facts.append(work_policy_lbl)
    if emp_type_lbl:
        facts.append(emp_type_lbl)
    if contract_lbl:
        facts.append(contract_lbl)
    if start_date:
        facts.append(start_date)
    if facts:
        md.append("- " + " · ".join(facts))
    if work_policy == "remote":
        if remote_scope:
            md.append(f"- Remote scope: {remote_scope}")
        if tz:
            md.append(f"- Timezone: {tz}")
    if salary_provided and (salary_min or salary_max):
        range_part = f"{salary_min or ''}–{salary_max or ''}".strip("–")
        salary_line = f"- Salary: {range_part} {currency}".strip()
        if period_lbl:
            salary_line += f" / {period_lbl}"
        md.append(salary_line)
    if role_summary:
        md.append("")
        md.append(role_summary)
    md.append("")

    md.append(f"## {h_tasks}")
    md.extend(_bullets(resp_items, empty_fallback="(TBD)"))
    md.append("")

    md.append(f"## {h_req}")
    if hard:
        md.append("**Hard skills**")
        md.extend(_bullets(hard))
    if hard_opt:
        md.append("")
        md.append("**Nice-to-haves**")
        md.extend(_bullets(hard_opt))
    if soft:
        md.append("")
        md.append("**Soft skills**")
        md.extend(_bullets(soft))
    if languages:
        md.append("")
        md.append("**Languages**")
        md.extend(_bullets(languages))
    if tools:
        md.append("")
        md.append("**Tools / technologies**")
        md.extend(_bullets(tools))
    if must_not:
        md.append("")
        md.append("**Must-not-haves**")
        md.extend(_bullets(must_not))
    md.append("")

    md.append(f"## {h_benefits}")
    md.extend(_bullets(benefits, empty_fallback="(TBD)"))
    md.append("")

    if stages or timeline or instructions or contact:
        md.append(f"## {h_process}")
        if stages:
            md.append("**Stages**")
            md.extend(_bullets(stages))
        if timeline:
            md.append(f"- Timeline: {timeline}")
        if instructions:
            md.append("\n" + instructions if not instructions.startswith("-") else instructions)
        md.append("")

    if apply_line:
        md.append(f"## {h_apply}")
        md.append(apply_line)

    return "\n".join(
        [normalize_space(line) if line and not line.startswith("-") and not line.startswith("#") else line for line in md]
    ).strip()


def _bullets(items: Iterable[str], empty_fallback: str | None = None) -> list[str]:
    clean = [normalize_space(x) for x in items if normalize_space(x)]
    if not clean and empty_fallback:
        return [f"- {empty_fallback}"]
    return [f"- {x}" for x in clean]


def export_docx_bytes(profile: dict, lang: str, markdown_override: str | None = None) -> bytes:
    """Create a basic DOCX export (editable)."""
    doc = Document()

    md = markdown_override or render_job_ad_markdown(profile, lang)
    for line in md.splitlines():
        raw = line.rstrip()
        if not raw:
            continue
        if raw.startswith("# "):
            doc.add_heading(raw[2:].strip(), level=1)
        elif raw.startswith("## "):
            doc.add_heading(raw[3:].strip(), level=2)
        elif raw.startswith("- "):
            doc.add_paragraph(raw[2:].strip(), style="List Bullet")
        elif raw.startswith("**") and raw.endswith("**") and len(raw) > 4:
            doc.add_paragraph(raw.strip("*"))
        else:
            doc.add_paragraph(raw)

    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()
