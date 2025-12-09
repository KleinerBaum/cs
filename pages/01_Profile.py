"""Profile page for the multi-step wizard."""

from __future__ import annotations

import streamlit as st

from state import get_app_state, set_app_state
from validators import validate_profile


def main() -> None:
    st.set_page_config(page_title="Profil", page_icon="🏢", layout="wide")
    lang = st.session_state.get("lang", "de")
    state = get_app_state()
    profile = state.profile

    st.title("Profil / Profile")
    st.caption("Pflichtfelder sind markiert / Required fields are marked with *")

    col1, col2 = st.columns(2)
    with col1:
        profile.company_name = st.text_input(
            "Company Name / Firmenname *",
            value=profile.company_name or "",
            help="Legal or brand name of the organization. / Rechtlicher oder Markenname.",
        )
        profile.employment_type = st.text_input(
            "Employment Type / Anstellungsart *",
            value=profile.employment_type or "",
            help="e.g. full-time, part-time. / z.B. Vollzeit, Teilzeit.",
        )
        profile.start_date = st.text_input(
            "Start Date / Startdatum *",
            value=profile.start_date or "",
            help="Planned start date. / Geplantes Startdatum.",
        )
    with col2:
        profile.primary_city = st.text_input(
            "Primary City / Hauptstandort *",
            value=profile.primary_city or "",
            help="Location for the role. / Einsatzort für die Rolle.",
        )
        profile.contract_type = st.text_input(
            "Contract Type / Vertragsart *",
            value=profile.contract_type or "",
            help="e.g. permanent, fixed-term. / z.B. unbefristet, befristet.",
        )
        profile.remote_policy = st.text_input(
            "Remote Policy / Remote-Regelung",
            value=profile.remote_policy or "",
            help="Optional: remote, hybrid, onsite details. / Optional: Remote-, Hybrid- oder Onsite-Regelung.",
        )

    set_app_state(state)

    errors = validate_profile(profile, lang=lang)
    if errors:
        st.error(
            "Bitte alle Pflichtfelder ausfüllen / Please complete all required fields:",
            icon="⚠️",
        )
        for _, msg in errors:
            st.write(f"- {msg}")

    nav_col1, nav_col2 = st.columns(2)
    with nav_col1:
        st.button("⬅️ Zurück / Back", disabled=True)
    with nav_col2:
        st.button(
            "Weiter / Next ➡️",
            type="primary",
            disabled=bool(errors),
            on_click=lambda: st.switch_page("pages/02_Role.py"),
        )


if __name__ == "__main__":
    main()
