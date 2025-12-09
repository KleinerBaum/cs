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
    full_payload.pop("contract_type")
    full_payload.pop("employment_type")

    result = validate_required_fields(full_payload)

    assert set(result["missing_required"]) == {"contract_type", "employment_type"}
    assert result["confidence"] == 0.67
