"""Streamlit entrypoint for the multi-step Need-Analysis wizard."""

from __future__ import annotations

import streamlit as st

from state import AppState, get_app_state, set_app_state


def _get_language() -> str:
    lang = st.session_state.get("lang", "de")
    st.session_state["lang"] = lang
    return lang


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
    st.write("Bereit? / Ready?")
    if st.button("Zum Profil starten / Go to Profile", type="primary"):
        st.switch_page("pages/01_Profile.py")

    st.caption(
        "Tipp: Du kannst jederzeit zur Zusammenfassung springen, um den aktuellen Status zu prüfen. / "
        "Tip: Jump to the summary page at any time to review progress."
    )


if __name__ == "__main__":
    main()
