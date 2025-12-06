from __future__ import annotations

from typing import Any

LANG_DE = "de"
LANG_EN = "en"
SUPPORTED_LANGS = (LANG_DE, LANG_EN)

_STRINGS: dict[str, dict[str, str]] = {
    LANG_DE: {
        "app.tagline": "Dynamischer Informationsgewinnungs-Flow für Anforderungsprofile & Job-Ads",
        "sidebar.title": "Einstellungen",
        "sidebar.language": "Sprache",
        "sidebar.openai_key": "OpenAI API Key",
        "sidebar.model": "Model",
        "sidebar.use_esco": "ESCO-Vorschläge aktivieren",
        "sidebar.auto_ai": "AI-Follow-ups automatisch vorschlagen",
        "sidebar.reset": "Session zurücksetzen",
        "intake.title": "1) Ausgangsbasis importieren",
        "intake.subtitle": "URL eingeben, PDF/DOCX hochladen oder Text einfügen, um Felder automatisch zu prefillen.",
        "intake.url": "Job-Ad URL (optional)",
        "intake.file": "PDF/DOCX Upload (optional)",
        "intake.paste": "Stellenausschreibung einfügen (optional)",
        "intake.paste_placeholder": "Vollständigen Stellenausschreibungstext hier einfügen …",
        "intake.process": "Importieren & Extrahieren",
        "intake.source_preview": "Extrahierter Text (Vorschau)",
        "intake.tip": "Tipp: Wenn du nichts importierst, kannst du direkt manuell starten (oben Step auswählen).",
        "intake.need_source": "Bitte URL, Datei oder Text angeben (oder einfach weiterklicken und manuell ausfüllen).",
        "intake.single_source": "Bitte nur eine Quelle gleichzeitig nutzen (URL, Upload oder Freitext).",
        "intake.import_failed": "Import fehlgeschlagen",
        "intake.no_openai_key": "Kein OpenAI API Key gesetzt – Import ist erfolgt, aber ohne LLM-Extraktion.",
        "intake.extract_done": "Extraktion abgeschlossen.",
        "intake.updated_fields": "Aktualisierte Felder",
        "intake.extract_failed": "LLM-Extraktion fehlgeschlagen",
        "progress.missing_required": "Fehlende Pflichtfelder",
        "progress.ready": "Alle Pflichtfelder sind gefüllt.",
        "step.missing_in_step": "Fehlt in diesem Schritt",
        "nav.prev": "Zurück",
        "nav.next": "Weiter",
        "step.company": "Unternehmen",
        "step.team": "Team",
        "step.framework": "Rahmenbedingungen",
        "step.tasks": "Aufgaben",
        "step.skills": "Skills",
        "step.benefits": "Benefits",
        "step.process": "Recruiting Prozess",
        "step.review": "Review & Export",
        "ui.more_details": "Mehr Details (optional)",
        "ui.ai_suggest": "AI: Vorschläge generieren",
        "ui.translate_to_en": "AI: Englisch-Versionen erzeugen",
        "ui.translate_done": "Englisch-Felder aktualisiert",
        "ui.translate_failed": "Übersetzung fehlgeschlagen",
        "ui.translate_hint": "EN-Felder werden genutzt, wenn du UI/Output auf Englisch stellst.",
        "ui.ai_hint": "AI-Follow-ups erscheinen nur bei Lücken/Unsicherheiten und bleiben optional.",
        "ui.ai_followups_title": "AI follow-ups",
        "ai.followups_done": "AI follow-ups erstellt",
        "ai.followups_failed": "AI follow-ups fehlgeschlagen",
        "ui.esco_search": "ESCO: Suche",
        "ui.esco_pick": "ESCO: Treffer auswählen",
        "ui.esco_apply_skills": "ESCO-Skills übernehmen",
        "ui.empty": "—",
        "esco.title": "ESCO",
        "esco.query": "ESCO Suchbegriff",
        "esco.skills_select": "Skills (zum Hinzufügen auswählen)",
        "esco.caption": "ESCO liefert standardisierte Occupations/Skills (EU).",
        "esco.merge_success": "Skills wurden in 'Hard Skills optional' ergänzt.",
        "esco.error": "ESCO Fehler",
        "review.title": "Ergebnis",
        "review.profile_json": "Profil-JSON (NeedAnalysisProfile)",
        "review.job_ad": "Job-Ad Entwurf",
        "review.download_json": "JSON herunterladen",
        "review.download_md": "Markdown herunterladen",
        "review.download_docx": "DOCX herunterladen",
        "review.edit_hint": "Du kannst den Entwurf unten bearbeiten, bevor du exportierst.",
        "review.provenance_title": "Provenance",
        "review.provenance_extracted": "Extracted",
        "review.provenance_ai": "AI suggestions",
        "provenance.user": "User",
        "provenance.extracted": "Extracted",
        "provenance.ai_suggestion": "AI suggestion",
        "field.generic": "Wert",
    },
    LANG_EN: {
        "app.tagline": "Dynamic requirement-gathering flow for job requisitions & job ads",
        "sidebar.title": "Settings",
        "sidebar.language": "Language",
        "sidebar.openai_key": "OpenAI API Key",
        "sidebar.model": "Model",
        "sidebar.use_esco": "Enable ESCO suggestions",
        "sidebar.auto_ai": "Suggest AI follow-ups automatically",
        "sidebar.reset": "Reset session",
        "intake.title": "1) Import a starting point",
        "intake.subtitle": "Paste a URL, upload a PDF/DOCX, or drop the text directly to prefill fields.",
        "intake.url": "Job ad URL (optional)",
        "intake.file": "PDF/DOCX upload (optional)",
        "intake.paste": "Paste job ad text (optional)",
        "intake.paste_placeholder": "Insert the full job ad text here …",
        "intake.process": "Import & extract",
        "intake.source_preview": "Extracted text (preview)",
        "intake.tip": "Tip: If you don't import anything, you can start manually (select a step above).",
        "intake.need_source": "Please provide a URL, file, or text (or just continue and fill everything manually).",
        "intake.single_source": "Please use only one source at a time (URL, upload, or pasted text).",
        "intake.import_failed": "Import failed",
        "intake.no_openai_key": "No OpenAI API key set – import succeeded, but without LLM extraction.",
        "intake.extract_done": "Extraction finished.",
        "intake.updated_fields": "Updated fields",
        "intake.extract_failed": "LLM extraction failed",
        "progress.missing_required": "Missing required fields",
        "progress.ready": "All required fields are filled.",
        "step.missing_in_step": "Missing in this step",
        "nav.prev": "Back",
        "nav.next": "Next",
        "step.company": "Company",
        "step.team": "Team",
        "step.framework": "Framework",
        "step.tasks": "Responsibilities",
        "step.skills": "Skills",
        "step.benefits": "Benefits",
        "step.process": "Recruiting process",
        "step.review": "Review & export",
        "ui.more_details": "More details (optional)",
        "ui.ai_suggest": "AI: generate suggestions",
        "ui.translate_to_en": "AI: Generate English variants",
        "ui.translate_done": "English fields updated",
        "ui.translate_failed": "Translation failed",
        "ui.translate_hint": "EN fields are used when you switch the UI/output to English.",
        "ui.ai_hint": "AI follow-ups only appear for gaps/uncertainties and remain optional.",
        "ui.ai_followups_title": "AI follow-ups",
        "ai.followups_done": "AI follow-ups generated",
        "ai.followups_failed": "AI follow-ups failed",
        "ui.esco_search": "ESCO: search",
        "ui.esco_pick": "ESCO: select result",
        "ui.esco_apply_skills": "Apply ESCO skills",
        "ui.empty": "—",
        "esco.title": "ESCO",
        "esco.query": "ESCO query",
        "esco.skills_select": "Skills (select to add)",
        "esco.caption": "ESCO provides standardized occupations/skills (EU).",
        "esco.merge_success": "Skills were added to 'Hard skills optional'.",
        "esco.error": "ESCO error",
        "review.title": "Result",
        "review.profile_json": "Profile JSON (NeedAnalysisProfile)",
        "review.job_ad": "Job ad draft",
        "review.download_json": "Download JSON",
        "review.download_md": "Download Markdown",
        "review.download_docx": "Download DOCX",
        "review.edit_hint": "You can edit the draft below before exporting.",
        "review.provenance_title": "Provenance",
        "review.provenance_extracted": "Extracted",
        "review.provenance_ai": "AI suggestions",
        "provenance.user": "User",
        "provenance.extracted": "Extracted",
        "provenance.ai_suggestion": "AI suggestion",
        "field.generic": "Value",
    },
}

_OPTION_LABELS: dict[str, dict[str, dict[str, str]]] = {
    "work_policy": {
        LANG_DE: {"onsite": "Vor Ort", "hybrid": "Hybrid", "remote": "Remote"},
        LANG_EN: {"onsite": "On-site", "hybrid": "Hybrid", "remote": "Remote"},
    },
    "employment_type": {
        LANG_DE: {
            "full_time": "Vollzeit",
            "part_time": "Teilzeit",
            "contractor": "Freelance/Contractor",
            "intern": "Praktikum",
        },
        LANG_EN: {
            "full_time": "Full-time",
            "part_time": "Part-time",
            "contractor": "Contractor",
            "intern": "Internship",
        },
    },
    "contract_type": {
        LANG_DE: {"permanent": "Unbefristet", "fixed_term": "Befristet"},
        LANG_EN: {"permanent": "Permanent", "fixed_term": "Fixed-term"},
    },
    "seniority": {
        LANG_DE: {
            "junior": "Junior",
            "mid": "Mid-level",
            "senior": "Senior",
            "lead": "Lead",
            "head": "Head",
            "c_level": "C-Level",
        },
        LANG_EN: {
            "junior": "Junior",
            "mid": "Mid-level",
            "senior": "Senior",
            "lead": "Lead",
            "head": "Head",
            "c_level": "C-level",
        },
    },
    "salary_period": {
        LANG_DE: {"year": "Jahr", "month": "Monat", "hour": "Stunde"},
        LANG_EN: {"year": "Year", "month": "Month", "hour": "Hour"},
    },
}


def t(lang: str, key: str, default: str | None = None) -> str:
    if lang not in _STRINGS:
        lang = LANG_EN
    return _STRINGS.get(lang, {}).get(key, default or key)


def option_label(lang: str, group: str, value: str) -> str:
    if lang not in SUPPORTED_LANGS:
        lang = LANG_EN
    return _OPTION_LABELS.get(group, {}).get(lang, {}).get(value, value)


def options_for(lang: str, group: str) -> list[tuple[str, str]]:
    if lang not in SUPPORTED_LANGS:
        lang = LANG_EN
    mapping = _OPTION_LABELS.get(group, {}).get(lang, {})
    return list(mapping.items())


def as_lang(lang: Any) -> str:
    return lang if lang in SUPPORTED_LANGS else LANG_EN
