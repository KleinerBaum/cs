# CognitiveStaffing – Need Analysis Wizard (Streamlit)

A modular Streamlit app for line managers to transform an existing job ad (URL, PDF, DOCX, or pasted text) into a structured **NeedAnalysisProfile** and an exportable job ad draft.

## Multi-step wizard (DE/EN)

The home page now provides a bilingual, multi-step wizard to collect all required fields before generating a job ad. Each section (company, position, location, compensation, requirements, process, and review) is its own `st.form` with forward/backward navigation and per-step validation, keeping values in `st.session_state` between steps.

The sidebar lets you switch between German and English labels, pick a light/dark theme, and toggle optional ESCO assistance for skills. All UI texts and generated job-ad exports follow the selected language.

### Branding & layout

- The main canvas uses `images/AdobeStock_506577005.jpeg` as a full-bleed background with a soft gradient overlay so the wizard steps remain legible.
- A fixed, pulsating logo (`images/animation_pulse_Default_7kigl22lw.gif`) sits in the top-right corner to keep the brand in view across all steps without obstructing the form content.

### ESCO skill suggestions

- ESCO calls now auto-detect whether the query/title looks German or English and query the ESCO API in that language for better hits.
- Retrieved ESCO skills can be staged via a dedicated button and are safely injected into the required hard-skills list without Streamlit widget key conflicts.

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
