"""Role page for the multi-step wizard."""

from __future__ import annotations

import streamlit as st

from state import get_app_state, set_app_state
from validators import validate_role


def _generate_summary(job_title: str | None, department: str | None) -> str:
    title = job_title or "Role"
    dept = f" in {department}" if department else ""
    return (
        f"{title}{dept} responsible for delivering key outcomes, collaborating across teams, "
        "and shaping the function's roadmap. / Verantwortlich für Ergebnisse, teamübergreifende "
        "Zusammenarbeit und die Weiterentwicklung des Bereichs."
    )


def main() -> None:
    st.set_page_config(page_title="Rolle", page_icon="🧑‍💼", layout="wide")
    lang = st.session_state.get("lang", "de")
    state = get_app_state()
    role = state.role

    st.title("Rolle / Role")
    st.caption("Pflichtfelder sind markiert / Required fields are marked with *")

    col1, col2 = st.columns(2)
    with col1:
        role.job_title = st.text_input(
            "Job Title / Rollenbezeichnung *",
            value=role.job_title or "",
            help="z.B. Senior Backend Engineer / e.g. Senior Backend Engineer",
        )
        role.department = st.text_input(
            "Department / Fachbereich *",
            value=role.department or "",
            help="Team oder Abteilung / Team or department",
        )
        role.direct_reports = st.number_input(
            "Direct Reports / Direkte Reports",
            value=role.direct_reports or 0,
            min_value=0,
            step=1,
            help="Anzahl direkter Reports / number of direct reports",
        )
    with col2:
        role.seniority = st.text_input(
            "Seniority / Seniorität *",
            value=role.seniority or "",
            help="z.B. Junior, Senior / e.g. Junior, Senior",
        )
        role.work_schedule = st.text_input(
            "Work Schedule / Arbeitszeitmodell",
            value=role.work_schedule or "",
            help="z.B. 40h, Schichtmodell / e.g. 40h, shifts",
        )
        role.summary = st.text_area(
            "Kurzbeschreibung / Summary",
            value=role.summary or "",
            help="Kurzer Überblick zur Rolle / Short overview of the role",
            height=180,
        )

    if st.button("Rollenbeschreibung generieren / Generate summary", type="secondary"):
        role.summary = _generate_summary(role.job_title, role.department)
        st.success("Summary aktualisiert / Summary updated", icon="✨")

    set_app_state(state)

    errors = validate_role(role, lang=lang)
    if errors:
        st.error(
            "Bitte alle Pflichtfelder ausfüllen / Please complete all required fields:",
            icon="⚠️",
        )
        for _, msg in errors:
            st.write(f"- {msg}")

    nav_col1, nav_col2 = st.columns(2)
    with nav_col1:
        st.button("⬅️ Zurück / Back", on_click=lambda: st.switch_page("pages/01_Profile.py"))
    with nav_col2:
        st.button(
            "Weiter / Next ➡️",
            type="primary",
            disabled=bool(errors),
            on_click=lambda: st.switch_page("pages/03_Skills.py"),
        )


if __name__ == "__main__":
    main()
