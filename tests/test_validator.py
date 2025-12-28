from __future__ import annotations

import pytest

from core.validator import REQUIRED, validate_required_fields


@pytest.fixture()
def full_payload() -> dict[str, str]:
    return {field: "value" for field in REQUIRED}


def test_missing_all_fields():
    result = validate_required_fields({})

    assert result["missing_required"] == REQUIRED
    assert result["confidence"] == 0.0


def test_no_missing_fields(full_payload: dict[str, str]):
    result = validate_required_fields(full_payload)

    assert result["missing_required"] == []
    assert result["confidence"] == 1.0


def test_partial_missing_fields(full_payload: dict[str, str]):
    missing = REQUIRED[:2]
    for key in missing:
        full_payload.pop(key)

    result = validate_required_fields(full_payload)

    assert set(result["missing_required"]) == set(missing)
    expected_confidence = max(
        0.0, round(1.0 - len(missing) / len(REQUIRED), 2)
    )
    assert result["confidence"] == expected_confidence
