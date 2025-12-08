from __future__ import annotations

import base64
import json
import os
import re
from functools import partial
from pathlib import Path
from typing import Any, Mapping, TypedDict, cast

import altair as alt
import pandas as pd
import streamlit as st

from .esco_client import ESCOError, occupation_related_skills, search_occupations
from .i18n import LANG_DE, LANG_EN, as_lang, option_label, t
from .ingest import (
    IngestError,
    SourceDocument,
    extract_text_from_upload,
    fetch_text_from_url,
    source_from_text,
)
from .keys import ALL_FIELDS, REQUIRED_FIELDS, Keys
from .llm_prompts import (
    EXTRACTION_INSTRUCTIONS,
    FILL_MISSING_INSTRUCTIONS,
    FOLLOWUP_INSTRUCTIONS,
    SUGGEST_MISSING_INSTRUCTIONS,
    TRANSLATE_INSTRUCTIONS,
    LLMClient,
    extraction_user_prompt,
    fill_missing_fields_prompt,
    followup_user_prompt,
    safe_parse_json,
    suggest_missing_fields_prompt,
    translate_user_prompt,
)
from .profile import (
    Provenance,
    clear_field,
    flatten_values,
    get_record,
    get_value,
    is_missing,
    is_missing_value,
    missing_required,
    new_profile,
    set_field,
    to_json,
    update_source_language,
    upsert_field,
)
from .question_engine import (
    STEPS,
    iter_missing_optional,
    missing_required_for_step,
    question_bank,
    question_help,
    question_label,
    select_questions_for_step,
)
from .rendering import export_docx_bytes, render_job_ad_markdown
from .salary_prediction import (
    SalaryAdjustment,
    SalaryPrediction,
    collect_salary_factors,
    predict_salary_range,
)
from .settings import APP_NAME, MAX_SOURCE_TEXT_CHARS
from .utils import extract_emails, extract_urls, list_to_multiline, multiline_to_list

# Session state keys
SS_PROFILE = "profile"
SS_STEP = "step"
SS_SOURCE_DOC = "source_doc"
SS_MODEL = "openai_model"
SS_USE_ESCO = "use_esco"
SS_AUTO_AI = "auto_ai_followups"
SS_AI_FOLLOWUPS = "ai_followups"
SS_TRANSLATED = "translated_once"
SS_JOB_AD_DRAFT = "job_ad_draft"
SS_THEME = "ui_theme"
SS_PENDING_ESCO_HARD_REQ = "pending_esco_hard_req"
SS_SHOW_REQUIRED_WARNING = "show_required_warning"
SS_SALARY_FACTORS = "salary_factors"
SS_SALARY_RESULT = "salary_prediction_result"
SS_SALARY_NARRATIVE = "salary_prediction_narrative"

THEME_LIGHT = "light"
THEME_DARK = "dark"

DEFAULT_MODEL = "gpt-5-mini"

BACKGROUND_IMAGE_PATH = Path("images/AdobeStock_506577005.jpeg")
LOGO_IMAGE_PATH = Path("images/animation_pulse_Default_7kigl22lw.gif")

PRIORITY_REQUIRED_PATHS = [
    Keys.POSITION_TITLE,
    Keys.EMPLOYMENT_TYPE,
    Keys.EMPLOYMENT_CONTRACT,
    Keys.LOCATION_CITY,
    Keys.LANG_REQ,
]

MAX_SUGGESTION_PATHS = 12

_EMPLOYMENT_TYPE_KEYWORDS: dict[str, str] = {
    "vollzeit": "full_time",
    "full time": "full_time",
    "full-time": "full_time",
    "teilzeit": "part_time",
    "part time": "part_time",
    "part-time": "part_time",
    "werkstudent": "part_time",
    "student": "part_time",
    "contractor": "contractor",
    "freelance": "contractor",
    "freelancer": "contractor",
    "praktikant": "intern",
    "praktikum": "intern",
    "intern": "intern",
    "internship": "intern",
}

_CONTRACT_TYPE_KEYWORDS: dict[str, str] = {
    "unbefristet": "permanent",
    "permanent": "permanent",
    "befristet": "fixed_term",
    "befristete": "fixed_term",
    "befristeter": "fixed_term",
    "fixed term": "fixed_term",
    "zeitvertrag": "fixed_term",
}

_LANGUAGE_KEYWORDS: dict[str, str] = {
    "german": "German",
    "deutsch": "German",
    "english": "English",
    "englisch": "English",
    "french": "French",
    "franz": "French",
    "spanish": "Spanish",
    "spanisch": "Spanish",
}

_CITY_PATTERNS: list[re.Pattern[str]] = [
    re.compile(
        r"(?:standort|location)[:\s]+([A-ZÄÖÜ][\wÄÖÜäöüß .-]{2,50})", re.IGNORECASE
    ),
    re.compile(r"in\s+([A-ZÄÖÜ][\wÄÖÜäöüß.-]{2,50})", re.IGNORECASE),
]

_STEP_LABEL_KEYS = {
    "intake": "intake.title",
    "company": "step.company",
    "team": "step.team",
    "framework": "step.framework",
    "tasks": "step.tasks",
    "skills": "step.skills",
    "benefits": "step.benefits",
    "process": "step.process",
    "review": "step.review",
}

SALARY_FACTOR_OPTIONS: tuple[tuple[str, str], ...] = (
    (Keys.POSITION_SENIORITY, "salary.factor.seniority"),
    (Keys.LOCATION_CITY, "salary.factor.city"),
    (Keys.LOCATION_WORK_POLICY, "salary.factor.work_policy"),
    (Keys.LOCATION_REMOTE_SCOPE, "salary.factor.remote_scope"),
    (Keys.EMPLOYMENT_TYPE, "salary.factor.employment_type"),
    (Keys.EMPLOYMENT_CONTRACT, "salary.factor.contract_type"),
    (Keys.COMPANY_INDUSTRY, "salary.factor.industry"),
    (Keys.COMPANY_SIZE, "salary.factor.company_size"),
    (Keys.SALARY_CURRENCY, "salary.factor.currency"),
)


class SalaryNarrative(TypedDict):
    de: str
    en: str


def _init_state() -> None:
    # Initialize session state for multi-step progress
    if SS_STEP not in st.session_state:
        st.session_state[SS_STEP] = "intake"
    if SS_PROFILE not in st.session_state:
        st.session_state[SS_PROFILE] = new_profile(ui_language=LANG_DE)
    if SS_SOURCE_DOC not in st.session_state:
        st.session_state[SS_SOURCE_DOC] = None
    if SS_AI_FOLLOWUPS not in st.session_state:
        st.session_state[SS_AI_FOLLOWUPS] = {}
    st.session_state[SS_MODEL] = DEFAULT_MODEL
    if SS_USE_ESCO not in st.session_state:
        st.session_state[SS_USE_ESCO] = True
    if SS_AUTO_AI not in st.session_state:
        st.session_state[SS_AUTO_AI] = False
    if SS_TRANSLATED not in st.session_state:
        st.session_state[SS_TRANSLATED] = False
    if SS_JOB_AD_DRAFT not in st.session_state:
        st.session_state[SS_JOB_AD_DRAFT] = ""
    if SS_THEME not in st.session_state:
        st.session_state[SS_THEME] = THEME_LIGHT
    if SS_PENDING_ESCO_HARD_REQ not in st.session_state:
        st.session_state[SS_PENDING_ESCO_HARD_REQ] = []
    if SS_SHOW_REQUIRED_WARNING not in st.session_state:
        st.session_state[SS_SHOW_REQUIRED_WARNING] = False
    if SS_SALARY_FACTORS not in st.session_state:
        st.session_state[SS_SALARY_FACTORS] = {
            Keys.POSITION_SENIORITY,
            Keys.LOCATION_CITY,
            Keys.EMPLOYMENT_TYPE,
            Keys.EMPLOYMENT_CONTRACT,
        }
    if SS_SALARY_RESULT not in st.session_state:
        st.session_state[SS_SALARY_RESULT] = None
    if SS_SALARY_NARRATIVE not in st.session_state:
        st.session_state[SS_SALARY_NARRATIVE] = None


def _reset_session() -> None:
    # Clear all relevant session keys and restart
    for k in [
        SS_PROFILE,
        SS_STEP,
        SS_SOURCE_DOC,
        SS_MODEL,
        SS_USE_ESCO,
        SS_AUTO_AI,
        SS_AI_FOLLOWUPS,
        SS_TRANSLATED,
        SS_JOB_AD_DRAFT,
        SS_THEME,
        SS_SHOW_REQUIRED_WARNING,
        SS_SALARY_FACTORS,
        SS_SALARY_RESULT,
        SS_SALARY_NARRATIVE,
    ]:
        st.session_state.pop(k, None)
    st.rerun()


def _get_lang() -> str:
    # Determine current UI language from session (default to DE)
    return as_lang(st.session_state.get("ui_lang", LANG_DE))


def _resolve_api_key() -> str | None:
    """Return the configured OpenAI API key without exposing it in the UI."""
    try:
        raw_secrets = st.secrets  # type: ignore[attr-defined]
    except Exception:
        raw_secrets = None
    if raw_secrets:
        direct_secret = raw_secrets.get("OPENAI_API_KEY")
        if direct_secret:
            return str(direct_secret)
        general_secret = raw_secrets.get("general", {})
        if isinstance(general_secret, dict):
            nested_secret = general_secret.get("OPENAI_API_KEY")
            if nested_secret:
                return str(nested_secret)
    env_key = os.getenv("OPENAI_API_KEY")
    if env_key:
        return env_key
    return None


def _apply_extracted_fields(
    profile: dict[str, Any],
    entries: list[Any],
    *,
    evidence: str,
    provenance: Provenance = "extracted",
) -> int:
    updates = 0
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        path = entry.get("path")
        val = entry.get("value")
        conf = entry.get("confidence")
        if path in ALL_FIELDS and upsert_field(
            profile,
            path,
            val,
            provenance=provenance,
            confidence=conf if isinstance(conf, (int, float)) else None,
            evidence=evidence,
        ):
            updates += 1
    return updates


def _dedupe_preserve_order(items: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        ordered.append(item)
    return ordered


def _guess_job_title(source_doc: SourceDocument) -> str | None:
    name_candidates = [source_doc.name]
    if source_doc.name and any(sep in source_doc.name for sep in ["|", "-"]):
        for token in re.split(r"[|\-–—]", source_doc.name):
            cleaned = token.strip()
            if cleaned:
                name_candidates.append(cleaned)
    text_candidates = [
        line.strip() for line in source_doc.text.splitlines() if line.strip()
    ]
    for cand in [*name_candidates, *text_candidates]:
        if 3 <= len(cand) <= 120:
            return cand
    return None


def _detect_keyword_value(text_lower: str, keyword_map: dict[str, str]) -> str | None:
    for key, mapped in keyword_map.items():
        if key in text_lower:
            return mapped
    return None


def _detect_languages(text_lower: str) -> list[str]:
    hits: list[str] = []
    for key, mapped in _LANGUAGE_KEYWORDS.items():
        if key in text_lower:
            hits.append(mapped)
    return _dedupe_preserve_order(hits)


def _find_city(text: str, name: str | None) -> str | None:
    for pattern in _CITY_PATTERNS:
        match = pattern.search(text)
        if match:
            candidate = match.group(1).strip().strip(",.;")
            if candidate:
                return candidate
    if name:
        for token in re.split(r"[|\-–—]", name):
            cleaned = token.strip()
            if cleaned and 2 <= len(cleaned) <= 60 and cleaned[0].isupper():
                return cleaned
    return None


def _heuristic_fill_required_fields(
    profile: dict[str, Any], missing_paths: list[str], source_doc: SourceDocument
) -> int:
    text_lower = source_doc.text.lower()
    updates = 0
    if Keys.POSITION_TITLE in missing_paths:
        title = _guess_job_title(source_doc)
        if title and upsert_field(
            profile,
            Keys.POSITION_TITLE,
            title,
            provenance="extracted",
            confidence=0.35,
            evidence="heuristic_title",
        ):
            updates += 1
    if Keys.EMPLOYMENT_TYPE in missing_paths:
        employment_type = _detect_keyword_value(text_lower, _EMPLOYMENT_TYPE_KEYWORDS)
        if employment_type and upsert_field(
            profile,
            Keys.EMPLOYMENT_TYPE,
            employment_type,
            provenance="extracted",
            confidence=0.30,
            evidence="keyword_employment_type",
        ):
            updates += 1
    if Keys.EMPLOYMENT_CONTRACT in missing_paths:
        contract_type = _detect_keyword_value(text_lower, _CONTRACT_TYPE_KEYWORDS)
        if contract_type and upsert_field(
            profile,
            Keys.EMPLOYMENT_CONTRACT,
            contract_type,
            provenance="extracted",
            confidence=0.30,
            evidence="keyword_contract_type",
        ):
            updates += 1
    if Keys.LANG_REQ in missing_paths:
        languages = _detect_languages(text_lower)
        if languages and upsert_field(
            profile,
            Keys.LANG_REQ,
            languages,
            provenance="extracted",
            confidence=0.25,
            evidence="keyword_languages",
        ):
            updates += 1
    if Keys.LOCATION_CITY in missing_paths:
        city = _find_city(source_doc.text, source_doc.name)
        if city and upsert_field(
            profile,
            Keys.LOCATION_CITY,
            city,
            provenance="extracted",
            confidence=0.20,
            evidence="location_hint",
        ):
            updates += 1
    return updates


def _collect_paths_for_ai_suggestions(profile: dict[str, Any]) -> list[str]:
    missing: list[str] = []
    for path in sorted(REQUIRED_FIELDS):
        if is_missing(profile, path):
            missing.append(path)
    optional_paths = [q.path for q in question_bank() if not q.required]
    for path in optional_paths:
        if is_missing(profile, path):
            missing.append(path)
    return _dedupe_preserve_order(missing)


def _set_step(step: str) -> None:
    if step in STEPS:
        st.session_state[SS_STEP] = step


def _step_index(step: str) -> int:
    try:
        return list(STEPS).index(step)
    except ValueError:
        return 0


def _go_next() -> None:
    idx = _step_index(st.session_state[SS_STEP])
    if idx < len(STEPS) - 1:
        st.session_state[SS_STEP] = STEPS[idx + 1]


def _go_prev() -> None:
    idx = _step_index(st.session_state[SS_STEP])
    if idx > 0:
        st.session_state[SS_STEP] = STEPS[idx - 1]


def _jump_to_step(step: str) -> None:
    _set_step(step)
    st.rerun()


def _apply_theme(theme: str) -> None:
    # Apply a custom light/dark theme via CSS variables
    css_light = """
    :root {
        --cs-bg: #f6f8fb;
        --cs-text: #0b1220;
        --cs-surface: #e7ebf3;
        --cs-surface-strong: #d8deea;
        --cs-primary: #1f7a8c;
        --cs-accent: #5eead4;
        --cs-border: #cdd5e4;
        --cs-muted: #3c4a64;
    }
    body {
        background-color: var(--cs-bg);
        color: var(--cs-text);
    }
    .stApp {
        background-color: var(--cs-bg);
    }
    .stSidebar, .sidebar-content {
        background: var(--cs-surface);
    }
    .stButton>button, .stDownloadButton>button {
        background: linear-gradient(135deg, var(--cs-primary), var(--cs-accent));
        border: none;
        color: #0b1220;
        font-weight: 600;
        box-shadow: 0 10px 30px rgba(31, 122, 140, 0.18);
        transition: transform 120ms ease, box-shadow 120ms ease;
    }
    .stButton>button:hover, .stDownloadButton>button:hover {
        transform: translateY(-1px);
        box-shadow: 0 16px 38px rgba(31, 122, 140, 0.25);
    }
    .stButton>button:focus-visible, .stDownloadButton>button:focus-visible {
        outline: 2px solid var(--cs-primary);
        outline-offset: 2px;
    }
    .stButton>button {
        border-radius: 0.25rem;
    }
    .cs-sidebar-shell {
        display: flex;
        flex-direction: column;
        gap: 0.75rem;
        color: var(--cs-text);
    }
    .cs-sidebar-card {
        background: var(--cs-surface-strong);
        border: 1px solid var(--cs-border);
        border-radius: 0.75rem;
        padding: 0.75rem 0.85rem;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.08);
    }
    .cs-sidebar-card-heading {
        font-size: 1.05rem;
        font-weight: 700;
        display: flex;
        align-items: center;
        gap: 0.35rem;
    }
    .cs-sidebar-card-subtitle {
        margin: 0.25rem 0 0;
        color: var(--cs-muted);
        font-size: 0.9rem;
    }
    .cs-sidebar-section-title {
        font-weight: 600;
        display: flex;
        align-items: center;
        gap: 0.35rem;
        color: var(--cs-text);
        margin-bottom: 0.35rem;
    }
    .cs-sidebar-divider {
        border: none;
        border-top: 1px solid var(--cs-border);
        margin: 0.15rem 0 0.5rem;
    }
    """
    css_dark = """
    :root {
        --cs-bg: #0c1626;
        --cs-text: #e5e7eb;
        --cs-surface: #111c2f;
        --cs-surface-strong: #1f2b3e;
        --cs-primary: #1f7a8c;
        --cs-accent: #5eead4;
        --cs-border: #24344d;
        --cs-muted: #94a3b8;
    }
    body {
        background-color: var(--cs-bg);
        color: var(--cs-text);
    }
    .stApp {
        background-color: var(--cs-bg);
    }
    .stSidebar, .sidebar-content {
        background: var(--cs-surface);
    }
    .stButton>button, .stDownloadButton>button {
        background: linear-gradient(135deg, var(--cs-primary), var(--cs-accent));
        border: none;
        color: #0b1220;
        font-weight: 600;
        box-shadow: 0 10px 30px rgba(94, 234, 212, 0.18);
        transition: transform 120ms ease, box-shadow 120ms ease;
    }
    .stButton>button:hover, .stDownloadButton>button:hover {
        transform: translateY(-1px);
        box-shadow: 0 16px 38px rgba(94, 234, 212, 0.28);
    }
    .stButton>button:focus-visible, .stDownloadButton>button:focus-visible {
        outline: 2px solid var(--cs-accent);
        outline-offset: 2px;
    }
    .stButton>button {
        border-radius: 0.25rem;
    }
    .cs-sidebar-shell {
        display: flex;
        flex-direction: column;
        gap: 0.75rem;
        color: var(--cs-text);
    }
    .cs-sidebar-card {
        background: var(--cs-surface-strong);
        border: 1px solid var(--cs-border);
        border-radius: 0.75rem;
        padding: 0.75rem 0.85rem;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.18);
    }
    .cs-sidebar-card-heading {
        font-size: 1.05rem;
        font-weight: 700;
        display: flex;
        align-items: center;
        gap: 0.35rem;
    }
    .cs-sidebar-card-subtitle {
        margin: 0.25rem 0 0;
        color: var(--cs-muted);
        font-size: 0.9rem;
    }
    .cs-sidebar-section-title {
        font-weight: 600;
        display: flex;
        align-items: center;
        gap: 0.35rem;
        color: var(--cs-text);
        margin-bottom: 0.35rem;
    }
    .cs-sidebar-divider {
        border: none;
        border-top: 1px solid var(--cs-border);
        margin: 0.15rem 0 0.5rem;
    }
    """
    style = css_light if theme == THEME_LIGHT else css_dark
    st.write(f"<style>{style}</style>", unsafe_allow_html=True)


def _apply_background(image_path: Path) -> None:
    # Set a fixed background image (with overlay handled in CSS in the image file itself)
    if image_path.exists():
        img_bytes = image_path.read_bytes()
        encoded = base64.b64encode(img_bytes).decode()
        st.write(
            f"""
            <style>
            .stApp {{
                background: url("data:image/jpeg;base64,{encoded}") center/cover no-repeat;
            }}
            </style>
            """,
            unsafe_allow_html=True,
        )


def _render_branding(image_path: Path) -> None:
    # Render a small pulsating logo image in the top-right corner
    if image_path.exists():
        st.markdown(
            f"""
            <style>
                .cs-brand-badge {{
                    position: fixed;
                    top: 1rem;
                    right: 1rem;
                    width: 7.5rem;
                    height: 7.5rem;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    background: var(--cs-surface, #ffffff);
                    border-radius: 1rem;
                    box-shadow: 0 14px 42px rgba(0, 0, 0, 0.12);
                    z-index: 1000;
                }}
                .cs-brand-badge img {{
                    width: 5.5rem;
                    height: 5.5rem;
                    object-fit: contain;
                }}
                @media (max-width: 768px) {{
                    .cs-brand-badge {{
                        right: 50%;
                        transform: translateX(50%);
                        width: 6.25rem;
                        height: 6.25rem;
                        top: 0.5rem;
                    }}
                    .cs-brand-badge img {{
                        width: 4.5rem;
                        height: 4.5rem;
                    }}
                }}
            </style>
            <div class="cs-brand-badge">
                <img src="data:image/gif;base64,{base64.b64encode(image_path.read_bytes()).decode()}" alt="Logo" />
            </div>
            """,
            unsafe_allow_html=True,
        )


def _format_sidebar_value(value: Any, lang: str) -> str:
    if is_missing_value(value):
        return t(lang, "ui.empty")
    if isinstance(value, list):
        cleaned = [str(v).strip() for v in value if str(v).strip()]
        return ", ".join(cleaned) if cleaned else t(lang, "ui.empty")
    if isinstance(value, bool):
        return t(lang, "ui.boolean_yes") if value else t(lang, "ui.boolean_no")
    if isinstance(value, dict):
        try:
            return json.dumps(value, ensure_ascii=False)
        except TypeError:
            return str(value)
    return str(value)


def _coerce_salary_prediction(raw: Any) -> SalaryPrediction | None:
    if isinstance(raw, SalaryPrediction):
        return raw
    if not isinstance(raw, dict):
        return None
    try:
        adjustments = [
            SalaryAdjustment(
                factor=str(adj.get("factor")),
                multiplier=float(adj.get("multiplier", 1.0)),
                value=str(adj.get("value", "")),
            )
            for adj in raw.get("adjustments", [])
            if isinstance(adj, dict) and "factor" in adj
        ]
        min_raw = raw.get("min_salary")
        max_raw = raw.get("max_salary")
        return SalaryPrediction(
            min_salary=int(min_raw if min_raw is not None else 0),
            max_salary=int(max_raw if max_raw is not None else 0),
            currency=str(raw.get("currency", "EUR")),
            applied_factors=dict(raw.get("applied_factors", {})),
            baseline=dict(raw.get("baseline", {})),
            adjustments=adjustments,
        )
    except Exception:
        return None


def _render_sidebar_overview(*, lang: str, profile: dict[str, Any]) -> None:
    st.markdown(
        f"""
        <div class="cs-sidebar-card">
            <div class="cs-sidebar-section-title">📑 {t(lang, "sidebar.overview")}</div>
            <hr class="cs-sidebar-divider" />
        """,
        unsafe_allow_html=True,
    )
    step_labels = {step: t(lang, _STEP_LABEL_KEYS.get(step, step)) for step in STEPS}
    for step in STEPS:
        questions = [
            q
            for q in question_bank()
            if q.step == step and (not q.show_if or q.show_if(profile))
        ]
        if not questions:
            continue
        expander = st.expander(step_labels.get(step, step), expanded=False)
        with expander:
            st.button(
                f"↪️ {t(lang, 'sidebar.jump_to_step')}",
                key=f"jump-step-{step}",
                on_click=_jump_to_step,
                args=(step,),
            )
            for q in questions:
                label = question_label(q, lang)
                value = _format_sidebar_value(get_value(profile, q.path), lang)
                st.markdown(f"**{label}:** {value}")
    st.markdown("</div>", unsafe_allow_html=True)


def _render_salary_factor_selection(profile: dict[str, Any], *, lang: str) -> set[str]:
    current = set(st.session_state.get(SS_SALARY_FACTORS) or set())
    updated: set[str] = set()
    for path, label_key in SALARY_FACTOR_OPTIONS:
        label = t(lang, label_key)
        value_display = _format_sidebar_value(get_value(profile, path), lang)
        checked = st.checkbox(
            f"{label} ({value_display})",
            value=path in current,
            key=f"salary_factor_{path}",
        )
        if checked:
            updated.add(path)
    st.session_state[SS_SALARY_FACTORS] = updated
    return updated


def _adjustment_label(adj: SalaryAdjustment, *, lang: str) -> str:
    label_map = {
        "base": "salary.factor.seniority",
        "location": "salary.factor.city",
        "work_policy": "salary.factor.work_policy",
        "employment_type": "salary.factor.employment_type",
        "contract_type": "salary.factor.contract_type",
        "industry": "salary.factor.industry",
        "company_size": "salary.factor.company_size",
        "remote_scope": "salary.factor.remote_scope",
    }
    if adj.factor == "base":
        return t(lang, "salary.breakdown.base", adj.value)
    pct = adj.multiplier - 1.0
    pct_str = f"{pct:+.0%}" if pct else "±0%"
    label = t(lang, label_map.get(adj.factor, adj.factor))
    return t(lang, "salary.breakdown.factor", label, pct_str, adj.value or "—")


def _render_salary_chart(
    prediction: SalaryPrediction, *, lang: str, theme: str = THEME_LIGHT
) -> None:
    avg_salary = (prediction.min_salary + prediction.max_salary) / 2
    df = pd.DataFrame(
        [
            {"label": t(lang, "salary.chart.min"), "value": prediction.min_salary},
            {"label": t(lang, "salary.chart.avg"), "value": int(avg_salary)},
            {"label": t(lang, "salary.chart.max"), "value": prediction.max_salary},
        ]
    )
    bar_color = "#1f7a8c" if theme == THEME_LIGHT else "#5eead4"
    text_color = "#0b1220" if theme == THEME_LIGHT else "#e5e7eb"
    chart = (
        alt.Chart(df)
        .mark_bar(cornerRadiusTopLeft=6, cornerRadiusTopRight=6)
        .encode(
            x=alt.X("label", sort=None, title=t(lang, "salary.chart.axis_label")),
            y=alt.Y(
                "value",
                title=f"{t(lang, 'salary.chart.salary_axis')} ({prediction.currency})",
            ),
            tooltip=["label", "value"],
            color=alt.value(bar_color),
        )
        .properties(height=260)
        .configure_axis(labelColor=text_color, titleColor=text_color)
        .configure_view(strokeWidth=0)
    )
    st.altair_chart(chart, use_container_width=True)


def _fallback_salary_narrative(prediction: SalaryPrediction, *, lang: str) -> str:
    adjustments = [adj for adj in prediction.adjustments if adj.factor != "base"]
    adjustments.sort(key=lambda adj: abs(adj.multiplier - 1.0), reverse=True)
    if not adjustments:
        return t(lang, "salary.narrative_fallback")
    highlights = [
        t(lang, "salary.narrative_bullet", _adjustment_label(adj, lang=lang))
        for adj in adjustments[:3]
    ]
    return "\n".join(highlights)


def _generate_salary_narrative(
    prediction: SalaryPrediction,
    selected_factors: Mapping[str, Any],
    *,
    api_key: str,
    model: str,
) -> SalaryNarrative | None:
    try:
        top_adjustments = [
            adj for adj in prediction.adjustments if adj.factor != "base"
        ]
        top_adjustments.sort(key=lambda adj: abs(adj.multiplier - 1.0), reverse=True)
        adjustment_snapshot = [
            {
                "factor": adj.factor,
                "multiplier": adj.multiplier,
                "value": adj.value,
            }
            for adj in top_adjustments[:3]
        ]
        client = LLMClient(api_key=api_key, model=model)
        prompt = (
            "Create a concise bilingual explanation (German and English) for a salary "
            "range prediction. Highlight the top drivers from the provided adjustments "
            "and keep it to 2-3 sentences per language."
            f"\nSalary range: {prediction.min_salary} - {prediction.max_salary}"
            f" {prediction.currency}."
            f"\nSelected factors: {json.dumps(selected_factors, ensure_ascii=False)}"
            f"\nKey adjustments: {json.dumps(adjustment_snapshot, ensure_ascii=False)}"
        )
        instructions = (
            "Respond ONLY with valid JSON following this schema:"
            ' {"de": string, "en": string}.'
            " Each value must be a short paragraph that mentions the range and the key"
            " factors."
        )
        raw = client.text(prompt, instructions=instructions, max_output_tokens=320)
        data = safe_parse_json(raw)
        if not isinstance(data, dict):
            return None
        de_text = str(data.get("de") or "").strip()
        en_text = str(data.get("en") or "").strip()
        if not de_text or not en_text:
            return None
        return {"de": de_text, "en": en_text}
    except Exception:
        return None


def _render_salary_prediction(
    profile: dict[str, Any], *, lang: str, api_key: str, model: str, theme: str
) -> None:
    st.markdown(f"### {t(lang, 'salary.section_title')}")
    st.caption(t(lang, "salary.section_hint"))

    selected_paths = _render_salary_factor_selection(profile, lang=lang)
    st.caption(t(lang, "salary.selection_hint"))

    if st.button(t(lang, "salary.calculate"), key="salary_predict_btn"):
        selected_factors = collect_salary_factors(profile, selected_paths)
        if not selected_factors:
            st.session_state[SS_SALARY_RESULT] = None
            st.session_state[SS_SALARY_NARRATIVE] = None
            st.warning(t(lang, "salary.no_values"))
        else:
            prediction = predict_salary_range(selected_factors)
            st.session_state[SS_SALARY_RESULT] = prediction.to_dict()
            st.session_state[SS_SALARY_NARRATIVE] = _generate_salary_narrative(
                prediction,
                selected_factors,
                api_key=api_key,
                model=model,
            )
            st.success(t(lang, "salary.prediction_done"))

    stored_prediction = _coerce_salary_prediction(
        st.session_state.get(SS_SALARY_RESULT)
    )
    if not stored_prediction:
        return

    st.markdown(f"#### {t(lang, 'salary.result_title')}")
    col_min, col_max = st.columns(2)
    with col_min:
        st.metric(
            t(lang, "salary.range_min"),
            f"{stored_prediction.min_salary:,.0f} {stored_prediction.currency}",
        )
    with col_max:
        st.metric(
            t(lang, "salary.range_max"),
            f"{stored_prediction.max_salary:,.0f} {stored_prediction.currency}",
        )

    st.markdown(f"**{t(lang, 'salary.used_parameters')}**")
    st.json(stored_prediction.applied_factors)

    st.markdown(f"**{t(lang, 'salary.breakdown_title')}**")
    for adj in stored_prediction.adjustments:
        st.write("- " + _adjustment_label(adj, lang=lang))

    st.markdown(f"#### {t(lang, 'salary.chart_title')}")
    _render_salary_chart(stored_prediction, lang=lang, theme=theme)
    st.caption(t(lang, "salary.chart_caption"))

    st.markdown(f"#### {t(lang, 'salary.narrative_title')}")
    stored_narrative = st.session_state.get(SS_SALARY_NARRATIVE)
    narrative_text = None
    if isinstance(stored_narrative, dict):
        narrative_text = stored_narrative.get(lang)
    if narrative_text:
        st.write(narrative_text)
    else:
        st.info(t(lang, "salary.narrative_hint"))
        st.markdown(_fallback_salary_narrative(stored_prediction, lang=lang))


def _render_sidebar(*, lang: str, profile: dict[str, Any]) -> str:
    """Render a structured sidebar with themed sections and controls."""
    with st.sidebar:
        st.markdown('<div class="cs-sidebar-shell">', unsafe_allow_html=True)
        st.markdown(
            f"""
            <div class="cs-sidebar-card">
                <div class="cs-sidebar-card-heading">🧭 {t(lang, "sidebar.title")}</div>
                <p class="cs-sidebar-card-subtitle">{t(lang, "sidebar.subtitle")}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown(
            f"""
            <div class="cs-sidebar-card">
                <div class="cs-sidebar-section-title">🎨 {t(lang, "sidebar.section.display")}</div>
                <hr class="cs-sidebar-divider" />
            """,
            unsafe_allow_html=True,
        )
        ui_lang = st.selectbox(
            f"🔤 {t(lang, 'sidebar.language')}",
            options=[LANG_DE, LANG_EN],
            format_func=lambda x: "Deutsch" if x == LANG_DE else "English",
            key="ui_lang",
        )
        profile.setdefault("meta", {})["ui_language"] = ui_lang
        theme = st.selectbox(
            f"🎨 {t(lang, 'sidebar.theme')}",
            options=[THEME_LIGHT, THEME_DARK],
            format_func=lambda x: t(lang, f"theme.{x}"),
            key=SS_THEME,
        )
        st.markdown(
            f"""
                <div class="cs-sidebar-section-title" style="margin-top:0.35rem;">🧠 {t(lang, "sidebar.section.assistants")}</div>
                <hr class="cs-sidebar-divider" />
            """,
            unsafe_allow_html=True,
        )
        st.session_state[SS_USE_ESCO] = st.checkbox(
            f"🗂️ {t(lang, 'sidebar.use_esco')}", value=st.session_state[SS_USE_ESCO]
        )
        st.session_state[SS_AUTO_AI] = st.checkbox(
            f"🤖 {t(lang, 'sidebar.auto_ai')}", value=st.session_state[SS_AUTO_AI]
        )
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown(
            f"""
            <div class="cs-sidebar-card">
                <div class="cs-sidebar-section-title">⚡ {t(lang, "sidebar.section.actions")}</div>
                <hr class="cs-sidebar-divider" />
            """,
            unsafe_allow_html=True,
        )
        if st.button(f"♻️ {t(lang, 'sidebar.reset')}", use_container_width=True):
            _reset_session()
        st.markdown("</div>", unsafe_allow_html=True)
        _render_sidebar_overview(lang=lang, profile=profile)
        st.markdown("</div>", unsafe_allow_html=True)

    return theme


def run_app() -> None:
    st.set_page_config(page_title="Need Analysis Wizard", page_icon="🧭", layout="wide")
    _init_state()

    lang = _get_lang()
    profile: dict[str, Any] = st.session_state[SS_PROFILE]

    # Resolve API key (from secrets or env) and enforce it
    api_key = _resolve_api_key()
    if not api_key:
        st.error(t(lang, "errors.no_api_key"))
        st.stop()
    api_key = cast(str, api_key)

    theme = _render_sidebar(lang=lang, profile=profile)
    model = st.session_state[SS_MODEL]

    # Apply theme and branding
    _apply_theme(theme)
    _apply_background(BACKGROUND_IMAGE_PATH)
    _render_branding(LOGO_IMAGE_PATH)

    st.title(APP_NAME)
    st.caption(t(lang, "app.tagline"))

    missing = missing_required(profile)
    progress = 1.0 - (len(missing) / max(1, len(REQUIRED_FIELDS)))
    st.progress(progress)
    missing_warning_enabled = bool(st.session_state.get(SS_SHOW_REQUIRED_WARNING))
    if missing and missing_warning_enabled:
        st.warning(f"{t(lang, 'progress.missing_required')}: {', '.join(missing)}")
    elif not missing:
        st.success(t(lang, "progress.ready"))

    # Top navigation: horizontal radio for steps
    step_labels = {s: t(lang, _STEP_LABEL_KEYS.get(s, s)) for s in STEPS}
    current_step = st.radio(
        " ",
        options=list(STEPS),
        index=_step_index(st.session_state[SS_STEP]),
        format_func=lambda s: step_labels.get(s, s),
        horizontal=True,
        label_visibility="collapsed",
    )
    _set_step(current_step)
    current_step = st.session_state[SS_STEP]

    # Prev/Next navigation buttons
    nav_cols = st.columns([1, 6, 1])
    with nav_cols[0]:
        st.button(
            t(lang, "nav.prev"), on_click=_go_prev, disabled=current_step == "intake"
        )
    with nav_cols[2]:
        st.button(
            t(lang, "nav.next"), on_click=_go_next, disabled=current_step == "review"
        )

    st.divider()

    # Render current step content
    if current_step == "intake":
        _render_intake(profile, api_key=api_key, model=model, lang=lang)
        return
    if current_step == "review":
        _render_review(profile, lang=lang, api_key=api_key, model=model, theme=theme)
        return

    _render_questions_step(
        profile, step=current_step, api_key=api_key, model=model, lang=lang
    )


def _render_intake(
    profile: dict[str, Any], *, api_key: str, model: str, lang: str
) -> None:
    st.markdown(f"## {t(lang, 'intake.title')}")
    st.caption(t(lang, "intake.subtitle"))
    url = st.text_input(t(lang, "intake.url"), placeholder="https://…")
    upload = st.file_uploader(t(lang, "intake.file"), type=["pdf", "docx"])
    pasted_text = st.text_area(
        t(lang, "intake.paste"),
        placeholder=t(lang, "intake.paste_placeholder"),
        height=200,
    )
    col1, col2 = st.columns([1, 2])
    with col1:
        process = st.button(t(lang, "intake.process"), type="primary")
    with col2:
        st.info(t(lang, "intake.tip"))
    if not process:
        # If not processing, show preview of already imported source if exists
        doc = st.session_state.get(SS_SOURCE_DOC)
        if doc and isinstance(doc, dict) and doc.get("text"):
            st.markdown(f"### {t(lang, 'intake.source_preview')}")
            st.text_area(
                " ",
                value=doc.get("text", "")[:3000],
                height=250,
                label_visibility="collapsed",
            )
        return

    source_doc: SourceDocument | None = None
    provided_sources = sum(
        1
        for candidate in (
            upload is not None,
            bool(url.strip()),
            bool(pasted_text.strip()),
        )
        if candidate
    )
    if provided_sources == 0:
        st.warning(t(lang, "intake.need_source"))
        return
    if provided_sources > 1:
        st.warning(t(lang, "intake.single_source"))
        return

    try:
        if upload is not None:
            source_doc = extract_text_from_upload(upload)
        elif url.strip():
            source_doc = fetch_text_from_url(url.strip())
        else:
            source_doc = source_from_text(pasted_text)
    except IngestError as exc:
        st.error(f"{t(lang, 'intake.import_failed')}: {exc}")
        return

    # Save source document in session
    st.session_state[SS_SOURCE_DOC] = {
        "source_type": source_doc.source_type,
        "name": source_doc.name,
        "text": source_doc.text,
        "meta": source_doc.meta,
    }

    # Basic extraction: find an email and URL to prefill contact email / website if empty
    emails = extract_emails(source_doc.text)
    urls = extract_urls(source_doc.text)
    if emails and (get_value(profile, Keys.COMPANY_CONTACT_EMAIL) in {None, ""}):
        set_field(
            profile,
            Keys.COMPANY_CONTACT_EMAIL,
            emails[0],
            provenance="extracted",
            confidence=0.55,
            evidence="regex",
        )
    if urls and (get_value(profile, Keys.COMPANY_WEBSITE) in {None, ""}):
        set_field(
            profile,
            Keys.COMPANY_WEBSITE,
            urls[0],
            provenance="extracted",
            confidence=0.50,
            evidence="regex",
        )

    if not api_key:
        # If no API key, skip LLM extraction and go straight to manual form
        st.warning(t(lang, "intake.no_openai_key"))
        st.session_state[SS_PROFILE] = profile
        st.session_state[SS_STEP] = "company"
        st.rerun()
        return

    try:
        # Use LLM to extract fields from the source text
        client = LLMClient(api_key=api_key, model=model)
        source_excerpt = source_doc.text[:MAX_SOURCE_TEXT_CHARS]
        raw = client.text(
            extraction_user_prompt(source_excerpt),
            instructions=EXTRACTION_INSTRUCTIONS,
            max_output_tokens=1000,
        )
        data = safe_parse_json(raw)
        updates = 0
        suggestion_updates = 0
        extracted_fields: list[Any] = []
        if isinstance(data, dict):
            extracted_fields = data.get("fields") or []
            updates += _apply_extracted_fields(
                profile, extracted_fields, evidence="llm_extraction"
            )
            lang_detected = data.get("detected_language")
            if lang_detected and isinstance(lang_detected, str):
                update_source_language(profile, lang_detected)

        missing_priority = [
            path for path in PRIORITY_REQUIRED_PATHS if is_missing(profile, path)
        ]
        updates += _heuristic_fill_required_fields(
            profile, missing_priority, source_doc
        )
        missing_priority = [
            path for path in PRIORITY_REQUIRED_PATHS if is_missing(profile, path)
        ]
        if missing_priority:
            context_payload: dict[str, Any] = {}
            if isinstance(data, dict):
                context_payload = {
                    "detected_language": data.get("detected_language"),
                    "fields": extracted_fields,
                }
            fill_raw = client.text(
                fill_missing_fields_prompt(
                    missing_paths=missing_priority,
                    extracted_context=context_payload,
                    source_text=source_excerpt,
                    source_name=source_doc.name,
                ),
                instructions=FILL_MISSING_INSTRUCTIONS,
                max_output_tokens=600,
            )
            fill_data = safe_parse_json(fill_raw)
            if isinstance(fill_data, dict):
                fill_fields = fill_data.get("fields") or []
                updates += _apply_extracted_fields(
                    profile, fill_fields, evidence="llm_missing_recovery"
                )
        suggestion_paths = _collect_paths_for_ai_suggestions(profile)[
            :MAX_SUGGESTION_PATHS
        ]
        if suggestion_paths:
            suggestion_context: dict[str, Any] = {
                "fields": extracted_fields,
                "profile_values": flatten_values(profile),
            }
            if isinstance(data, dict):
                suggestion_context["detected_language"] = data.get("detected_language")
            suggest_raw = client.text(
                suggest_missing_fields_prompt(
                    missing_paths=suggestion_paths,
                    extracted_context=suggestion_context,
                    source_text=source_excerpt,
                    source_name=source_doc.name,
                ),
                instructions=SUGGEST_MISSING_INSTRUCTIONS,
                max_output_tokens=800,
            )
            suggest_data = safe_parse_json(suggest_raw)
            if isinstance(suggest_data, dict):
                suggested_fields = suggest_data.get("suggestions") or []
                suggestion_updates = _apply_extracted_fields(
                    profile,
                    suggested_fields,
                    evidence="llm_ai_suggestion",
                    provenance="ai_suggestion",
                )
                updates += suggestion_updates
        st.session_state[SS_PROFILE] = profile
        st.success(t(lang, "intake.extract_done"))
        st.info(f"{t(lang, 'intake.updated_fields')}: {updates}")
        if suggestion_updates:
            st.info(t(lang, "ai.suggestions_done").format(suggestion_updates))
    except Exception as e:
        st.error(f"{t(lang, 'intake.extract_failed')}: {e}")

    # After extraction, move to first form step (Company)
    st.session_state[SS_STEP] = "company"
    st.rerun()


def _render_questions_step(
    profile: dict[str, Any],
    step: str,
    *,
    api_key: str,
    model: str,
    lang: str,
) -> None:
    # Render all questions (primary and advanced) for a given wizard step
    missing_step = missing_required_for_step(profile, step)
    if missing_step:
        st.info(f"{t(lang, 'step.missing_in_step')}: {', '.join(missing_step)}")

    primary, more = select_questions_for_step(profile, step)
    _render_question_list(profile, primary, step=step, lang=lang)

    with st.expander(t(lang, "ui.more_details"), expanded=False):
        _render_question_list(
            profile, more, step=step, lang=lang, advanced_section=True
        )

        # Optional: generate English variants for key fields (title + skills/tools)
        if step == "skills":
            st.divider()
            col_tr, col_tr_hint = st.columns([1, 3])
            with col_tr:
                do_translate = st.button(
                    t(lang, "ui.translate_to_en"),
                    disabled=not bool(api_key),
                    key="translate_to_en_btn",
                )
            with col_tr_hint:
                st.caption(t(lang, "ui.translate_hint"))
            if do_translate:
                _translate_fields_to_english(
                    profile, api_key=api_key, model=model, lang=lang
                )

        # ESCO integration (only on Skills step)
        if step == "skills" and st.session_state.get(SS_USE_ESCO, True):
            st.divider()
            _render_esco_sidebar(profile, lang=lang)

    st.divider()
    col_ai, col_hint = st.columns([1, 3])
    with col_ai:
        st.button(
            t(lang, "ui.ai_suggest"),
            on_click=partial(_generate_ai_followups, step, api_key, model, lang),
            disabled=not bool(api_key),
        )
    with col_hint:
        st.caption(t(lang, "ui.ai_hint"))

    # Auto-run follow-ups generation if enabled
    if st.session_state.get(SS_AUTO_AI) and bool(api_key):
        if step not in st.session_state[SS_AI_FOLLOWUPS]:
            _generate_ai_followups(step, api_key, model, lang, silent=True)

    # Render AI follow-up questions if any
    fu = st.session_state.get(SS_AI_FOLLOWUPS, {}).get(step) or []
    if fu:
        st.markdown(f"### {t(lang, 'ui.ai_followups_title')}")
        for i, q in enumerate(fu, start=1):
            _render_ai_followup(profile, q, step=step, idx=i, lang=lang)


def _render_question_list(
    profile: dict[str, Any],
    questions: list[Any],
    *,
    step: str,
    lang: str,
    advanced_section: bool = False,
) -> None:
    if not questions:
        st.caption(t(lang, "ui.empty"))
    for q in questions:
        rec = get_record(profile, q.path)
        prov = rec.get("provenance") if rec else None
        conf = rec.get("confidence") if rec else None
        suffix = ""
        if prov:
            suffix = f" · {t(lang, f'provenance.{prov}', prov)}"
            if conf is not None:
                suffix += f" ({conf:.2f})"
        label = question_label(q, lang) + (suffix if suffix else "")
        help_txt = question_help(q, lang)
        widget_key = f"w__{step}__{q.id}"
        # Render appropriate input widget based on type
        if q.input_type in {"text", "email"}:
            st.text_input(
                label,
                value=str(get_value(profile, q.path) or ""),
                help=help_txt or None,
                key=widget_key,
                on_change=partial(_on_widget_change, q.path, q.input_type, widget_key),
            )
        elif q.input_type == "textarea":
            st.text_area(
                label,
                value=str(get_value(profile, q.path) or ""),
                help=help_txt or None,
                key=widget_key,
                height=120,
                on_change=partial(_on_widget_change, q.path, q.input_type, widget_key),
            )
        elif q.input_type == "bool":
            st.checkbox(
                label,
                value=bool(get_value(profile, q.path) or False),
                help=help_txt or None,
                key=widget_key,
                on_change=partial(_on_widget_change, q.path, q.input_type, widget_key),
            )
        elif q.input_type == "number":
            raw = get_value(profile, q.path)
            st.text_input(
                label,
                value=str(raw) if raw not in {None, ""} else "",
                help=help_txt or None,
                key=widget_key,
                on_change=partial(_on_widget_change, q.path, q.input_type, widget_key),
            )
        elif q.input_type == "date":
            raw = get_value(profile, q.path)
            st.text_input(
                label,
                value=str(raw) if raw else "",
                help=(help_txt or "") + " (YYYY-MM-DD)",
                key=widget_key,
                on_change=partial(_on_widget_change, q.path, q.input_type, widget_key),
            )
        elif q.input_type == "select":
            values = list(q.options_values or ())
            opts = [""] + values

            def _fmt(v: str) -> str:
                if not v:
                    return "—"
                if q.options_group:
                    return option_label(lang, q.options_group, v)
                return v

            current = get_value(profile, q.path)
            current = current if current in values else ""
            st.selectbox(
                label,
                options=opts,
                index=opts.index(current),
                format_func=_fmt,
                help=help_txt or None,
                key=widget_key,
                on_change=partial(_on_widget_change, q.path, q.input_type, widget_key),
            )
        elif q.input_type == "list":
            raw_list = get_value(profile, q.path)
            st.text_area(
                label,
                value=list_to_multiline(
                    raw_list
                    if isinstance(raw_list, list)
                    else multiline_to_list(str(raw_list or ""))
                ),
                help=help_txt or None,
                key=widget_key,
                height=140,
                on_change=partial(_on_widget_change, q.path, q.input_type, widget_key),
            )
        else:
            st.text_input(
                label,
                value=str(get_value(profile, q.path) or ""),
                help=help_txt or None,
                key=widget_key,
                on_change=partial(_on_widget_change, q.path, "text", widget_key),
            )


def _queue_esco_skills(skills: list[str]) -> None:
    st.session_state[SS_PENDING_ESCO_HARD_REQ] = skills


def _apply_pending_esco_skills(profile: dict[str, Any], *, lang: str) -> None:
    pending = st.session_state.get(SS_PENDING_ESCO_HARD_REQ) or []
    if not pending:
        return
    cleaned = [str(s).strip() for s in pending if str(s).strip()]
    st.session_state[SS_PENDING_ESCO_HARD_REQ] = []
    if not cleaned:
        return
    # Update Hard Skills (required) both in widget and profile
    widget_key = "w__skills__hard_req"
    st.session_state[widget_key] = list_to_multiline(cleaned)
    set_field(
        profile,
        Keys.HARD_REQ,
        cleaned,
        provenance="ai_suggestion",
        confidence=0.7,
        evidence="esco_skill_apply",
    )
    st.session_state[SS_PROFILE] = profile
    st.success(t(lang, "esco.apply_success"))


def _on_widget_change(path: str, input_type: str, widget_key: str) -> None:
    profile: dict[str, Any] = st.session_state[SS_PROFILE]
    raw = st.session_state.get(widget_key)
    value: Any = raw
    if input_type in {"text", "textarea", "email"}:
        value = str(raw or "").strip()
        if not value:
            clear_field(profile, path)
            return
    elif input_type == "bool":
        value = bool(raw)
    elif input_type == "number":
        s = str(raw or "").strip()
        if not s:
            clear_field(profile, path)
            return
        try:
            value = int(s) if s.isdigit() else float(s)
        except Exception:
            value = s  # If numeric conversion fails, keep as string
    elif input_type == "date":
        s = str(raw or "").strip()
        if not s:
            clear_field(profile, path)
            return
        value = s  # assume valid date string
    elif input_type == "select":
        s = str(raw or "").strip()
        if not s:
            clear_field(profile, path)
            return
        value = s
    elif input_type == "list":
        s = str(raw or "")
        value = multiline_to_list(s)
        if not value:
            clear_field(profile, path)
            return
    set_field(
        profile, path, value, provenance="user", confidence=1.0, evidence="user_input"
    )
    st.session_state[SS_PROFILE] = profile


def _generate_ai_followups(
    step: str, api_key: str, model: str, lang: str, silent: bool = False
) -> None:
    profile: dict[str, Any] = st.session_state[SS_PROFILE]
    if not api_key:
        return
    primary, more = select_questions_for_step(profile, step)
    miss_req = missing_required_for_step(profile, step)
    miss_opt = iter_missing_optional(profile, list(primary) + list(more))
    if not miss_req and not miss_opt:
        st.session_state[SS_AI_FOLLOWUPS][step] = []
        return
    context = {
        "company": get_value(profile, Keys.COMPANY_NAME),
        "job_title": get_value(profile, Keys.POSITION_TITLE),
        "step": step,
    }
    try:
        client = LLMClient(api_key=api_key, model=model)
        raw = client.text(
            followup_user_prompt(
                miss_req, miss_opt[:20], context=json.dumps(context, ensure_ascii=False)
            ),
            instructions=FOLLOWUP_INSTRUCTIONS,
            max_output_tokens=900,
        )
        payload = safe_parse_json(raw)
        questions = payload.get("questions") or []
        cleaned: list[dict[str, Any]] = []
        for q in questions:
            if not isinstance(q, dict):
                continue
            path = q.get("target_path")
            if path not in ALL_FIELDS:
                continue
            answer_type = q.get("answer_type") or "text"
            question_de = q.get("question_de") or ""
            question_en = q.get("question_en") or ""
            opts = q.get("options")
            if isinstance(opts, list):
                opts = [str(x) for x in opts if str(x).strip()]
            else:
                opts = None
            cleaned.append(
                {
                    "target_path": path,
                    "answer_type": str(answer_type),
                    "question_de": str(question_de),
                    "question_en": str(question_en),
                    "options": opts,
                }
            )
        st.session_state[SS_AI_FOLLOWUPS][step] = cleaned[:7]
        if not silent:
            st.success(f"{t(lang, 'ai.followups_done')}: {len(cleaned[:7])}")
    except Exception as e:
        if not silent:
            st.error(f"{t(lang, 'ai.followups_failed')}: {e}")


def _render_ai_followup(
    profile: dict[str, Any], q: dict[str, Any], *, step: str, idx: int, lang: str
) -> None:
    path = q.get("target_path")
    if path not in ALL_FIELDS:
        return
    question = q.get("question_de") if lang == LANG_DE else q.get("question_en")
    question = question or str(path)
    answer_type = q.get("answer_type") or "text"
    widget_key = f"fu__{step}__{idx}__{path}"
    if answer_type == "bool":
        st.checkbox(
            question,
            value=bool(get_value(profile, path) or False),
            key=widget_key,
            on_change=partial(_on_widget_change, path, "bool", widget_key),
        )
    elif answer_type == "list":
        raw_list = get_value(profile, path)
        st.text_area(
            question,
            value=list_to_multiline(
                raw_list
                if isinstance(raw_list, list)
                else multiline_to_list(str(raw_list or ""))
            ),
            height=120,
            key=widget_key,
            on_change=partial(_on_widget_change, path, "list", widget_key),
        )
    elif (
        answer_type == "select"
        and isinstance(q.get("options"), list)
        and q.get("options")
    ):
        opts = [""] + list(q["options"])
        st.selectbox(
            question,
            options=opts,
            key=widget_key,
            on_change=partial(_on_widget_change, path, "select", widget_key),
        )
    else:
        st.text_input(
            question,
            value=str(get_value(profile, path) or ""),
            key=widget_key,
            on_change=partial(_on_widget_change, path, "text", widget_key),
        )


def _render_esco_sidebar(profile: dict[str, Any], *, lang: str) -> None:
    st.markdown(f"#### {t(lang, 'esco.title')}")
    default_query = str(get_value(profile, Keys.POSITION_TITLE) or "").strip()
    query = st.text_input(t(lang, "esco.query"), value=default_query, key="esco_query")
    # Detect language of query (simple heuristic: presence of German-specific characters)
    lowered = query.lower()
    query_lang = "de" if any(ch in lowered for ch in ("ä", "ö", "ü", "ß")) else "en"
    col1, col2 = st.columns([1, 4])
    with col1:
        do_search = st.button(t(lang, "ui.esco_search"), key="esco_search_btn")
    with col2:
        st.caption(
            f"{t(lang, 'esco.caption')} · {t(lang, 'esco.lang_hint').format(query_lang)}"
        )
    if do_search:
        try:
            results = search_occupations(query, language=query_lang, limit=10)
            st.session_state["esco_results"] = results
        except ESCOError as e:
            st.error(f"{t(lang, 'esco.error')}: {e}")
            st.session_state["esco_results"] = []
    # Display occupation results and skill suggestions
    results = st.session_state.get("esco_results") or []
    if results:
        labels = [r["label"] for r in results]
        choice = st.selectbox(
            t(lang, "ui.esco_pick"),
            options=list(range(len(labels))),
            format_func=lambda i: labels[i],
            key="esco_pick",
        )
        picked = results[choice] if choice is not None else None
        if picked:
            # Store chosen occupation in profile (URI and label)
            set_field(
                profile,
                Keys.ESCO_OCCUPATION_URI,
                picked["uri"],
                provenance="user",
                confidence=1.0,
                evidence="esco_pick",
            )
            set_field(
                profile,
                Keys.ESCO_OCCUPATION_LABEL,
                picked["label"],
                provenance="user",
                confidence=1.0,
                evidence="esco_pick",
            )
            if st.button(t(lang, "ui.esco_apply_skills"), key="esco_apply_btn"):
                try:
                    skills = occupation_related_skills(
                        picked["uri"], language=query_lang
                    )
                    st.session_state["esco_skills"] = skills
                    set_field(
                        profile,
                        Keys.ESCO_SUGGESTED_SKILLS,
                        skills,
                        provenance="ai_suggestion",
                        confidence=0.8,
                        evidence="esco_skill_lookup",
                    )
                except ESCOError as e:
                    st.error(f"{t(lang, 'esco.error')}: {e}")
                    st.session_state["esco_skills"] = []
    skills = st.session_state.get("esco_skills") or []
    if skills:
        selected = st.multiselect(
            t(lang, "esco.skills_select"),
            options=skills,
            default=skills[:8],
            key="esco_skills_select",
        )
        st.button(
            t(lang, "ui.esco_insert_hard"),
            key="esco_insert_btn",
            disabled=not selected,
            on_click=_queue_esco_skills,
            args=(selected,),
            type="primary",
        )
        if selected:
            st.caption(t(lang, "esco.apply_hint"))
    # After applying, if any pending skills are queued, integrate into profile
    _apply_pending_esco_skills(profile, lang=lang)


def _translate_fields_to_english(
    profile: dict[str, Any], *, api_key: str, model: str, lang: str
) -> None:
    if not api_key:
        return
    # Prepare the payload with current German text for translation
    payload = {
        "position.job_title": get_value(profile, Keys.POSITION_TITLE),
        "requirements.hard_skills_required": get_value(profile, Keys.HARD_REQ),
        "requirements.soft_skills_required": get_value(profile, Keys.SOFT_REQ),
        "requirements.tools_and_technologies": get_value(profile, Keys.TOOLS),
    }
    try:
        client = LLMClient(api_key=api_key, model=model)
        raw = client.text(
            translate_user_prompt(payload),
            instructions=TRANSLATE_INSTRUCTIONS,
            max_output_tokens=800,
        )
        data = safe_parse_json(raw)
        updates = 0
        if isinstance(data, dict):
            for path in [
                Keys.POSITION_TITLE_EN,
                Keys.HARD_REQ_EN,
                Keys.SOFT_REQ_EN,
                Keys.TOOLS_EN,
            ]:
                val = data.get(path)
                if val is None:
                    continue
                # Convert newline-separated strings to list for skills/tools fields
                if path in {
                    Keys.HARD_REQ_EN,
                    Keys.SOFT_REQ_EN,
                    Keys.TOOLS_EN,
                } and isinstance(val, str):
                    val = multiline_to_list(val)
                set_field(
                    profile,
                    path,
                    val,
                    provenance="ai_suggestion",
                    confidence=0.75,
                    evidence="translation",
                )
                updates += 1
        st.session_state[SS_PROFILE] = profile
        st.success(f"{t(lang, 'ui.translate_done')}: {updates}")
    except Exception as e:
        st.error(f"{t(lang, 'ui.translate_failed')}: {e}")


def _render_review(
    profile: dict[str, Any], *, lang: str, api_key: str, model: str, theme: str
) -> None:
    st.markdown(f"## {t(lang, 'review.title')}")
    st.caption(t(lang, "review.edit_hint"))
    generated_md = render_job_ad_markdown(profile, lang)
    if not st.session_state.get(SS_JOB_AD_DRAFT):
        st.session_state[SS_JOB_AD_DRAFT] = generated_md
    md = st.text_area(
        t(lang, "review.job_ad"),
        value=st.session_state[SS_JOB_AD_DRAFT],
        height=450,
        key=SS_JOB_AD_DRAFT,
    )

    st.divider()
    _render_salary_prediction(
        profile, lang=lang, api_key=api_key, model=model, theme=theme
    )

    col1, col2, col3 = st.columns(3)
    with col1:
        st.download_button(
            t(lang, "review.download_json"),
            data=to_json(profile),
            file_name="need_analysis_profile.json",
            mime="application/json",
        )
    with col2:
        st.download_button(
            t(lang, "review.download_md"),
            data=md,
            file_name="job_ad.md",
            mime="text/markdown",
        )
    with col3:
        docx_bytes = export_docx_bytes(profile, lang, markdown_override=md)
        st.download_button(
            t(lang, "review.download_docx"),
            data=docx_bytes,
            file_name="job_ad.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
    st.divider()
    st.markdown(f"### {t(lang, 'review.profile_json')}")
    st.code(to_json(profile), language="json")
    extracted = []
    suggested = []
    for path, rec in profile.get("fields", {}).items():
        prov = rec.get("provenance")
        if prov == "extracted":
            extracted.append(path)
        elif prov == "ai_suggestion":
            suggested.append(path)
    if extracted or suggested:
        st.markdown(f"### {t(lang, 'review.provenance_title')}")
        if extracted:
            st.write(
                f"{t(lang, 'review.provenance_extracted')}: ", ", ".join(extracted)
            )
        if suggested:
            st.write(f"{t(lang, 'review.provenance_ai')}: ", ", ".join(suggested))
