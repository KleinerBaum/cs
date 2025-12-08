# CognitiveStaffing – Need Analysis Wizard (Streamlit)

A modular Streamlit app for line managers to transform an existing job ad (URL, PDF, DOCX, or pasted text) into a structured **NeedAnalysisProfile** and an exportable job ad draft.

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

- **Field extraction:** In the *Import* step, if an OpenAI API key is configured, the app will attempt to extract structured information from the provided job ad text using an LLM (via OpenAI model **gpt-5-mini**). Detected fields (e.g. company contact email or website) are prefilled with a provenance tag "Extracted". This speeds up the form-filling process.
- **Follow-up questions:** At each step, you can click **"AI: Generate suggestions"** to have the LLM propose follow-up questions for any missing or uncertain fields. These AI-generated questions (in both DE and EN) will appear below the form, allowing you to fill in additional details. This feature is optional and only triggers if relevant fields are missing. You can also enable auto-generation of follow-ups via the sidebar ("Suggest AI follow-ups automatically").
- **English translation:** As noted, the LLM can translate key fields to English for international job ads. The translated values are stored in parallel fields (e.g., `job_title_en`) and used when you switch to English output.
- **Fixed model selection:** The app always uses OpenAI **gpt-5-mini** for extraction, follow-ups, and translations; the sidebar no longer exposes a model selector to avoid accidental misconfiguration.
- **Model compatibility:** The Responses API for **gpt-5-mini** does not accept a `temperature` parameter. The app therefore relies on the model defaults and omits unsupported sampling parameters to avoid HTTP 400 errors during extraction, follow-up generation, and translation.

## Configuration

Before launching the app, set the OpenAI API key via Streamlit secrets or an environment variable. The UI does **not** expose a text field for the API key; if no key is configured, the app will stop with an error message.

You can add the key to `.streamlit/secrets.toml` or as an environment variable:

```toml
OPENAI_API_KEY = "sk-..." 

# or under a [general] section:
[general]
OPENAI_API_KEY = "sk-..."
