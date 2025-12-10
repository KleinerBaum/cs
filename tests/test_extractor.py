from __future__ import annotations

import pytest

from core.extractor import run_extraction
from core.schemas import RawInput


def test_extract_text_basic_fields():
    raw = RawInput(
        source_type="text",
        content="Senior Data Scientist at ACME AG using Python and Pandas",
    )

    result = run_extraction(raw)

    assert result.seniority == "Senior"
    assert result.company in {"ACME", "ACME AG"}
    assert result.must_have_skills == ["Python", "Pandas"]


def test_unknown_source_raises_valueerror():
    raw = RawInput(source_type="unknown", content="No matching extractor")

    with pytest.raises(ValueError):
        run_extraction(raw)
