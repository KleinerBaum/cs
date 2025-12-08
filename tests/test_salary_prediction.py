from __future__ import annotations

from src.keys import Keys
from src.profile import new_profile, set_field
from src.salary_prediction import collect_salary_factors, predict_salary_range


def test_collect_salary_factors_skips_missing() -> None:
    profile = new_profile()
    set_field(
        profile,
        Keys.POSITION_SENIORITY,
        "senior",
        provenance="user",
        confidence=1.0,
        evidence="test",
    )
    set_field(
        profile,
        Keys.COMPANY_SIZE,
        "",
        provenance="user",
        confidence=1.0,
        evidence="test",
    )

    factors = collect_salary_factors(
        profile, {Keys.POSITION_SENIORITY, Keys.COMPANY_SIZE, Keys.LOCATION_CITY}
    )

    assert factors == {Keys.POSITION_SENIORITY: "senior"}


def test_predict_salary_range_applies_multipliers() -> None:
    factors = {
        Keys.POSITION_SENIORITY: "senior",
        Keys.LOCATION_CITY: "Munich",
        Keys.EMPLOYMENT_TYPE: "part_time",
    }

    result = predict_salary_range(factors)

    # Senior baseline is 75k–95k; Munich premium (12%) and part-time (70%) should keep ordering
    assert 50000 <= result.min_salary < result.max_salary <= 90000
    assert result.currency == "EUR"
    assert any(adj.factor == "location" for adj in result.adjustments)
