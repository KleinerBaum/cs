from core.profile_extractor import extract_profile_required_fields


def test_extract_company_german() -> None:
    text = "Über uns bei Beispiel GmbH: Wir wachsen rasant und suchen Talente."
    result = extract_profile_required_fields(text)

    assert result.company_name == "Beispiel"


def test_extract_company_english() -> None:
    text = "Join ACME Inc hiring new team members across Europe."
    result = extract_profile_required_fields(text)

    assert result.company_name == "ACME"


def test_extract_city_labelled_german() -> None:
    text = "Hauptstandort: München\nArbeitszeit: Vollzeit"
    result = extract_profile_required_fields(text)

    assert result.primary_city == "München"


def test_extract_city_inline_english() -> None:
    text = "Location: Hamburg, Germany"
    result = extract_profile_required_fields(text)

    assert result.primary_city == "Hamburg"


def test_extract_employment_type_german() -> None:
    text = "Arbeitszeit: Vollzeit mit Team-Events"
    result = extract_profile_required_fields(text)

    assert result.employment_type == "full_time"


def test_extract_employment_type_english_part_time() -> None:
    text = "We offer a part-time setup with flexibility."
    result = extract_profile_required_fields(text)

    assert result.employment_type == "part_time"


def test_extract_contract_type_german() -> None:
    text = "Vertragsart: unbefristet mit Probezeit"
    result = extract_profile_required_fields(text)

    assert result.contract_type == "permanent"


def test_extract_contract_type_english() -> None:
    text = "This is a fixed-term contract for 12 months."
    result = extract_profile_required_fields(text)

    assert result.contract_type == "fixed_term"


def test_extract_start_date_specific() -> None:
    text = "Startdatum: 01.09.2024 erwartet"
    result = extract_profile_required_fields(text)

    assert result.start_date == "01.09.2024"


def test_extract_start_date_asap() -> None:
    text = "Start: ab sofort möglich"
    result = extract_profile_required_fields(text)

    assert result.start_date == "ASAP"
