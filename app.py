# app.py - Streamlit job description wizard
from __future__ import annotations

import os
import time

import openai
import streamlit as st

from esco_utils import fetch_essential_skills
from src.keys import Keys, REQUIRED_FIELDS


MODEL_NAME = "gpt-4o-mini"

STEP_ORDER: tuple[int, ...] = (1, 2, 3, 4, 5, 6, 7)
REVIEW_STEP = STEP_ORDER[-1]

STEP_REQUIRED_FIELDS: dict[int, tuple[str, ...]] = {
    1: (Keys.COMPANY_NAME, Keys.COMPANY_CONTACT_EMAIL),
    2: (Keys.POSITION_TITLE, Keys.POSITION_SENIORITY),
    3: (
        Keys.LOCATION_CITY,
        Keys.EMPLOYMENT_TYPE,
        Keys.EMPLOYMENT_CONTRACT,
        Keys.EMPLOYMENT_START,
    ),
    4: (Keys.BENEFITS_ITEMS,),
    5: (
        Keys.RESPONSIBILITIES,
        Keys.HARD_REQ,
        Keys.SOFT_REQ,
        Keys.LANG_REQ,
        Keys.TOOLS,
    ),
    6: (),
}


def _init_session_state() -> None:
    st.session_state.setdefault("current_step", STEP_ORDER[0])


def _read_value(key: str) -> str:
    value = st.session_state.get(key, "")
    return str(value) if value is not None else ""


def _parse_multiline(text: str) -> list[str]:
    if not text:
        return []
    if "\n" in text:
        return [line.strip() for line in text.splitlines() if line.strip()]
    if "," in text:
        return [item.strip() for item in text.split(",") if item.strip()]
    return [text.strip()] if text.strip() else []


def _missing_fields(step: int) -> list[str]:
    missing: list[str] = []
    for key in STEP_REQUIRED_FIELDS.get(step, ()):  # type: ignore[arg-type]
        if not _read_value(key).strip():
            missing.append(key)
    return missing


def _humanize_field(key: str) -> str:
    labels = {
        Keys.COMPANY_NAME: "Firmenname / Company name",
        Keys.COMPANY_CONTACT_EMAIL: "Kontakt E-Mail / Contact email",
        Keys.POSITION_TITLE: "Stellentitel / Job title",
        Keys.POSITION_SENIORITY: "Senioritätslevel / Seniority",
        Keys.LOCATION_CITY: "Dienstort / Work location",
        Keys.EMPLOYMENT_TYPE: "Anstellungsart / Employment type",
        Keys.EMPLOYMENT_CONTRACT: "Vertragsart / Contract type",
        Keys.EMPLOYMENT_START: "Startdatum / Start date",
        Keys.BENEFITS_ITEMS: "Benefits",
        Keys.RESPONSIBILITIES: "Aufgaben / Responsibilities",
        Keys.HARD_REQ: "Must-have Hard Skills",
        Keys.SOFT_REQ: "Soft Skills",
        Keys.LANG_REQ: "Sprachen / Languages",
        Keys.TOOLS: "Tools",
    }
    return labels.get(key, key)


def _render_navigation(step: int, prev_clicked: bool, next_clicked: bool) -> None:
    if prev_clicked and step > STEP_ORDER[0]:
        st.session_state["current_step"] = STEP_ORDER[STEP_ORDER.index(step) - 1]
        st.session_state.setdefault("navigation_message", "")
        st.session_state["navigation_message"] = "⟨ Zurück / Back"
        return

    if next_clicked:
        missing = _missing_fields(step)
        if missing:
            labels = ", ".join(_humanize_field(key) for key in missing)
            st.error(
                f"Bitte füllen Sie die Pflichtfelder aus / Please complete required fields: {labels}."
            )
            return
        st.session_state["current_step"] = STEP_ORDER[
            min(STEP_ORDER.index(step) + 1, len(STEP_ORDER) - 1)
        ]
        st.session_state.setdefault("navigation_message", "")
        st.session_state["navigation_message"] = "Weiter / Next"


def _company_form(step: int) -> None:
    with st.form(key="company_form"):
        st.header("Unternehmen / Company")
        st.text_input(
            "Firmenname (Pflicht) / Company name (required)", key=Keys.COMPANY_NAME
        )
        st.text_input("Webseite / Website", key=Keys.COMPANY_WEBSITE)
        st.text_input("Branche / Industry", key=Keys.COMPANY_INDUSTRY)
        st.text_input("Unternehmensgröße / Company size", key=Keys.COMPANY_SIZE)
        st.text_input("Hauptsitz / Headquarters", key=Keys.COMPANY_HQ)
        st.text_area("Firmenbeschreibung / Company description", key=Keys.COMPANY_DESC)
        st.text_input(
            "Ansprechperson (Name) / Contact person (name)",
            key=Keys.COMPANY_CONTACT_NAME,
        )
        st.text_input(
            "Ansprechperson (E-Mail, Pflicht) / Contact email (required)",
            key=Keys.COMPANY_CONTACT_EMAIL,
        )

        prev_clicked = False
        next_clicked = st.form_submit_button("Weiter > / Next")
        _render_navigation(step, prev_clicked, next_clicked)


def _position_form(step: int) -> None:
    with st.form(key="position_form"):
        st.header("Position & Team / Role & Team")
        st.text_input(
            "Stellentitel (Englisch, Pflicht) / Job title (English, required)",
            key=Keys.POSITION_TITLE,
        )
        st.text_input("Job-Familie / Job family", key=Keys.POSITION_FAMILY)
        st.text_input(
            "Senioritätslevel (Pflicht) / Seniority (required)",
            key=Keys.POSITION_SENIORITY,
        )
        st.text_area(
            "Rollenbeschreibung / Role summary",
            key=Keys.POSITION_SUMMARY,
        )
        st.text_input(
            "Vorgesetzte Position / Reports to",
            key=Keys.POSITION_REPORTS_TO_TITLE,
        )
        st.text_input(
            "Führungsverantwortung / People management",
            key=Keys.POSITION_PEOPLE_MGMT,
        )
        st.text_input(
            "Direkte Reports / Direct reports",
            key=Keys.POSITION_DIRECT_REPORTS,
        )
        st.text_input("Abteilung / Department", key=Keys.TEAM_DEPT)
        st.text_input("Teamname / Team name", key=Keys.TEAM_NAME)
        st.text_input(
            "Reporting Line / Reporting line",
            key=Keys.TEAM_REPORTING_LINE,
        )
        st.text_input(
            "Teamgröße aktuell / Current team size", key=Keys.TEAM_HEADCOUNT_CURRENT
        )
        st.text_input(
            "Teamgröße geplant / Planned team size", key=Keys.TEAM_HEADCOUNT_TARGET
        )
        st.text_input("Tools im Team / Collaboration tools", key=Keys.TEAM_TOOLS)

        prev_clicked = st.form_submit_button("< Zurück / Back")
        next_clicked = st.form_submit_button("Weiter > / Next")
        _render_navigation(step, prev_clicked, next_clicked)


def _location_form(step: int) -> None:
    with st.form(key="location_form"):
        st.header("Standort & Anstellung / Location & Employment")
        st.text_input(
            "Arbeitsmodell / Work model",
            key=Keys.LOCATION_WORK_POLICY,
        )
        st.text_input(
            "Dienstort (Pflicht) / Work location (required)", key=Keys.LOCATION_CITY
        )
        st.text_input(
            "Remote-Anteil / Remote scope",
            key=Keys.LOCATION_REMOTE_SCOPE,
        )
        st.text_input("Zeitzone / Time zone", key=Keys.LOCATION_TZ)
        st.text_input(
            "Reisebereitschaft / Travel requirement",
            key=Keys.LOCATION_TRAVEL_REQUIRED,
        )
        st.text_input(
            "Reiseanteil (%) / Travel percentage (%)",
            key=Keys.LOCATION_TRAVEL_PCT,
        )
        st.text_input(
            "Anstellungsart (Pflicht) / Employment type (required)",
            key=Keys.EMPLOYMENT_TYPE,
        )
        st.text_input(
            "Vertragsart (Pflicht) / Contract type (required)",
            key=Keys.EMPLOYMENT_CONTRACT,
        )
        st.text_input(
            "Startdatum (Pflicht) / Start date (required)",
            key=Keys.EMPLOYMENT_START,
        )
        st.text_input(
            "Visa-Anforderungen / Visa requirements",
            key=Keys.EMPLOYMENT_VISA,
        )

        prev_clicked = st.form_submit_button("< Zurück / Back")
        next_clicked = st.form_submit_button("Weiter > / Next")
        _render_navigation(step, prev_clicked, next_clicked)


def _compensation_form(step: int) -> None:
    with st.form(key="compensation_form"):
        st.header("Vergütung & Benefits / Compensation & Benefits")
        st.text_input(
            "Gehalt angegeben (Ja/Nein) / Salary provided (Yes/No)",
            key=Keys.SALARY_PROVIDED,
        )
        st.text_input(
            "Gehaltsspanne Minimum / Salary range minimum", key=Keys.SALARY_MIN
        )
        st.text_input(
            "Gehaltsspanne Maximum / Salary range maximum", key=Keys.SALARY_MAX
        )
        st.text_input("Währung / Currency", key=Keys.SALARY_CURRENCY)
        st.text_input(
            "Zeitraum (z.B. jährlich) / Period (e.g., yearly)",
            key=Keys.SALARY_PERIOD,
        )
        st.text_area(
            "Benefits (Pflicht) / Benefits (required)",
            key=Keys.BENEFITS_ITEMS,
        )

        prev_clicked = st.form_submit_button("< Zurück / Back")
        next_clicked = st.form_submit_button("Weiter > / Next")
        _render_navigation(step, prev_clicked, next_clicked)


def _requirements_form(step: int) -> None:
    with st.form(key="requirements_form"):
        st.header("Aufgaben & Anforderungen / Tasks & Requirements")
        st.text_area(
            "Aufgaben (Pflicht) / Responsibilities (required)",
            key=Keys.RESPONSIBILITIES,
        )
        st.text_area(
            "Must-have Hard Skills (Pflicht, Englisch) / Must-have hard skills (required, English)",
            key=Keys.HARD_REQ,
        )
        st.text_area(
            "Optionale Hard Skills / Optional hard skills",
            key=Keys.HARD_OPT,
        )
        st.text_area(
            "Soft Skills (Pflicht, Englisch) / Soft skills (required, English)",
            key=Keys.SOFT_REQ,
        )
        st.text_area(
            "Sprachen (Pflicht) / Languages (required)",
            key=Keys.LANG_REQ,
        )
        st.text_area(
            "Tools & Technologien (Pflicht, Englisch) / Tools & technologies (required, English)",
            key=Keys.TOOLS,
        )
        st.text_area(
            "Ausschlusskriterien / Disqualifiers",
            key=Keys.MUST_NOT,
        )

        suggest_clicked = st.form_submit_button(
            "Typische Hard Skills vorschlagen (ESCO) / Suggest hard skills (ESCO)"
        )
        prev_clicked = st.form_submit_button("< Zurück / Back")
        next_clicked = st.form_submit_button("Weiter > / Next")

        if suggest_clicked:
            title = _read_value(Keys.POSITION_TITLE)
            if not title.strip():
                st.warning(
                    "Bitte zuerst einen Stellentitel eingeben / Please enter a job title first."
                )
            else:
                skills = fetch_essential_skills(title.strip(), language="en")
                if skills:
                    st.session_state[Keys.HARD_REQ] = "\n".join(skills)
                    st.success(
                        "Typische Hard Skills wurden eingetragen / Suggested hard skills inserted."
                    )
                else:
                    st.warning(
                        "Keine passenden Skills gefunden / No matching skills found."
                    )
            return

        _render_navigation(step, prev_clicked, next_clicked)


def _process_form(step: int) -> None:
    with st.form(key="process_form"):
        st.header("Bewerbungsprozess / Application process")
        st.text_area(
            "Interviewphasen / Interview stages",
            key=Keys.PROCESS_STAGES,
        )
        st.text_area(
            "Bewerbungs-Anweisungen / Application instructions",
            key=Keys.PROCESS_INSTRUCTIONS,
        )
        st.text_input(
            "Kontakt E-Mail für Bewerbung / Contact email for applications",
            key=Keys.PROCESS_CONTACT,
        )
        st.text_input(
            "Auswahl-Zeitrahmen / Selection timeline",
            key=Keys.PROCESS_TIMELINE,
        )

        prev_clicked = st.form_submit_button("< Zurück / Back")
        next_clicked = st.form_submit_button("Weiter > / Next")
        _render_navigation(step, prev_clicked, next_clicked)


def _build_prompt() -> str:
    prompt_lines: list[str] = []
    prompt_lines.append(
        f"Unternehmen: {_read_value(Keys.COMPANY_NAME)} | Company: {_read_value(Keys.COMPANY_NAME)}"
    )
    if _read_value(Keys.COMPANY_INDUSTRY):
        prompt_lines.append(f"Branche / Industry: {_read_value(Keys.COMPANY_INDUSTRY)}")
    if _read_value(Keys.COMPANY_SIZE):
        prompt_lines.append(
            f"Unternehmensgröße / Company size: {_read_value(Keys.COMPANY_SIZE)}"
        )
    if _read_value(Keys.COMPANY_HQ):
        prompt_lines.append(f"Hauptsitz / Headquarters: {_read_value(Keys.COMPANY_HQ)}")
    if _read_value(Keys.COMPANY_DESC):
        prompt_lines.append(
            f"Beschreibung / Description: {_read_value(Keys.COMPANY_DESC)}"
        )
    prompt_lines.append(
        f"Position: {_read_value(Keys.POSITION_TITLE)} (Seniorität / Seniority: {_read_value(Keys.POSITION_SENIORITY)})"
    )
    if _read_value(Keys.POSITION_FAMILY):
        prompt_lines.append(
            f"Job-Familie / Job family: {_read_value(Keys.POSITION_FAMILY)}"
        )
    if _read_value(Keys.POSITION_REPORTS_TO_TITLE):
        prompt_lines.append(
            f"Reports to: {_read_value(Keys.POSITION_REPORTS_TO_TITLE)}"
        )
    if _read_value(Keys.POSITION_PEOPLE_MGMT):
        prompt_lines.append(
            f"Führungsverantwortung / People management: {_read_value(Keys.POSITION_PEOPLE_MGMT)}"
        )
    if _read_value(Keys.POSITION_DIRECT_REPORTS):
        prompt_lines.append(
            f"Direkte Reports / Direct reports: {_read_value(Keys.POSITION_DIRECT_REPORTS)}"
        )
    if (
        _read_value(Keys.TEAM_DEPT)
        or _read_value(Keys.TEAM_NAME)
        or _read_value(Keys.TEAM_REPORTING_LINE)
        or _read_value(Keys.TEAM_HEADCOUNT_CURRENT)
        or _read_value(Keys.TEAM_HEADCOUNT_TARGET)
        or _read_value(Keys.TEAM_TOOLS)
    ):
        prompt_lines.append("Team:")
        if _read_value(Keys.TEAM_DEPT):
            prompt_lines.append(
                f"- Abteilung / Department: {_read_value(Keys.TEAM_DEPT)}"
            )
        if _read_value(Keys.TEAM_NAME):
            prompt_lines.append(
                f"- Teamname / Team name: {_read_value(Keys.TEAM_NAME)}"
            )
        if _read_value(Keys.TEAM_REPORTING_LINE):
            prompt_lines.append(
                f"- Reporting Line: {_read_value(Keys.TEAM_REPORTING_LINE)}"
            )
        if _read_value(Keys.TEAM_HEADCOUNT_CURRENT):
            prompt_lines.append(
                f"- Teamgröße aktuell / Current headcount: {_read_value(Keys.TEAM_HEADCOUNT_CURRENT)}"
            )
        if _read_value(Keys.TEAM_HEADCOUNT_TARGET):
            prompt_lines.append(
                f"- Teamgröße geplant / Planned headcount: {_read_value(Keys.TEAM_HEADCOUNT_TARGET)}"
            )
        if _read_value(Keys.TEAM_TOOLS):
            prompt_lines.append(f"- Tools: {_read_value(Keys.TEAM_TOOLS)}")
    prompt_lines.append(f"Dienstort / Location: {_read_value(Keys.LOCATION_CITY)}")
    if _read_value(Keys.LOCATION_WORK_POLICY):
        prompt_lines.append(
            f"Arbeitsmodell / Work model: {_read_value(Keys.LOCATION_WORK_POLICY)}"
        )
    if _read_value(Keys.LOCATION_REMOTE_SCOPE):
        prompt_lines.append(
            f"Remote-Anteil / Remote scope: {_read_value(Keys.LOCATION_REMOTE_SCOPE)}"
        )
    if _read_value(Keys.LOCATION_TZ):
        prompt_lines.append(
            f"Zeitzonenanforderungen / Time zone: {_read_value(Keys.LOCATION_TZ)}"
        )
    if _read_value(Keys.LOCATION_TRAVEL_REQUIRED):
        prompt_lines.append(
            f"Reisetätigkeit / Travel requirement: {_read_value(Keys.LOCATION_TRAVEL_REQUIRED)}"
        )
    if _read_value(Keys.LOCATION_TRAVEL_PCT):
        prompt_lines.append(
            f"Reiseanteil / Travel percentage: {_read_value(Keys.LOCATION_TRAVEL_PCT)}"
        )
    prompt_lines.append(
        f"Anstellungsart / Employment type: {_read_value(Keys.EMPLOYMENT_TYPE)}"
    )
    prompt_lines.append(
        f"Vertragsart / Contract type: {_read_value(Keys.EMPLOYMENT_CONTRACT)}"
    )
    prompt_lines.append(
        f"Startdatum / Start date: {_read_value(Keys.EMPLOYMENT_START)}"
    )
    if _read_value(Keys.EMPLOYMENT_VISA):
        prompt_lines.append(f"Visa / Work permit: {_read_value(Keys.EMPLOYMENT_VISA)}")

    salary_toggle = _read_value(Keys.SALARY_PROVIDED).strip().lower()
    if salary_toggle in {"ja", "yes", "y"}:
        min_salary = _read_value(Keys.SALARY_MIN)
        max_salary = _read_value(Keys.SALARY_MAX)
        if min_salary or max_salary:
            range_text = f"{min_salary or '?'} - {max_salary or '?'}"
            if _read_value(Keys.SALARY_CURRENCY):
                range_text = f"{range_text} {_read_value(Keys.SALARY_CURRENCY)}"
            if _read_value(Keys.SALARY_PERIOD):
                range_text = f"{range_text} pro / per {_read_value(Keys.SALARY_PERIOD)}"
            prompt_lines.append(f"Gehalt / Salary: {range_text}")

    benefits = _parse_multiline(_read_value(Keys.BENEFITS_ITEMS))
    if benefits:
        prompt_lines.append("Benefits:")
        prompt_lines.extend([f"- {benefit}" for benefit in benefits])

    responsibilities = _parse_multiline(_read_value(Keys.RESPONSIBILITIES))
    if responsibilities:
        prompt_lines.append("Aufgaben / Responsibilities:")
        prompt_lines.extend([f"- {item}" for item in responsibilities])

    requirements: list[str] = []
    hard_req = _parse_multiline(_read_value(Keys.HARD_REQ))
    soft_req = _parse_multiline(_read_value(Keys.SOFT_REQ))
    lang_req = _parse_multiline(_read_value(Keys.LANG_REQ))
    tools_req = _parse_multiline(_read_value(Keys.TOOLS))
    hard_opt = _parse_multiline(_read_value(Keys.HARD_OPT))
    must_not = _parse_multiline(_read_value(Keys.MUST_NOT))

    if hard_req:
        requirements.append(
            f"Fachliche Anforderungen / Hard skills: {', '.join(hard_req)}"
        )
    if soft_req:
        requirements.append(f"Soft Skills: {', '.join(soft_req)}")
    if lang_req:
        requirements.append(f"Sprachen / Languages: {', '.join(lang_req)}")
    if tools_req:
        requirements.append(f"Tools: {', '.join(tools_req)}")
    if hard_opt:
        requirements.append(
            f"Optionale Skills / Optional skills: {', '.join(hard_opt)}"
        )
    if must_not:
        requirements.append(
            f"Ausschlusskriterien / Disqualifiers: {', '.join(must_not)}"
        )
    if requirements:
        prompt_lines.append("Anforderungen / Requirements:")
        prompt_lines.extend([f"- {req}" for req in requirements])

    process_stages = _parse_multiline(_read_value(Keys.PROCESS_STAGES))
    if (
        process_stages
        or _read_value(Keys.PROCESS_INSTRUCTIONS)
        or _read_value(Keys.PROCESS_CONTACT)
        or _read_value(Keys.PROCESS_TIMELINE)
    ):
        prompt_lines.append("Bewerbungsprozess / Application process:")
        if process_stages:
            prompt_lines.append("  Phasen / Stages:")
            prompt_lines.extend([f"  - {stage}" for stage in process_stages])
        if _read_value(Keys.PROCESS_INSTRUCTIONS):
            prompt_lines.append(
                f"  Hinweise / Instructions: {_read_value(Keys.PROCESS_INSTRUCTIONS)}"
            )
        if _read_value(Keys.PROCESS_CONTACT):
            prompt_lines.append(
                f"  Kontakt / Contact: {_read_value(Keys.PROCESS_CONTACT)}"
            )
        if _read_value(Keys.PROCESS_TIMELINE):
            prompt_lines.append(
                f"  Zeitrahmen / Timeline: {_read_value(Keys.PROCESS_TIMELINE)}"
            )

    return "\n".join(prompt_lines)


def _render_review() -> None:
    st.header("Review & Generierung / Review & Generate")
    st.write(
        "Bitte prüfen Sie Ihre Angaben bevor die Stellenanzeige generiert wird. / Please review your inputs before generating the job ad."
    )

    missing_global = [key for key in REQUIRED_FIELDS if not _read_value(key).strip()]
    if missing_global:
        st.warning(
            "Einige Pflichtfelder fehlen noch / Some required fields are missing: "
            + ", ".join(_humanize_field(key) for key in missing_global)
        )

    st.subheader("Eingegebene Daten / Entered data")
    for key in REQUIRED_FIELDS:
        st.text(f"{_humanize_field(key)}: {_read_value(key)}")

    if st.button("< Zurück / Back to edit"):
        st.session_state["current_step"] = STEP_ORDER[-2]

    if st.button("Stellenanzeige generieren / Generate job ad"):
        _generate_job_ad()


def _generate_job_ad() -> None:
    api_key = (
        os.getenv("OPENAI_API_KEY")
        or getattr(st.secrets, "OPENAI_API_KEY", None)
        or st.session_state.get("openai_api_key_input")
    )
    if not api_key:
        st.error("Es wurde kein OpenAI API-Key angegeben / No OpenAI API key provided.")
        return
    openai.api_key = api_key

    missing = [key for key in REQUIRED_FIELDS if not _read_value(key).strip()]
    if missing:
        st.error(
            "Bitte füllen Sie alle Pflichtfelder aus / Please complete all required fields."
        )
        return

    prompt = _build_prompt()
    messages = [
        {
            "role": "system",
            "content": "Du bist ein erfahrener HR-Experte und schreibst professionelle Stellenanzeigen auf Deutsch.",
        },
        {
            "role": "user",
            "content": (
                "Schreibe auf Basis der folgenden strukturierten Daten eine ansprechende zweisprachige (DE & EN) Stellenanzeige."
                "\nPlease write a compelling bilingual (DE & EN) job ad based on the structured data.\n"
                f"Daten / Data:\n{prompt}"
            ),
        },
    ]
    with st.spinner("Generiere Stellenanzeige... / Generating job ad..."):
        for attempt in range(3):
            try:
                response = openai.ChatCompletion.create(
                    model=MODEL_NAME,
                    messages=messages,
                    temperature=0.7,
                    max_tokens=1200,
                    request_timeout=30,
                )
                job_ad = response["choices"][0]["message"]["content"].strip()
                st.subheader("Generierte Stellenanzeige / Generated job ad")
                st.markdown(job_ad)
                st.download_button(
                    "Als Textdatei herunterladen / Download as text",
                    job_ad,
                    file_name="stellenanzeige.txt",
                )
                return
            except Exception as exc:  # pragma: no cover - API errors handled by UI
                if attempt < 2:
                    wait_time = 2**attempt
                    st.warning(
                        "API-Aufruf fehlgeschlagen, neuer Versuch folgt / API call failed, retrying..."
                    )
                    time.sleep(wait_time)
                else:
                    st.error(f"Fehler bei der Generierung: {exc}")


def _render_step() -> None:
    current_step: int = st.session_state.get("current_step", STEP_ORDER[0])
    if current_step == 1:
        _company_form(current_step)
    elif current_step == 2:
        _position_form(current_step)
    elif current_step == 3:
        _location_form(current_step)
    elif current_step == 4:
        _compensation_form(current_step)
    elif current_step == 5:
        _requirements_form(current_step)
    elif current_step == 6:
        _process_form(current_step)
    else:
        _render_review()


def main() -> None:
    st.set_page_config(
        page_title="Job Description Generator", page_icon="📝", layout="wide"
    )
    st.title("Job Description Generator / Stellenanzeigen-Generator")
    st.markdown(
        "Dieses Streamlit-Tool generiert zweisprachige Stellenanzeigen auf Basis strukturierter Eingaben. "
        "This Streamlit tool generates bilingual job ads based on structured inputs."
    )

    _init_session_state()

    st.session_state["openai_api_key_input"] = st.sidebar.text_input(
        "OpenAI API-Key eingeben / Enter OpenAI API key",
        type="password",
        value=st.session_state.get("openai_api_key_input", ""),
    )

    progress_ratio = STEP_ORDER.index(st.session_state.get("current_step", 1)) / (
        len(STEP_ORDER) - 1
    )
    st.progress(progress_ratio)

    _render_step()


if __name__ == "__main__":
    main()
