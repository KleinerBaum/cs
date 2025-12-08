# Changelog

## Unreleased
- Added flexible job-ad intake supporting URL fetches with HTML parsing, PDF/DOCX uploads, and pasted text inputs to prefill the wizard.
- Added bilingual multi-step wizard UI with per-step validation, navigation, and review before job-ad generation.
- Switched OpenAI authentication to Streamlit secrets/ENV, added UI language/theme toggles, and applied consistent theming for light/dark modes.
- Improved ESCO skill suggestions with language auto-detection, safer session-state updates for hard-skill injection, and clearer optional English job-title labelling.
- Refreshed the UI with a branded hero background and fixed pulsating logo, ensuring consistent visibility across all wizard steps.
- Clarified OpenAI key setup: set `OPENAI_API_KEY` in the environment or Streamlit secrets before starting, and surface a clearer in-app message when the key is missing.
- Fixed the theme toggle to rely on the selectbox return value instead of manual session-state writes, preventing Streamlit errors when switching modes.
- Removed the unsupported `temperature` parameter from GPT-5-mini Responses API calls to avoid HTTP 400 errors during extraction, follow-up generation, and translation.
- Harmonised the branding by resizing the pulsating logo badge and applying a teal-slate color palette across light/dark themes and CTAs.
