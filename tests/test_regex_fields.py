from __future__ import annotations

from pathlib import Path

from core import regex_fields as rf


FIXTURE_PATH = Path("tests/fixtures/job_ad_mandatory_fields_de.txt")


def _load_fixture() -> str:
    return FIXTURE_PATH.read_text(encoding="utf-8")


def test_clean_city_strips_trailing_stopwords() -> None:
    assert rf.clean_city("Düsseldorf eine") == "Düsseldorf"


def test_extractors_from_fixture() -> None:
    text = _load_fixture()

    assert rf.extract_company_name(text) == "ACME GmbH"
    assert rf.extract_primary_city(text) == "Düsseldorf"
    assert rf.extract_employment_type(text) == "Vollzeit"
    assert rf.extract_contract_type(text) == "Unbefristet"
    start_date = rf.extract_desired_start_date(text)
    assert start_date == {"raw": "ab sofort", "normalized": "ASAP"}
    assert rf.extract_job_title(text) == "Senior Software Engineer"
    assert rf.extract_seniority(text) == "Senior"
    assert rf.extract_department(text) == "IT"


def test_extract_desired_start_date_parses_numeric_date() -> None:
    text = "Start: 12.01.2025"

    result = rf.extract_desired_start_date(text)

    assert result == {"raw": "12.01.2025", "normalized": "2025-01-12"}


def test_extract_employment_type_prefers_first_match() -> None:
    text = "Wir suchen dich in Teilzeit oder Vollzeit"

    assert rf.extract_employment_type(text) == "Teilzeit"


def test_extract_contract_type_handles_fixed_term() -> None:
    text = "Vertragsart: Befristet für 12 Monate"

    assert rf.extract_contract_type(text) == "Befristet"
