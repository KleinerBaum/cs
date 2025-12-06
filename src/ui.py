from __future__ import annotations

import base64
import json
import os
from functools import lru_cache, partial
from pathlib import Path
from string import Template
from typing import Any, cast

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
    FOLLOWUP_INSTRUCTIONS,
    TRANSLATE_INSTRUCTIONS,
    LLMClient,
    extraction_user_prompt,
    followup_user_prompt,
    safe_parse_json,
    translate_user_prompt,
)
from .profile import (
    clear_field,
    get_record,
    get_value,
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
    question_help,
    question_label,
    select_questions_for_step,
)
from .rendering import export_docx_bytes, render_job_ad_markdown
from .settings import APP_NAME, MAX_SOURCE_TEXT_CHARS
from .utils import (
    clamp_str,
    extract_emails,
    extract_urls,
    list_to_multiline,
    multiline_to_list,
)


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

THEME_LIGHT = "light"
THEME_DARK = "dark"

BACKGROUND_IMAGE_PATH = Path("images/AdobeStock_506577005.jpeg")
LOGO_IMAGE_PATH = Path("images/animation_pulse_Default_7kigl22lw.gif")


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


def _init_state() -> None:
    if SS_STEP not in st.session_state:
        st.session_state[SS_STEP] = "intake"
    if SS_PROFILE not in st.session_state:
        st.session_state[SS_PROFILE] = new_profile(ui_language=LANG_DE)
    if SS_SOURCE_DOC not in st.session_state:
        st.session_state[SS_SOURCE_DOC] = None
    if SS_AI_FOLLOWUPS not in st.session_state:
        st.session_state[SS_AI_FOLLOWUPS] = {}
    if SS_MODEL not in st.session_state:
        st.session_state[SS_MODEL] = "gpt-5-mini"
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


def _reset_session() -> None:
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
    ]:
        st.session_state.pop(k, None)
    st.rerun()


def _get_lang() -> str:
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


def _apply_theme(theme: str) -> None:
    css_light = """
    :root {
        --cs-bg: #ffffff;
        --cs-text: #111827;
        --cs-surface: #f8fafc;
        --cs-primary: #2563eb;
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
    .stButton>button {
        color: #ffffff;
        background: var(--cs-primary);
        border-color: var(--cs-primary);
    }
    """

    css_dark = """
    :root {
        --cs-bg: #111827;
        --cs-text: #e5e7eb;
        --cs-surface: #1f2937;
        --cs-primary: #60a5fa;
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
    .stMarkdown, .stText, .stCaption, label, p, h1, h2, h3, h4, h5, h6 {
        color: var(--cs-text);
    }
    .stButton>button {
        color: #0b1021;
        background: var(--cs-primary);
        border-color: var(--cs-primary);
    }
    textarea, input, select {
        background: #111827;
        color: #e5e7eb;
        border-color: #374151;
    }
    """

    css = css_dark if theme == THEME_DARK else css_light
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
    st.markdown(
        f"<script>document.body.dataset.theme='{theme}';</script>",
        unsafe_allow_html=True,
    )


@lru_cache(maxsize=4)
def _load_base64_asset(path: str) -> str | None:
    try:
        data = Path(path).read_bytes()
    except OSError:
        return None

    return base64.b64encode(data).decode("utf-8")


def _apply_background(image_path: Path) -> None:
    encoded = _load_base64_asset(str(image_path))
    if not encoded:
        return

    css_template = Template(
        """
        .stApp {
            background-image: linear-gradient(180deg, rgba(17, 24, 39, 0.60) 0%, rgba(17, 24, 39, 0.35) 100%),
                url('data:image/jpeg;base64,$encoded');
            background-size: cover;
            background-position: center;
            background-repeat: no-repeat;
        }

        .block-container {
            background: rgba(255, 255, 255, 0.92);
            border-radius: 18px;
            padding: 26px 30px;
            box-shadow: 0 24px 60px rgba(0, 0, 0, 0.18);
            backdrop-filter: blur(4px);
            border: 1px solid rgba(255, 255, 255, 0.35);
            margin-top: 18px;
        }

        [data-theme="dark"] .block-container {
            background: rgba(17, 24, 39, 0.86);
            border-color: rgba(255, 255, 255, 0.12);
        }
        """
    )
    css = css_template.safe_substitute(encoded=encoded)

    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


def _render_branding(logo_path: Path) -> None:
    encoded = _load_base64_asset(str(logo_path))
    if not encoded:
        return

    st.markdown(
        Template(
            """
            <style>
            .cs-logo-container {
                position: fixed;
                top: 1.4rem;
                right: 1.6rem;
                padding: 0.85rem 1.1rem;
                border-radius: 1rem;
                background: rgba(255, 255, 255, 0.9);
                box-shadow: 0 16px 40px rgba(0, 0, 0, 0.22);
                backdrop-filter: blur(6px);
                border: 1px solid rgba(255, 255, 255, 0.6);
                z-index: 999;
            }

            [data-theme="dark"] .cs-logo-container {
                background: rgba(26, 32, 44, 0.92);
                border-color: rgba(255, 255, 255, 0.2);
            }

            .cs-logo-container img {
                display: block;
                max-height: 72px;
                width: auto;
            }
            </style>
            <div class="cs-logo-container">
                <img src="data:image/gif;base64,$logo" alt="Animated Need Analysis Wizard logo" />
            </div>
            """
        ).safe_substitute(logo=encoded),
        unsafe_allow_html=True,
    )


def _guess_text_language(text: str, fallback: str) -> str:
    """Return a rough language guess ("de" or "en") for ESCO queries."""

    lowered = text.lower()
    if any(ch in lowered for ch in ("ä", "ö", "ü", "ß")):
        return LANG_DE

    german_markers = (
        " für ",
        " mit ",
        " und ",
        "kenntnisse",
        "erfahrung",
    )
    if any(marker in lowered for marker in german_markers):
        return LANG_DE

    return LANG_DE if fallback == LANG_DE else LANG_EN


def run_app() -> None:
    st.set_page_config(page_title="Need Analysis Wizard", page_icon="🧭", layout="wide")
    _init_state()

    lang = _get_lang()
    profile: dict[str, Any] = st.session_state[SS_PROFILE]

    api_key = _resolve_api_key()
    if not api_key:
        st.error(t(lang, "errors.no_api_key"))
        st.stop()
    api_key = cast(str, api_key)

    with st.sidebar:
        st.markdown(f"### {t(lang, 'sidebar.title')}")
        ui_lang = st.selectbox(
            t(lang, "sidebar.language"),
            options=[LANG_DE, LANG_EN],
            format_func=lambda x: "Deutsch" if x == LANG_DE else "English",
            key="ui_lang",
        )
        profile.get("meta", {})["ui_language"] = ui_lang

        st.session_state[SS_THEME] = st.selectbox(
            t(lang, "sidebar.theme"),
            options=[THEME_LIGHT, THEME_DARK],
            format_func=lambda x: t(lang, f"theme.{x}"),
            key=SS_THEME,
        )

        model = st.text_input(
            t(lang, "sidebar.model"), value=st.session_state[SS_MODEL], key=SS_MODEL
        )
        st.session_state[SS_USE_ESCO] = st.checkbox(
            t(lang, "sidebar.use_esco"), value=st.session_state[SS_USE_ESCO]
        )
        st.session_state[SS_AUTO_AI] = st.checkbox(
            t(lang, "sidebar.auto_ai"), value=st.session_state[SS_AUTO_AI]
        )

        if st.button(t(lang, "sidebar.reset")):
            _reset_session()

    _apply_theme(st.session_state.get(SS_THEME, THEME_LIGHT))
    _apply_background(BACKGROUND_IMAGE_PATH)
    _render_branding(LOGO_IMAGE_PATH)

    st.title(APP_NAME)
    st.caption(t(lang, "app.tagline"))

    missing = missing_required(profile)
    progress = 1.0 - (len(missing) / max(1, len(REQUIRED_FIELDS)))
    st.progress(progress)

    if missing:
        st.warning(f"{t(lang, 'progress.missing_required')}: {', '.join(missing)}")
    else:
        st.success(t(lang, "progress.ready"))

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

    if current_step == "intake":
        _render_intake(profile, api_key=api_key, model=model, lang=lang)
        return
    if current_step == "review":
        _render_review(profile, lang=lang)
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

    st.session_state[SS_SOURCE_DOC] = {
        "source_type": source_doc.source_type,
        "name": source_doc.name,
        "text": source_doc.text,
        "meta": source_doc.meta,
    }

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
        st.warning(t(lang, "intake.no_openai_key"))
        st.session_state[SS_PROFILE] = profile
        st.session_state[SS_STEP] = "company"
        st.rerun()
        return

    try:
        client = LLMClient(api_key=api_key, model=model)
        text = source_doc.text[:MAX_SOURCE_TEXT_CHARS]
        raw = client.text(
            extraction_user_prompt(text),
            instructions=EXTRACTION_INSTRUCTIONS,
            temperature=0.0,
            max_output_tokens=1800,
        )
        payload = safe_parse_json(raw)

        detected = payload.get("detected_language")
        if isinstance(detected, str):
            update_source_language(profile, detected)

        fields = payload.get("fields") or []
        updated = 0
        for item in fields:
            if not isinstance(item, dict):
                continue
            path = item.get("path")
            if path not in ALL_FIELDS:
                continue
            value = item.get("value")
            conf = item.get("confidence")
            evidence = item.get("evidence")

            if value is None and path in {
                Keys.BENEFITS_ITEMS,
                Keys.RESPONSIBILITIES,
                Keys.HARD_REQ,
                Keys.HARD_OPT,
                Keys.SOFT_REQ,
                Keys.LANG_REQ,
                Keys.TOOLS,
                Keys.MUST_NOT,
                Keys.PROCESS_STAGES,
            }:
                value = []
            if isinstance(value, str) and not value.strip():
                value = None
            if path in {
                Keys.BENEFITS_ITEMS,
                Keys.RESPONSIBILITIES,
                Keys.HARD_REQ,
                Keys.HARD_OPT,
                Keys.SOFT_REQ,
                Keys.LANG_REQ,
                Keys.TOOLS,
                Keys.MUST_NOT,
                Keys.PROCESS_STAGES,
            } and isinstance(value, str):
                value = multiline_to_list(value)

            conf_f = float(conf) if isinstance(conf, (int, float)) else None
            evidence = clamp_str(evidence, 220) if isinstance(evidence, str) else None

            if upsert_field(
                profile,
                path,
                value,
                provenance="extracted",
                confidence=conf_f,
                evidence=evidence,
                prefer_existing_user=True,
            ):
                updated += 1

        st.success(
            f"{t(lang, 'intake.extract_done')} {t(lang, 'intake.updated_fields')}: {updated}"
        )
        st.session_state[SS_PROFILE] = profile
        st.session_state[SS_STEP] = "company"
        st.rerun()
    except Exception as e:
        st.error(f"{t(lang, 'intake.extract_failed')}: {e}")
        st.session_state[SS_PROFILE] = profile


def _render_questions_step(
    profile: dict[str, Any], *, step: str, api_key: str, model: str, lang: str
) -> None:
    st.markdown(f"## {t(lang, _STEP_LABEL_KEYS.get(step, step))}")

    if step == "skills":
        _apply_pending_esco_skills(profile, lang=lang)

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

        # ESCO integration best fits in skills step
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

    if st.session_state.get(SS_AUTO_AI) and bool(api_key):
        if step not in st.session_state[SS_AI_FOLLOWUPS]:
            _generate_ai_followups(step, api_key, model, lang, silent=True)

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
            value = s
    elif input_type == "date":
        s = str(raw or "").strip()
        if not s:
            clear_field(profile, path)
            return
        value = s
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
            temperature=0.2,
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

    query_lang = _guess_text_language(query, LANG_DE if lang == LANG_DE else LANG_EN)

    col1, col2 = st.columns([1, 2])
    with col1:
        do_search = st.button(t(lang, "ui.esco_search"), key="esco_search_btn")
    with col2:
        st.caption(
            f"{t(lang, 'esco.caption')} · {t(lang, 'esco.lang_hint').format(query_lang)}"
        )

    if do_search and query:
        try:
            results = search_occupations(query, language=query_lang, limit=10)
            st.session_state["esco_results"] = results
        except ESCOError as e:
            st.error(f"{t(lang, 'esco.error')}: {e}")
            st.session_state["esco_results"] = []

    results = st.session_state.get("esco_results") or []
    if results:
        labels = [r["label"] for r in results]
        choice = st.selectbox(
            t(lang, "ui.esco_pick"),
            options=list(range(len(labels))),
            format_func=lambda i: labels[i],
            key="esco_pick",
        )
        picked = results[int(choice)]
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
                    picked["uri"], language=query_lang, max_items=25
                )
                st.session_state["esco_skills"] = skills
                set_field(
                    profile,
                    Keys.ESCO_SUGGESTED_SKILLS,
                    skills,
                    provenance="ai_suggestion",
                    confidence=0.7,
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


def _translate_fields_to_english(
    profile: dict[str, Any], *, api_key: str, model: str, lang: str
) -> None:
    if not api_key:
        return

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
            temperature=0.1,
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


def _render_review(profile: dict[str, Any], *, lang: str) -> None:
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
