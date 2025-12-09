"""Skills page for the multi-step wizard."""

from __future__ import annotations

import streamlit as st

from state import get_app_state, set_app_state
from validators import validate_skills


def _to_text(value: list[str]) -> str:
    return "\n".join(value)


def _to_list(value: str) -> list[str]:
    return [item.strip() for item in value.splitlines() if item.strip()]


def _sample_tasks(job_title: str | None) -> list[str]:
    title = job_title or "die Rolle"
    return [
        f"Leitet Projekte für {title} / Leads projects for {title}",
        "Koordiniert Stakeholder / Coordinates stakeholders",
        "Berichtet Status und Risiken / Reports status and risks",
    ]


def _sample_skills() -> list[str]:
    return ["Kommunikation / Communication", "Teamwork", "Problem-Solving"]


def _sample_nice_to_have() -> list[str]:
    return ["Branchenerfahrung / Industry experience", "Mentoring", "Process Improvement"]


def main() -> None:
    st.set_page_config(page_title="Skills", page_icon="🛠️", layout="wide")
    lang = st.session_state.get("lang", "de")
    state = get_app_state()
    skills = state.skills

    st.title("Skills & Tasks")
    st.caption("Pflichtfelder sind markiert / Required fields are marked with *")

    tasks_tab, must_tab, nice_tab = st.tabs(
        ["Tasks", "Core Skills", "Nice to have"]
    )

    with tasks_tab:
        tasks_text = st.text_area(
            "Tasks / Aufgaben *",
            value=_to_text(skills.tasks),
            height=180,
            help="Eine Zeile pro Aufgabe / One line per task",
        )
        if st.button("Tasks generieren / Generate tasks"):
            skills.tasks = _sample_tasks(state.role.job_title)
            st.success("Tasks aktualisiert / Tasks updated", icon="✨")
        else:
            skills.tasks = _to_list(tasks_text)

    with must_tab:
        must_text = st.text_area(
            "Pflicht-Skills / Must-have Skills *",
            value=_to_text(skills.must_have),
            height=160,
            help="Eine Zeile pro Skill / One line per skill",
        )
        if st.button("Core Skills vorschlagen / Suggest core skills"):
            skills.must_have = _sample_skills()
            st.success("Core Skills aktualisiert / Core skills updated", icon="✨")
        else:
            skills.must_have = _to_list(must_text)

    with nice_tab:
        nice_text = st.text_area(
            "Nice to have",
            value=_to_text(skills.nice_to_have),
            height=160,
            help="Optionale Skills / Optional skills",
        )
        if st.button("Nice to have vorschlagen / Suggest nice to have"):
            skills.nice_to_have = _sample_nice_to_have()
            st.success("Nice to have aktualisiert / Nice-to-have updated", icon="✨")
        else:
            skills.nice_to_have = _to_list(nice_text)

    set_app_state(state)

    errors = validate_skills(skills, lang=lang)
    if errors:
        st.error(
            "Bitte alle Pflichtfelder ausfüllen / Please complete all required fields:",
            icon="⚠️",
        )
        for _, msg in errors:
            st.write(f"- {msg}")

    nav_col1, nav_col2 = st.columns(2)
    with nav_col1:
        st.button("⬅️ Zurück / Back", on_click=lambda: st.switch_page("pages/02_Role.py"))
    with nav_col2:
        st.button(
            "Weiter / Next ➡️",
            type="primary",
            disabled=bool(errors),
            on_click=lambda: st.switch_page("pages/04_Compensation.py"),
        )


if __name__ == "__main__":
    main()
