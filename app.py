"""Streamlit entrypoint for the multi-step Need-Analysis wizard."""

from __future__ import annotations

import streamlit as st
from core.extractor import run_extraction
from core.schemas import RawInput
from streamlit.runtime.uploaded_file_manager import UploadedFile

from src.ingest import (
    IngestError,
    SourceDocument,
    extract_text_from_upload,
    fetch_text_from_url,
    source_from_text,
)
from state import AppState, get_app_state, set_app_state


def _get_language() -> str:
    lang = st.session_state.get("lang", "de")
    st.session_state["lang"] = lang
    return lang


def _ingest_source(
    *, url: str, upload: UploadedFile | None, pasted_text: str
) -> SourceDocument:
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
        raise IngestError(
            "Bitte eine Quelle angeben (URL, Upload oder Text). / "
            "Please provide a source (URL, upload, or pasted text)."
        )
    if provided_sources > 1:
        raise IngestError(
            "Nur eine Quelle auf einmal verwenden (URL, Upload oder Text). / "
            "Please use only one source at a time (URL, upload, or pasted text)."
        )

    if upload is not None:
        return extract_text_from_upload(upload)
    if url.strip():
        return fetch_text_from_url(url.strip())
    return source_from_text(pasted_text)


def _autofill_from_source(state: AppState, source_doc: SourceDocument) -> list[str]:
    extraction = run_extraction(RawInput(text=source_doc.text, source_type="text"))
    updated_fields: list[str] = []

    if extraction.company and not state.profile.company_name:
        state.profile.company_name = extraction.company
        updated_fields.append("Company / Unternehmen")

    if extraction.job_title and not state.role.job_title:
        state.role.job_title = extraction.job_title
        updated_fields.append("Job Title / Stellenbezeichnung")

    if extraction.seniority and not state.role.seniority:
        state.role.seniority = extraction.seniority
        updated_fields.append("Seniority / Seniorität")

    if extraction.location and not state.profile.primary_city:
        state.profile.primary_city = extraction.location
        updated_fields.append("Location / Standort")

    if extraction.employment_type and not state.profile.employment_type:
        state.profile.employment_type = extraction.employment_type
        updated_fields.append("Employment Type / Beschäftigungsart")

    if extraction.responsibilities and not state.skills.tasks:
        state.skills.tasks = extraction.responsibilities
        updated_fields.append("Responsibilities / Aufgaben")

    if extraction.must_have_skills and not state.skills.must_have:
        state.skills.must_have = extraction.must_have_skills
        updated_fields.append("Must-have Skills / Muss-Fähigkeiten")

    return updated_fields


def main() -> None:
    """Render the landing page and initialize state."""

    st.set_page_config(page_title="Need Analysis Wizard", page_icon="🧭", layout="wide")
    _get_language()

    state = st.session_state.get("app_state")
    if not isinstance(state, AppState):
        state = get_app_state()
        set_app_state(state)

    st.title("Need-Analysis Wizard / Bedarfsanalyse")
    st.write(
        "Führe Schritt für Schritt durch Profil, Rolle, Skills, Compensation, Forecast und Zusammenfassung. / "
        "Step through profile, role, skills, compensation, forecast, and summary."
    )

    st.info(
        "Alle Eingaben werden zwischengespeichert, sodass du jederzeit fortsetzen kannst. / "
        "All inputs are stored in the session so you can continue later.",
        icon="💾",
    )

    col1, col2 = st.columns([2, 1])
    with col1:
        st.subheader("Schnellstart / Quick start")
        st.markdown(
            "- Nutze die Navigation links, um durch die einzelnen Seiten zu springen. / "
            "Use the left navigation to move between pages.\n"
            "- Pflichtfelder sind mit einem Stern gekennzeichnet. / Required fields carry an asterisk.\n"
            "- LLM-Buttons füllen nur die vorgesehenen Felder aus. / LLM buttons only update the target fields."
        )
    with col2:
        st.subheader("Sprache / Language")
        lang_choice = st.radio("Bitte auswählen / Please choose", ("de", "en"), index=0)
        st.session_state["lang"] = lang_choice

    st.divider()
    st.subheader("Vakanzdaten importieren / Import vacancy data")
    st.caption(
        "URL einfügen, PDF/DOCX hochladen oder den Text direkt einfügen, um Felder "
        "vorzubelegen. / Paste a URL, upload a PDF/DOCX, or drop the text to prefill "
        "the wizard."
    )

    intake_col1, intake_col2 = st.columns([2, 1])
    with intake_col1:
        source_url = st.text_input("Job-URL / Job ad URL", placeholder="https://…")
        upload = st.file_uploader(
            "PDF oder DOCX hochladen / Upload PDF or DOCX", type=["pdf", "docx"]
        )
        pasted_text = st.text_area(
            "Text einfügen / Paste job description", height=150, placeholder="…"
        )
    with intake_col2:
        st.info(
            "Bitte nur eine Quelle zurzeit verwenden. / Please use only one source "
            "at a time.",
            icon="ℹ️",
        )
        process_intake = st.button(
            "Autofill starten / Start autofill",
            type="primary",
            use_container_width=True,
        )

    if process_intake:
        try:
            source_doc = _ingest_source(
                url=source_url, upload=upload, pasted_text=pasted_text
            )
        except IngestError as exc:
            st.error(str(exc))
        else:
            st.session_state["source_preview"] = source_doc.text
            updated = _autofill_from_source(state, source_doc)
            set_app_state(state)

            if updated:
                st.success(
                    "Eingaben wurden vorbefüllt: "
                    + ", ".join(updated)
                    + ". / Prefilled fields: "
                    + ", ".join(updated)
                    + "."
                )
            else:
                st.warning(
                    "Quelle geladen, aber keine neuen Felder erkannt. / Source "
                    "loaded, but no new fields detected."
                )

            st.text_area(
                "Quelle (gekürzt) / Source preview (truncated)",
                value=source_doc.text[:2000],
                height=200,
            )

    st.divider()
    st.write("Bereit? / Ready?")
    if st.button("Zum Profil starten / Go to Profile", type="primary"):
        st.switch_page("pages/01_Profile.py")

    st.caption(
        "Tipp: Du kannst jederzeit zur Zusammenfassung springen, um den aktuellen Status zu prüfen. / "
        "Tip: Jump to the summary page at any time to review progress."
    )


if __name__ == "__main__":
    main()
