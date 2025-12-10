# CognitiveStaffing – Need Analysis Wizard (Streamlit)

A modular Streamlit app for line managers to transform an existing job ad (URL, PDF, DOCX, or pasted text) into a structured **NeedAnalysisProfile** and an exportable job ad draft.

## Multi-page wizard (Profile → Summary)

The wizard now uses native Streamlit multi-page navigation (`app.py` + `pages/*`) with distinct steps and validation per section:

- **01 Profile:** company name, city, employment/contract type, start date, remote policy.
- **02 Role:** title, seniority, department, direct reports, work schedule, and a one-click summary generator.
- **03 Skills:** tasks, core skills, and nice-to-haves split into tabs with bilingual suggestion buttons.
- **04 Compensation:** currency and salary range validation (min ≤ max), benefits, variable %, relocation, visa.
- **05 Forecast:** configurable conversion rates and time-to-fill Monte-Carlo simulation with KPI tiles and histogram.
- **99 Summary:** section status (✅/⚠️) plus JSON and Markdown exports of the consolidated NeedAnalysisProfile.

Navigation buttons prevent advancing until the current section is valid. All inputs persist in `st.session_state`, so you can revisit any page without losing data.

The landing page now includes a bilingual intake card beneath the language selector. Provide exactly one source (job-ad URL, PDF/DOCX upload, or pasted text) and click **Autofill** to pre-populate company, seniority, and initial must-have skills before entering the Profile step.

## Ingestion fidelity (DE/EN)

- PDF uploads use PyMuPDF with ligature and whitespace preservation so that bullet lists, headings, and special characters remain intact in the extracted raw text.
- DOCX uploads now keep blank lines between paragraphs to retain list and section boundaries when populating the wizard.
- If a PDF contains only images (likely a scan) and no extractable text, the import step surfaces a bilingual hint to provide a searchable PDF or run OCR first.

## Multi-step wizard (DE/EN)

The app features a bilingual, multi-step wizard to collect all required fields before generating a job ad. Each section (company, team, position, framework, tasks, skills, benefits, process, and review) is presented step-by-step with forward/backward navigation. Required fields ("Pflichtfelder") are marked with an asterisk and highlighted if missing. All UI labels and generated job-ad content adapt to the selected language (German or English).

- **Bilingual UI:** Use the sidebar language selector to switch between German and English labels. The final job ad draft will be generated in the chosen language.
- **English field translation:** In the "Skills" step, you can automatically translate key fields (job title, required hard/soft skills, tools) to English by clicking the **"AI: Generate English versions"** button. This uses the OpenAI API to fill optional English fields (marked as "*English version, optional*"). If you switch the UI language to English, these translated values will be used in the job ad output.
- **Dynamic forms:** Each step groups a set of questions (basic and optional advanced fields). Advanced fields are hidden under *"More details (optional)"* to keep the UI uncluttered. Conditional fields (e.g., travel percentage if travel is required) only appear when relevant.
- **Calm validation:** Required-field warnings stay hidden on initial load and only appear after you attempt an action where the missing inputs matter (e.g., clicking **Next** with empty required fields). Errors now render inline beneath the affected inputs so you can fix them without hunting for a global banner.
- **Session state:** Form data persists in `st.session_state` as you navigate. You can reset the session via the sidebar. The
  centralized `AppState` can be reconstructed from a NeedAnalysisProfile mapping and exported back for deterministic pipeline
  runs, keeping UI inputs and payloads aligned.
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
- **Responses API compatibility:** Structured extraction uses the Responses API `text.format` field (supported in `openai==2.9.0`) to request JSON outputs without raising type errors during intake.
- **English translation:** As noted, the LLM can translate key fields to English for international job ads. The translated values are stored in parallel fields (e.g., `job_title_en`) and used when you switch to English output.
- **Scoped AI buttons:** Dedicated buttons now trigger exactly one action each (role summary, tasks, core skills, nice-to-have skills) and leave other fields untouched. Unsupported sampling parameters are stripped before sending the payload so models that do not accept `temperature` or `top_p` still work.
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

## Extractor adapters

Use the deterministic extractor layer to turn raw inputs into minimal fields without LLM calls. Example:

```bash
python - <<'EOF'
from core.extractor import run_extraction
from core.schemas import RawInput

result = run_extraction(
    RawInput(source_type="text", content="Senior Data Scientist at ACME AG using Python")
)
print(result)
EOF
```

## Pipeline orchestrator

Use `pipeline.py` to chain extraction, validation, and enrichment in one deterministic call. Provide a `RawInput` plus the
required-field payload; enrichment runs only when no required fields are missing. The pipeline now logs debug output for each
stage and returns an `error` key with the exception message if any step fails, ensuring the caller can surface a clear
problem description. Run `python pipeline.py` for a quick manual smoke test of the orchestration.

This returns the parsed seniority, company, and must-have skills for the supplied snippet.

- **Streamlit runner payloads:** The lightweight `/ui/steps/run.py` page now feeds the pipeline with a typed
  `PipelinePayload` model that normalizes legacy UI keys (e.g., `extracted_company`, `parsed_title`) into
  the canonical schema fields (`company_name`, `job_title`, `seniority`, etc.).

### CLI runner (deterministic pipeline)

For local debugging without Streamlit, run the deterministic pipeline directly via the CLI helper:

```bash
python cli.py --content "Senior Python Engineer at LEGO AG"
```

You can optionally pass a validation payload JSON file for required fields:

```bash
python cli.py --content "Senior Python Engineer at LEGO AG" \
  --payload scripts/sample_payload.json
```

The script prints the pipeline result as pretty-printed JSON so you can inspect extraction, validation, enrichment, or
errors at a glance.

## Enrichment helpers (DE/EN)

Use the pure enrichment helpers in `core.enricher` to derive a small ESCO skill set (first ten skills), build a boolean search string, and suggest a salary band for Mid/Senior roles (Ermittlung der ersten zehn ESCO-Skills, Aufbau eines Boolean-Strings und Gehaltsband für Mid/Senior).

```python
from core.enricher import run_enrichment
from core.extractor import ExtractionResult

result = run_enrichment(ExtractionResult(seniority="Senior", must_have_skills=["Python", "SQL"]))
print(result)
```

## Developer notes

- All structured field keys live in `src/keys.py` (`Keys` class). Reuse these constants for prompts, UI labels, and exports to avoid drift between modules.
- A centralized, typed `AppState` (see `state.py`) mirrors the Streamlit session, grouping profile, role, skills, compensation, and forecast data. Validation helpers in `validators.py` use the same keys to surface bilingual, per-step errors.
- Set `DEBUG_LLM_RESPONSES=1` to display raw Responses API outputs directly in the Streamlit UI for troubleshooting JSON parsing. Keep this flag disabled in production to avoid noisy logs.
- A lightweight validator in `core.validator.validate_required_fields` reports missing required fields and a confidence score (1 - missing/total, rounded to two decimals) so ingestion steps can surface clear QA signals.
- The deterministic text extractor in `core.extractor.TextExtractor` now captures company names (with and without legal suffixes), job titles and seniority cues, basic location/employment-type hints, responsibilities, and common DE/EN skills to prefill at least half of the wizard fields from typical job ads.
