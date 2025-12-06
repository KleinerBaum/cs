# app.py - Streamlit application
import streamlit as st
import openai
from esco_utils import fetch_essential_skills

st.set_page_config(
    page_title="Job Description Generator", page_icon="📝", layout="wide"
)

st.title("Job Description Generator")
st.markdown(
    "Dieses Streamlit-Tool generiert eine Stellenanzeige basierend auf strukturierten Eingaben. "
    "Es nutzt die OpenAI Chat API ([GPT-5-mini Modell](https://platform.openai.com/docs/models/gpt-5-mini)) für die Textgenerierung und die ESCO-API für Skill-Vorschläge."
)

# OpenAI API key input (from secrets or user input)
api_key = st.secrets.get("OPENAI_API_KEY", None) if hasattr(st, "secrets") else None
if not api_key:
    api_key = st.sidebar.text_input("OpenAI API-Key eingeben", type="password")
if api_key:
    openai.api_key = api_key

# LLM model to use
MODEL_NAME = (
    "gpt-3.5-turbo"  # Standardmodell (GPT-5-mini alias gemäß OpenAI-Dokumentation)
)

# --- Company section ---
st.header("Unternehmen")
company_name = st.text_input("Firmenname (Pflicht)", key="company_name")
company_website = st.text_input("Webseite", key="company_website")
company_industry = st.text_input("Branche", key="company_industry")
company_size = st.text_input("Unternehmensgröße", key="company_size")
company_hq = st.text_input("Hauptsitz (Ort)", key="company_hq")
company_desc = st.text_area("Kurzbeschreibung des Unternehmens", key="company_desc")
company_contact_name = st.text_input(
    "Ansprechperson (Name)", key="company_contact_name"
)
company_contact_email = st.text_input(
    "Ansprechperson (E-Mail, Pflicht)", key="company_contact_email"
)

# --- Position / Team section ---
st.header("Position und Team")
position_title = st.text_input("Stellentitel (Englisch, Pflicht)", key="position_title")
position_family = st.text_input("Job-Familie / Berufsfeld", key="position_family")
position_seniority = st.text_input(
    "Senioritätslevel (Pflicht)", key="position_seniority"
)
position_summary = st.text_area(
    "Rollenbeschreibung / Aufgabenüberblick", key="position_summary"
)
position_reports_to = st.text_input("Vorgesetzte Position", key="position_reports_to")
position_people_mgmt = st.text_input(
    "Verantwortung (Teamleitung)", key="position_people_mgmt"
)
position_direct_reports = st.text_input(
    "Direkt unterstellte Mitarbeiter (Anzahl)", key="position_direct_reports"
)
team_dept = st.text_input("Abteilung", key="team_dept")
team_name = st.text_input("Teamname", key="team_name")
team_reporting_line = st.text_input(
    "Übergeordnete Struktur / Reporting Line", key="team_reporting_line"
)
team_headcount_current = st.text_input(
    "Aktuelle Teamgröße", key="team_headcount_current"
)
team_headcount_target = st.text_input("Geplante Teamgröße", key="team_headcount_target")
team_tools = st.text_input("Kollaborationstools im Team", key="team_tools")

# --- Location / Employment section ---
st.header("Standort und Anstellung")
location_work_policy = st.text_input(
    "Arbeitsmodell (z.B. vor Ort, Hybrid, Remote)", key="location_work_policy"
)
location_city = st.text_input("Dienstsitz / Ort (Pflicht)", key="location_city")
location_remote_scope = st.text_input(
    "Remote-Anteil / -Möglichkeiten", key="location_remote_scope"
)
location_timezone = st.text_input("Zeitzonenanforderungen", key="location_timezone")
location_travel_required = st.text_input(
    "Reisetätigkeit erforderlich?", key="location_travel_required"
)
location_travel_pct = st.text_input("Reiseanteil (%)", key="location_travel_pct")
employment_type = st.text_input(
    "Anstellungsart (Pflicht, z.B. Vollzeit/Teilzeit)", key="employment_type"
)
employment_contract = st.text_input(
    "Vertragsart (Pflicht, z.B. unbefristet)", key="employment_contract"
)
employment_start = st.text_input("Startdatum (Pflicht)", key="employment_start")
employment_visa = st.text_input(
    "Visa-Sponsoring / Arbeitserlaubnis", key="employment_visa"
)

# --- Compensation / Benefits section ---
st.header("Vergütung und Benefits")
salary_provided = st.text_input("Gehalt angegeben? (Ja/Nein)", key="salary_provided")
salary_min = st.text_input("Gehaltsspanne Minimum", key="salary_min")
salary_max = st.text_input("Gehaltsspanne Maximum", key="salary_max")
salary_currency = st.text_input("Währung (z.B. EUR)", key="salary_currency")
salary_period = st.text_input(
    "Zeitraum des Gehalts (z.B. jährlich)", key="salary_period"
)
benefits_items = st.text_area(
    "Benefits (Pflicht - eine pro Zeile)", key="benefits_items"
)

# --- Responsibilities / Requirements section ---
st.header("Aufgaben und Anforderungen")
responsibilities_items = st.text_area(
    "Aufgaben / Verantwortlichkeiten (Pflicht - eine pro Zeile)",
    key="responsibilities_items",
)
hard_req = st.text_area(
    "Fachliche Anforderungen (Pflicht - Englisch, eine pro Zeile)", key="hard_req"
)
if st.button("Typische Hard Skills vorschlagen (ESCO)"):
    if not position_title or not position_title.strip():
        st.warning("Bitte zuerst einen Stellentitel eingeben.")
    else:
        skills = fetch_essential_skills(position_title.strip(), language="en")
        if skills:
            st.session_state["hard_req"] = "\n".join(skills)
            st.success("Typische Hard Skills wurden eingetragen.")
        else:
            st.warning("Keine passenden Skills in ESCO gefunden.")
hard_opt = st.text_area("Optionale Hard Skills (eine pro Zeile)", key="hard_opt")
soft_req = st.text_area(
    "Soft Skills (Pflicht - Englisch, eine pro Zeile)", key="soft_req"
)
lang_req = st.text_area("Sprachkenntnisse (Pflicht - eine pro Zeile)", key="lang_req")
tools_req = st.text_area(
    "Tools & Technologien (Pflicht - Englisch, eine pro Zeile)", key="tools_req"
)
must_not = st.text_area(
    "Ausschlusskriterien (optional - eine pro Zeile)", key="must_not"
)

# --- Recruiting process section ---
st.header("Bewerbungsprozess")
process_stages = st.text_area("Interviewphasen (eine pro Zeile)", key="process_stages")
process_instructions = st.text_area(
    "Bewerbungsanweisungen / Hinweise", key="process_instructions"
)
process_contact = st.text_input("Kontakt für Bewerbung (E-Mail)", key="process_contact")
process_timeline = st.text_input(
    "Geplanter Auswahlzeitraum / Timeline", key="process_timeline"
)

# --- Generate job description using OpenAI LLM ---
if st.button("Stellenanzeige generieren"):
    if not api_key:
        st.error("Es wurde kein OpenAI API-Key angegeben.")
        st.stop()
    # Check required fields
    missing = []
    if not company_name or not company_name.strip():
        missing.append("Firmenname")
    if not company_contact_email or not company_contact_email.strip():
        missing.append("Kontakt E-Mail")
    if not position_title or not position_title.strip():
        missing.append("Stellentitel")
    if not position_seniority or not position_seniority.strip():
        missing.append("Senioritätslevel")
    if not location_city or not location_city.strip():
        missing.append("Dienstsitz/Ort")
    if not employment_type or not employment_type.strip():
        missing.append("Anstellungsart")
    if not employment_contract or not employment_contract.strip():
        missing.append("Vertragsart")
    if not employment_start or not employment_start.strip():
        missing.append("Startdatum")
    if not benefits_items or not benefits_items.strip():
        missing.append("Benefits")
    if not responsibilities_items or not responsibilities_items.strip():
        missing.append("Aufgaben")
    if not hard_req or not hard_req.strip():
        missing.append("Fachliche Anforderungen")
    if not soft_req or not soft_req.strip():
        missing.append("Soft Skills")
    if not lang_req or not lang_req.strip():
        missing.append("Sprachkenntnisse")
    if not tools_req or not tools_req.strip():
        missing.append("Tools & Technologien")
    if missing:
        st.error("Bitte füllen Sie alle Pflichtfelder aus: " + ", ".join(missing))
        st.stop()

    # Parse multiline inputs into lists
    def parse_list(text: str):
        if not text:
            return []
        if "\n" in text:
            items = [i.strip() for i in text.splitlines() if i.strip()]
        elif "," in text:
            items = [i.strip() for i in text.split(",") if i.strip()]
        else:
            items = [text.strip()] if text.strip() else []
        return items

    responsibilities_list = parse_list(responsibilities_items)
    benefits_list = parse_list(benefits_items)
    hard_req_list = parse_list(hard_req)
    soft_req_list = parse_list(soft_req)
    lang_req_list = parse_list(lang_req)
    tools_req_list = parse_list(tools_req)
    hard_opt_list = parse_list(hard_opt)
    must_not_list = parse_list(must_not)
    # Build prompt from inputs
    prompt_lines = []
    prompt_lines.append(f"Unternehmen: {company_name.strip()}")
    if company_industry:
        prompt_lines.append(f"Branche: {company_industry.strip()}")
    if company_size:
        prompt_lines.append(f"Unternehmensgröße: {company_size.strip()}")
    if company_hq:
        prompt_lines.append(f"Hauptsitz: {company_hq.strip()}")
    if company_desc:
        prompt_lines.append(f"Unternehmensbeschreibung: {company_desc.strip()}")
    prompt_lines.append(
        f"Position: {position_title.strip()} (Seniorität: {position_seniority.strip()})"
    )
    if position_family:
        prompt_lines.append(f"Job-Familie: {position_family.strip()}")
    if position_reports_to:
        prompt_lines.append(f"Vorgesetzte Position: {position_reports_to.strip()}")
    if position_people_mgmt:
        prompt_lines.append(f"Führungsverantwortung: {position_people_mgmt.strip()}")
    if position_direct_reports:
        prompt_lines.append(f"Direkt unterstellte: {position_direct_reports.strip()}")
    if (
        team_dept
        or team_name
        or team_reporting_line
        or team_headcount_current
        or team_headcount_target
        or team_tools
    ):
        prompt_lines.append("Team:")
        if team_dept:
            prompt_lines.append(f"- Abteilung: {team_dept.strip()}")
        if team_name:
            prompt_lines.append(f"- Teamname: {team_name.strip()}")
        if team_reporting_line:
            prompt_lines.append(f"- Übergeordnet: {team_reporting_line.strip()}")
        if team_headcount_current:
            prompt_lines.append(
                f"- Aktuelle Teamgröße: {team_headcount_current.strip()}"
            )
        if team_headcount_target:
            prompt_lines.append(
                f"- Geplante Teamgröße: {team_headcount_target.strip()}"
            )
        if team_tools:
            prompt_lines.append(f"- Tools im Team: {team_tools.strip()}")
    prompt_lines.append(f"Einsatzort: {location_city.strip()}")
    if location_work_policy:
        prompt_lines.append(f"Arbeitsmodell: {location_work_policy.strip()}")
    if location_remote_scope:
        prompt_lines.append(f"Remote-Anteil: {location_remote_scope.strip()}")
    if location_timezone:
        prompt_lines.append(f"Zeitzonen: {location_timezone.strip()}")
    if location_travel_required:
        prompt_lines.append(f"Reisebereitschaft: {location_travel_required.strip()}")
    if location_travel_pct:
        prompt_lines.append(f"Reiseanteil: {location_travel_pct.strip()}")
    prompt_lines.append(f"Anstellungsart: {employment_type.strip()}")
    prompt_lines.append(f"Vertragsart: {employment_contract.strip()}")
    prompt_lines.append(f"Startdatum: {employment_start.strip()}")
    if employment_visa:
        prompt_lines.append(f"Visa/Arbeitserlaubnis: {employment_visa.strip()}")
    if salary_provided and salary_provided.strip().lower() in ["ja", "yes"]:
        if salary_min or salary_max:
            range_text = (
                (salary_min.strip() if salary_min else "?")
                + " - "
                + (salary_max.strip() if salary_max else "?")
            )
            if salary_currency:
                range_text += " " + salary_currency.strip()
            if salary_period:
                range_text += f" pro {salary_period.strip()}"
            prompt_lines.append(f"Gehalt: {range_text}")
    if benefits_list:
        prompt_lines.append("Benefits:")
        for b in benefits_list:
            prompt_lines.append(f"- {b}")
    if responsibilities_list:
        prompt_lines.append("Aufgaben:")
        for r in responsibilities_list:
            prompt_lines.append(f"- {r}")
    req_lines = []
    if hard_req_list:
        req_lines.append(f"Fachliche Fähigkeiten: {', '.join(hard_req_list)}")
    if soft_req_list:
        req_lines.append(f"Soziale Kompetenzen: {', '.join(soft_req_list)}")
    if tools_req_list:
        req_lines.append(f"Tools und Technologien: {', '.join(tools_req_list)}")
    if lang_req_list:
        req_lines.append(f"Sprachen: {', '.join(lang_req_list)}")
    if hard_opt_list:
        req_lines.append(f"Optional: {', '.join(hard_opt_list)}")
    if must_not_list:
        req_lines.append(f"Ausschlusskriterien: {', '.join(must_not_list)}")
    if req_lines:
        prompt_lines.append("Anforderungen:")
        for line in req_lines:
            prompt_lines.append(f"- {line}")
    if process_stages or process_instructions or process_contact or process_timeline:
        prompt_lines.append("Prozess:")
        if process_stages:
            stage_list = parse_list(process_stages)
            if stage_list:
                prompt_lines.append("  Phasen:")
                for s in stage_list:
                    prompt_lines.append(f"  - {s}")
        if process_instructions:
            prompt_lines.append(f"  Hinweise: {process_instructions.strip()}")
        if process_contact:
            prompt_lines.append(f"  Kontakt: {process_contact.strip()}")
        if process_timeline:
            prompt_lines.append(f"  Zeitrahmen: {process_timeline.strip()}")
    prompt = "\n".join(prompt_lines)
    messages = [
        {
            "role": "system",
            "content": "Du bist ein erfahrener HR-Experte und schreibst professionelle Stellenanzeigen auf Deutsch.",
        },
        {"role": "user", "content": prompt},
    ]
    try:
        response = openai.ChatCompletion.create(
            model=MODEL_NAME, messages=messages, temperature=0.7, max_tokens=1024
        )
        job_ad = response["choices"][0]["message"]["content"].strip()
        st.subheader("Generierte Stellenanzeige:")
        st.markdown(job_ad)
        st.download_button(
            "Als Textdatei herunterladen", job_ad, file_name="Stellenanzeige.txt"
        )
    except Exception as e:
        st.error(f"Fehler bei der Generierung: {e}")
