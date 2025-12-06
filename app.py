"""Streamlit entrypoint for the Need Analysis Wizard UI."""

from __future__ import annotations

from src.ui import run_app


def main() -> None:
    """Launch the Streamlit UI."""

    run_app()


if __name__ == "__main__":
    main()
