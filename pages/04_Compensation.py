"""Compensation page for the multi-step wizard."""

from __future__ import annotations

import streamlit as st

from state import get_app_state, set_app_state
from validators import validate_compensation


def _to_text(value: list[str]) -> str:
    return "\n".join(value)


def _to_list(value: str) -> list[str]:
    return [item.strip() for item in value.splitlines() if item.strip()]


def main() -> None:
    st.set_page_config(page_title="Compensation", page_icon="💰", layout="wide")
    lang = st.session_state.get("lang", "de")
    state = get_app_state()
    comp = state.compensation

    st.title("Compensation")
    st.caption("Pflichtfelder sind markiert / Required fields are marked with *")

    col1, col2 = st.columns(2)
    with col1:
        comp.currency = st.text_input(
            "Currency / Währung *",
            value=comp.currency or "",
            help="z.B. EUR, USD / e.g. EUR, USD",
        )
        comp.salary_min = st.number_input(
            "Salary Min / Gehalt Minimum *",
            value=comp.salary_min or 0.0,
            min_value=0.0,
            step=1000.0,
        )
        comp.variable_pct = st.number_input(
            "Variable % / Variable Vergütung",
            value=comp.variable_pct or 0.0,
            min_value=0.0,
            max_value=100.0,
            step=1.0,
        )
        comp.relocation = st.checkbox(
            "Relocation support / Umzugsunterstützung",
            value=bool(comp.relocation),
        )
    with col2:
        comp.salary_max = st.number_input(
            "Salary Max / Gehalt Maximum *",
            value=comp.salary_max or 0.0,
            min_value=0.0,
            step=1000.0,
        )
        benefits_text = st.text_area(
            "Benefits (eine Zeile pro Benefit) / Benefits (one per line) *",
            value=_to_text(comp.benefits),
            height=140,
        )
        comp.visa = st.checkbox("Visa Sponsorship / Visasponsoring", value=bool(comp.visa))

    comp.benefits = _to_list(benefits_text)
    set_app_state(state)

    errors = validate_compensation(comp, lang=lang)
    if errors:
        st.error(
            "Bitte alle Pflichtfelder ausfüllen / Please complete all required fields:",
            icon="⚠️",
        )
        for _, msg in errors:
            st.write(f"- {msg}")

    nav_col1, nav_col2 = st.columns(2)
    with nav_col1:
        st.button("⬅️ Zurück / Back", on_click=lambda: st.switch_page("pages/03_Skills.py"))
    with nav_col2:
        st.button(
            "Weiter / Next ➡️",
            type="primary",
            disabled=bool(errors),
            on_click=lambda: st.switch_page("pages/05_Forecast.py"),
        )


if __name__ == "__main__":
    main()
