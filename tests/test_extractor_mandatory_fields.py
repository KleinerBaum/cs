from __future__ import annotations

from pathlib import Path

from core.extractor import run_extraction
from core.schemas import RawInput
from src.keys import Keys


def test_run_extraction_populates_required_fields() -> None:
    text = Path("tests/fixtures/job_ad_mandatory_fields_de.txt").read_text(
        encoding="utf-8"
    )

    result = run_extraction(RawInput(text=text))
    fields = result.schema_fields

    assert fields[Keys.COMPANY_NAME] == "ACME GmbH"
    assert fields[Keys.LOCATION_CITY] == "Düsseldorf"
    assert fields[Keys.EMPLOYMENT_TYPE] == "Vollzeit"
    assert fields[Keys.EMPLOYMENT_CONTRACT] == "Unbefristet"
    assert fields[Keys.EMPLOYMENT_START] == "ASAP"
    assert fields[Keys.POSITION_TITLE] == "Senior Software Engineer"
    assert fields[Keys.POSITION_SENIORITY] == "Senior"
    assert fields[Keys.TEAM_DEPT] == "IT"

    assert result.location == "Düsseldorf"
