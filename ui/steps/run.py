"""Run the deterministic pipeline inside Streamlit."""

from __future__ import annotations

import streamlit as st

from core.schemas import RawInput
from core.validator import validate_required_fields
from pipeline import run_pipeline
from ui.components.payload import PipelinePayload


def _read_text_from_state() -> str:
    """Fetch the raw text from common session state keys."""

    for key in ("raw_input", "raw_text", "content", "text"):
        stored = st.session_state.get(key)
        if isinstance(stored, str) and stored.strip():
            return stored
    return ""


def _read_payload_from_state() -> PipelinePayload:
    stored_payload = st.session_state.get("payload")
    return PipelinePayload.from_mapping(stored_payload)


def main() -> None:
    st.set_page_config(page_title="Pipeline Runner | Pipeline-Ausführung")
    st.title("Pipeline Runner / Pipeline-Ausführung")

    raw_text = _read_text_from_state()
    payload_model = _read_payload_from_state()
    payload = payload_model.to_canonical_dict()

    if not raw_text:
        st.info(
            "Provide input text in session state before running. | "
            "Bitte Eingangstext im Session-State bereitstellen, bevor gestartet wird.",
        )
        return

    result = run_pipeline(RawInput(text=raw_text), payload)

    validation = validate_required_fields(payload)
    missing = validation["missing_required"]

    if missing:
        missing_list = ", ".join(missing)
        st.warning(
            f"Missing required fields: {missing_list} | "
            f"Fehlende Pflichtfelder: {missing_list}"
        )
    else:
        st.success(
            "All required fields are present. | Alle Pflichtfelder sind ausgefüllt."
        )

    st.subheader("Pipeline output / Pipeline-Ausgabe")
    st.json(result)


if __name__ == "__main__":
    main()
