"""Summary and export page."""

from __future__ import annotations

import json
from datetime import datetime

import streamlit as st

from state import AppState, apply_app_state_to_profile, get_app_state


def _section_status(label: str, complete: bool) -> str:
    icon = "✅" if complete else "⚠️"
    return f"{icon} {label}"


def _markdown_export(state: AppState) -> str:
    profile = state.profile
    role = state.role
    comp = state.compensation
    skills = state.skills

    lines = [
        "# Job Brief / Stellensteckbrief",
        f"**Company / Unternehmen:** {profile.company_name or '-'}",
        f"**City / Stadt:** {profile.primary_city or '-'}",
        f"**Job Title / Rolle:** {role.job_title or '-'}",
        f"**Seniority / Seniorität:** {role.seniority or '-'}",
        f"**Department / Bereich:** {role.department or '-'}",
        "",
        "## Summary / Kurzbeschreibung",
        role.summary or "-",
        "",
        "## Tasks / Aufgaben",
        *(f"- {task}" for task in skills.tasks or ["-"]),
        "",
        "## Must-have Skills",
        *(f"- {skill}" for skill in skills.must_have or ["-"]),
        "",
        "## Nice-to-have Skills",
        *(f"- {skill}" for skill in skills.nice_to_have or ["-"]),
        "",
        "## Compensation / Vergütung",
        f"- Currency / Währung: {comp.currency or '-'}",
        f"- Range: {comp.salary_min or '-'} - {comp.salary_max or '-'}",
        f"- Variable %: {comp.variable_pct or 0}",
        f"- Benefits: {', '.join(comp.benefits) if comp.benefits else '-'}",
        f"- Relocation: {comp.relocation}",
        f"- Visa: {comp.visa}",
        "",
        f"Exported: {datetime.now(datetime.UTC).isoformat()} UTC",
    ]
    return "\n".join(lines)


def main() -> None:
    st.set_page_config(page_title="Summary", page_icon="📄", layout="wide")
    state = get_app_state()

    st.title("Summary / Zusammenfassung")
    st.caption("Übersicht und Export / Overview and export")

    profile_complete = state.profile.is_complete()
    role_complete = state.role.is_complete()
    skills_complete = state.skills.is_complete()
    comp_complete = state.compensation.is_complete()
    forecast_complete = state.forecast.is_complete()

    st.subheader("Status")
    st.write(_section_status("Profile", profile_complete))
    st.write(_section_status("Role", role_complete))
    st.write(_section_status("Skills", skills_complete))
    st.write(_section_status("Compensation", comp_complete))
    st.write(_section_status("Forecast", forecast_complete))

    st.divider()
    st.subheader("Exports")
    profile_payload = apply_app_state_to_profile(state)
    json_bytes = json.dumps(profile_payload, indent=2, ensure_ascii=False).encode("utf-8")
    st.download_button(
        label="JSON Export",
        file_name="need_analysis_profile.json",
        mime="application/json",
        data=json_bytes,
    )

    markdown_payload = _markdown_export(state)
    st.download_button(
        label="Markdown Export",
        file_name="need_analysis_summary.md",
        mime="text/markdown",
        data=markdown_payload,
    )
    st.text_area("Markdown Vorschau / Preview", value=markdown_payload, height=260)

    st.caption(
        "Nutze die Navigation links, um Korrekturen vorzunehmen. / Use the left navigation to adjust entries."
    )


if __name__ == "__main__":
    main()
