# Changelog

## Unreleased
- Added debug logging across the extraction/validation/pipeline stages and ensured pipeline failures return an `error` key with
  the underlying exception message for easier surfacing in clients.
- Normalised the Streamlit pipeline runner to use a typed payload model that maps legacy UI keys to canonical schema fields
  (`company_name`, `job_title`, `seniority`, etc.) before validation/enrichment.
- Added a deterministic pipeline orchestrator that chains extraction, validation, and optional enrichment for vacancy data.
- Added deterministic enrichment helpers for ESCO skills, boolean search strings, and salary bands based on seniority.
- Added a required-field validator that reports missing keys plus a rounded confidence score for vacancy intake quality gates.
- Added a deterministic text extractor adapter with schema aliases for ``content``/``source_type`` inputs and minimal skill/company parsing.
- Switched Responses API structured outputs to the `text.format` parameter so `openai==2.9.0` calls avoid `TypeError` during intake extraction.
- Enforced structured Responses API outputs for extraction/suggestion calls, preventing JSON fallbacks by default and improving parser reliability.
- Added a low-cost recovery call for intake parse/LLM failures that retries `fill_missing_fields_prompt` on prioritized paths with short backoff before falling back to heuristics.
- Hardened intake parsing so ValueError from malformed LLM JSON triggers a bilingual warning with a raw-response snippet while continuing with fallback data instead of aborting the flow.
- Removed duplicate field-constant module and legacy wizard catalog in favor of the centralized `src/keys.py` definitions and the active question engine.
- Added a themed salary visualization (min/avg/max) plus bilingual AI rationale beneath the checkbox selection, making the prediction easier to interpret alongside the applied factors.
- Added a selectable salary prediction section that gathers marked profile fields, triggers calculation on demand, and explains the resulting range via applied heuristics.
- Added flexible job-ad intake supporting URL fetches with HTML parsing, PDF/DOCX uploads, and pasted text inputs to prefill the wizard.
- Added bilingual multi-step wizard UI with per-step validation, navigation, and review before job-ad generation.
- Switched OpenAI authentication to Streamlit secrets/ENV, added UI language/theme toggles, and applied consistent theming for light/dark modes.
- Improved ESCO skill suggestions with language auto-detection, safer session-state updates for hard-skill injection, and clearer optional English job-title labelling.
- Refreshed the UI with a branded hero background and fixed pulsating logo, ensuring consistent visibility across all wizard steps.
- Clarified OpenAI key setup: set `OPENAI_API_KEY` in the environment or Streamlit secrets before starting, and surface a clearer in-app message when the key is missing.
- Fixed the theme toggle to rely on the selectbox return value instead of manual session-state writes, preventing Streamlit errors when switching modes.
- Removed the unsupported `temperature` parameter from GPT-5-mini Responses API calls to avoid HTTP 400 errors during extraction, follow-up generation, and translation.
- Harmonised the branding by resizing the pulsating logo badge and applying a teal-slate color palette across light/dark themes and CTAs.
- Modernised the sidebar with themed cards, icon-labelled section headers, and clearer grouping for display settings, assistants, and reset actions.
- Improved PDF/DOCX ingestion: preserve bullet/layout spacing, keep paragraph breaks, and surface a bilingual hint when uploads look like scanned image PDFs without extractable text.
- Hardened job-ad extraction so Pflichtfelder (job title, employment type, contract type, primary city, required languages) are prioritised, with a second LLM pass plus heuristics to backfill missing values.
- Added automatic AI suggestions for still-empty required or optional fields, marking them with dedicated provenance so users can review and edit the proposed values quickly.
- Switched the default OpenAI model to `gpt-4o-mini`, added `OPENAI_MODEL` overrides plus a bilingual sidebar selector, and covered model fallback/resolution with unit tests.
- Added a `DEBUG_LLM_RESPONSES` toggle that surfaces raw Responses API payloads in the UI to diagnose malformed JSON before parsing.
- Added targeted intake error handling for invalid AI configurations and retry/backoff guidance on network or timeout failures.
