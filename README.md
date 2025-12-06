# CognitiveStaffing – Need Analysis Wizard (Streamlit)

A modular Streamlit app for line managers to transform an existing job ad (URL, PDF, DOCX, or pasted text) into a structured **NeedAnalysisProfile** and an exportable job ad draft.

## Multi-step wizard (DE/EN)

The home page now provides a bilingual, multi-step wizard to collect all required fields before generating a job ad. Each section (company, position, location, compensation, requirements, process, and review) is its own `st.form` with forward/backward navigation and per-step validation, keeping values in `st.session_state` between steps.

The sidebar lets you switch between German and English labels, pick a light/dark theme, and toggle optional ESCO assistance for skills. All UI texts and generated job-ad exports follow the selected language.

## Configuration

Set the OpenAI API key via Streamlit secrets (e.g., `.streamlit/secrets.toml`) or the `OPENAI_API_KEY` environment variable. The UI no longer exposes a text field for the key; the app will stop early with a clear error if the key is missing.

```toml
[general]
OPENAI_API_KEY = "sk-..."
```

## Quickstart (local)

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
source .venv/bin/activate

pip install -r requirements.txt
streamlit run app.py
