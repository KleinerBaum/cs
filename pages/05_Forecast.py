"""Forecast simulation page."""

from __future__ import annotations

import streamlit as st

from src.forecast import simulate_time_to_fill
from state import ForecastConfig, get_app_state, set_app_state


def main() -> None:
    st.set_page_config(page_title="Forecast", page_icon="📈", layout="wide")
    state = get_app_state()
    forecast_state = state.forecast
    config: ForecastConfig = forecast_state.config

    st.title("Forecast / Simulation")
    st.caption("Grobe Time-to-Fill Abschätzung / Rough time-to-fill simulation")

    col1, col2 = st.columns(2)
    with col1:
        config.budget_total = st.number_input(
            "Budgeted candidates / Budgetierte Kandidaten",
            value=config.budget_total or 0.0,
            min_value=0.0,
            step=1.0,
            help="Wie viele Top-of-Funnel-Kontakte geplant sind. / How many top-of-funnel contacts you plan.",
        )
        config.conv_screen_to_offer = st.number_input(
            "Conversion Screen→Offer (0-1)",
            value=config.conv_screen_to_offer or 0.2,
            min_value=0.0,
            max_value=1.0,
            step=0.05,
        )
        config.ttf_mean_days = st.number_input(
            "Ø Time-to-Fill (Tage) / Mean time-to-fill (days)",
            value=config.ttf_mean_days or 45.0,
            min_value=1.0,
            step=1.0,
        )
    with col2:
        config.conv_top_to_screen = st.number_input(
            "Conversion Top→Screen (0-1)",
            value=config.conv_top_to_screen or 0.5,
            min_value=0.0,
            max_value=1.0,
            step=0.05,
        )
        config.conv_offer_to_hire = st.number_input(
            "Conversion Offer→Hire (0-1)",
            value=config.conv_offer_to_hire or 0.6,
            min_value=0.0,
            max_value=1.0,
            step=0.05,
        )
        config.ttf_std_days = st.number_input(
            "Streuung (Std) / Std deviation (days)",
            value=config.ttf_std_days or 10.0,
            min_value=0.0,
            step=1.0,
        )

    if st.button("Simulate / Simulation starten", type="primary"):
        if not config.is_ready():
            st.error(
                "Bitte alle Felder für die Simulation ausfüllen / Please complete all simulation fields",
                icon="⚠️",
            )
        else:
            forecast_state.result = simulate_time_to_fill(config)
            st.success("Simulation aktualisiert / Simulation updated", icon="✅")

    set_app_state(state)

    if forecast_state.result:
        res = forecast_state.result
        st.subheader("Ergebnisse / Results")
        kpi1, kpi2, kpi3, kpi4 = st.columns(4)
        kpi1.metric("Ø Tage / Expected days", f"{res.expected_days:.1f}")
        kpi2.metric("Optimistisch", f"{res.optimistic_days:.1f}")
        kpi3.metric("Pessimistisch", f"{res.pessimistic_days:.1f}")
        kpi4.metric("Mögliche Hires", f"{res.hires_possible:.1f}")

        st.caption("Histogramm der simulierten Werte / Histogram of simulated samples")
        st.bar_chart(res.samples)

    nav_col1, nav_col2 = st.columns(2)
    with nav_col1:
        st.button("⬅️ Zurück / Back", on_click=lambda: st.switch_page("pages/04_Compensation.py"))
    with nav_col2:
        st.button(
            "Weiter / Next ➡️",
            type="primary",
            disabled=not forecast_state.config.is_ready(),
            on_click=lambda: st.switch_page("pages/99_Summary.py"),
        )


if __name__ == "__main__":
    main()
