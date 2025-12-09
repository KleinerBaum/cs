# CognitiveStaffing – Need Analysis Wizard (Streamlit)

A modular Streamlit app for line managers to transform an existing job ad (URL, PDF, DOCX, or pasted text) into a structured **NeedAnalysisProfile** and an exportable job ad draft.

## Ingestion fidelity (DE/EN)

- PDF uploads use PyMuPDF with ligature and whitespace preservation so that bullet lists, headings, and special characters remain intact in the extracted raw text.
- DOCX uploads now keep blank lines between paragraphs to retain list and section boundaries when populating the wizard.
- If a PDF contains only images (likely a scan) and no extractable text, the import step surfaces a bilingual hint to provide a searchable PDF or run OCR first.

## Multi-step wizard (DE/EN)

The app features a bilingual, multi-step wizard to collect all required fields before generating a job ad. Each section (company, team, position, framework, tasks, skills, benefits, process, and review) is presented step-by-step with forward/backward navigation. Required fields ("Pflichtfelder") are marked with an asterisk and highlighted if missing. All UI labels and generated job-ad content adapt to the selected language (German or English).

- **Bilingual UI:** Use the sidebar language selector to switch between German and English labels. The final job ad draft will be generated in the chosen language.
- **English field translation:** In the "Skills" step, you can automatically translate key fields (job title, required hard/soft skills, tools) to English by clicking the **"AI: Generate English versions"** button. This uses the OpenAI API to fill optional English fields (marked as "*English version, optional*"). If you switch the UI language to English, these translated values will be used in the job ad output.
- **Dynamic forms:** Each step groups a set of questions (basic and optional advanced fields). Advanced fields are hidden under *"More details (optional)"* to keep the UI uncluttered. Conditional fields (e.g., travel percentage if travel is required) only appear when relevant.
- **Calm validation:** Required-field warnings stay hidden on initial load and only appear after you attempt an action where the missing inputs matter (e.g., clicking **Next** with empty required fields). This avoids surprising users with alerts before they start.
- **Session state:** Form data persists in `st.session_state` as you navigate. You can reset the session via the sidebar.
- **Sidebar input overview:** Below the **"Reset session"** button, each step now has a collapsible summary (company, team, framework, etc.) showing all fields with their current values and a quick **"Go to step"** jump link.

## Branding & layout

- The main app uses a background image (`images/AdobeStock_506577005.jpeg`) with a subtle overlay to ensure readability of form text.
- A pulsating logo (`images/animation_pulse_Default_7kigl22lw.gif`) now sits in a scaled badge with generous padding; it stays clear of the wizard content while remaining visible on both desktop and mobile.
- Light and dark themes share a teal-and-slate palette that matches the logo tones; buttons use the same gradient to keep CTA styling consistent with the branding.
- The sidebar groups controls into icon-labeled sections (display/language, assistants, quick actions) on a contrasting card background to keep settings scannable.

## ESCO skill suggestions

- **ESCO integration:** On the *Skills* step, you can search for standardized occupations and skills from the European ESCO database. The app detects the language of your query (DE/EN) and fetches relevant occupations.
- After selecting an occupation from the search results, click **"Apply ESCO skills"** to retrieve related skills for that occupation. You can then choose up to several skills and insert them into the required hard skills list with one click. The app avoids duplicate entries and labels these as AI-suggested in the profile.
- ESCO suggestions are optional and can be toggled on/off via the sidebar ("Enable ESCO suggestions").

## AI-powered assistance

- **Field extraction:** In the *Import* step, if an OpenAI API key is configured, the app will attempt to extract structured information from the provided job ad text using an LLM (default model **gpt-4o-mini**, overrideable). Detected fields (e.g. company contact email or website) are prefilled with a provenance tag "Extracted". This speeds up the form-filling process.
- **Mandatory-field recovery:** The extractor now explicitly prioritises all Pflichtfelder—especially job title, employment type, contract type, primary city, and required languages—and performs a targeted second LLM pass plus lightweight heuristics to backfill anything still missing.
- **Auto-suggest for gaps:** After extraction, the wizard asks the LLM for plausible suggestions for any remaining required **or optional** fields. These values are inserted with the provenance "AI suggestion" so they are visually marked, fully editable, and easy to accept or overwrite.
- **Follow-up questions:** At each step, you can click **"AI: Generate suggestions"** to have the LLM propose follow-up questions for any missing or uncertain fields. These AI-generated questions (in both DE and EN) will appear below the form, allowing you to fill in additional details. This feature is optional and only triggers if relevant fields are missing. You can also enable auto-generation of follow-ups via the sidebar ("Suggest AI follow-ups automatically").
- **English translation:** As noted, the LLM can translate key fields to English for international job ads. The translated values are stored in parallel fields (e.g., `job_title_en`) and used when you switch to English output.
- **Model flexibility with safe default:** The sidebar now offers an optional model selector (defaulting to **gpt-4o-mini**). You can also set `OPENAI_MODEL` (Streamlit secrets or environment) to pin a specific model like `gpt-3.5-turbo` for cost-sensitive runs. The app continues to omit unsupported sampling parameters for Responses API compatibility.
- **Resilient error handling:** Intake LLM calls surface targeted configuration hints for invalid models/parameters and separate retry/backoff guidance for network or timeout issues (bilingual messaging).
- **Structured JSON + fallback:** LLM calls now request structured Responses API outputs (`response_format`) so extraction and suggestion payloads stay valid JSON without manual clean-up. If a response still cannot be parsed or the first call fails, the app runs a low-cost recovery request via `fill_missing_fields_prompt` for prioritized missing paths (source text only) with short backoff. If this also fails, the UI surfaces a bilingual warning and continues with heuristic fills instead of aborting.

## Salary prediction (checkbox-driven)

- In the **Review & Export** step, a dedicated *Salary prediction* card lists key profile fields (seniority, location, work policy, contract/employment type, industry, size, currency).
- Use the checkboxes to explicitly choose which values should drive the estimate; the UI shows the current value of each field so you can see what will be applied.
- Click **“Gehaltsprognose berechnen”** to trigger the calculation once you are happy with the selection—this avoids re-running the heuristic on every small edit.
- The app stores the used parameters, shows the predicted range (lower/upper bound), visualises the min/avg/max band in a theme-aware chart, and provides a short bilingual rationale based on the applied multipliers (e.g., city premium, part-time discount, contract type).

## Configuration

Before launching the app, set the OpenAI API key via Streamlit secrets or an environment variable. The UI does **not** expose a text field for the API key; if no key is configured, the app will stop with an error message.

You can also choose the default model via Streamlit secrets or an environment variable; the sidebar allows toggling between common options at runtime:

You can add the key to `.streamlit/secrets.toml` or as an environment variable:

```toml
OPENAI_API_KEY = "sk-..."
OPENAI_MODEL = "gpt-4o-mini"  # Optional: override the default model for all requests

# or under a [general] section:
[general]
OPENAI_API_KEY = "sk-..."
OPENAI_MODEL = "gpt-3.5-turbo"

```

Tip: use `OPENAI_MODEL=gpt-3.5-turbo` to test a cheaper model end-to-end, or switch back to **gpt-4o-mini** in the sidebar for higher-quality responses.

## Developer notes

- All structured field keys live in `src/keys.py` (`Keys` class). Reuse these constants for prompts, UI labels, and exports to avoid drift between modules.
- Set `DEBUG_LLM_RESPONSES=1` to display raw Responses API outputs directly in the Streamlit UI for troubleshooting JSON parsing. Keep this flag disabled in production to avoid noisy logs.
