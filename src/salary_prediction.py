from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping

from .keys import Keys
from .profile import get_value, is_missing_value


@dataclass
class SalaryAdjustment:
    factor: str
    multiplier: float
    value: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class SalaryPrediction:
    min_salary: int
    max_salary: int
    currency: str
    applied_factors: dict[str, Any]
    baseline: dict[str, Any]
    adjustments: list[SalaryAdjustment]

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["adjustments"] = [adj.to_dict() for adj in self.adjustments]
        return data


BASELINE_BY_SENIORITY: dict[str, tuple[int, int]] = {
    "junior": (42000, 52000),
    "mid": (55000, 72000),
    "senior": (75000, 95000),
    "lead": (90000, 115000),
    "head": (105000, 135000),
    "c_level": (130000, 180000),
}


def collect_salary_factors(
    profile: dict[str, Any], selected_paths: set[str]
) -> dict[str, Any]:
    factors: dict[str, Any] = {}
    for path in selected_paths:
        value = get_value(profile, path)
        if is_missing_value(value):
            continue
        factors[path] = value
    return factors


def _seniority_baseline(selected_factors: Mapping[str, Any]) -> tuple[str, int, int]:
    raw = str(selected_factors.get(Keys.POSITION_SENIORITY, "") or "").strip().lower()
    if raw not in BASELINE_BY_SENIORITY:
        raw = "mid"
    base_min, base_max = BASELINE_BY_SENIORITY[raw]
    return raw, base_min, base_max


def _location_adjustment(city_raw: str) -> tuple[float, str]:
    city = city_raw.strip().lower()
    if not city:
        return 1.0, city_raw
    premium_cities = {
        "munich": 1.12,
        "münchen": 1.12,
        "zurich": 1.3,
        "zürich": 1.3,
        "london": 1.25,
        "paris": 1.18,
        "new york": 1.28,
        "frankfurt": 1.1,
    }
    moderate_cities = {"berlin": 1.05, "hamburg": 1.08, "amsterdam": 1.12}
    cost_savers = {"leipzig": 0.92, "sofia": 0.85, "krakow": 0.9, "kraków": 0.9}

    for key, factor in premium_cities.items():
        if key in city:
            return factor, city_raw
    for key, factor in moderate_cities.items():
        if key in city:
            return factor, city_raw
    for key, factor in cost_savers.items():
        if key in city:
            return factor, city_raw
    return 1.0, city_raw


def _company_size_multiplier(size_raw: str) -> float:
    digits = [
        int(part)
        for part in size_raw.replace("+", " ").replace("-", " ").split()
        if part.isdigit()
    ]
    if not digits:
        return 1.0
    avg_size = sum(digits) / len(digits)
    if avg_size < 50:
        return 0.95
    if avg_size < 250:
        return 1.0
    if avg_size < 1000:
        return 1.05
    return 1.1


def _industry_multiplier(industry_raw: str) -> float:
    industry = industry_raw.lower()
    premium_markers = (
        "fintech",
        "finance",
        "consulting",
        "software",
        "ai",
        "machine learning",
    )
    discount_markers = ("nonprofit", "non-profit", "ngo", "public", "government")
    if any(marker in industry for marker in premium_markers):
        return 1.08
    if any(marker in industry for marker in discount_markers):
        return 0.92
    return 1.0


def _employment_multiplier(employment_type: str) -> float:
    mapping = {
        "full_time": 1.0,
        "part_time": 0.7,
        "contractor": 1.15,
        "intern": 0.6,
    }
    return mapping.get(employment_type, 1.0)


def _contract_multiplier(contract_type: str) -> float:
    if contract_type == "fixed_term":
        return 0.95
    return 1.0


def _work_policy_multiplier(policy: str) -> float:
    if policy == "remote":
        return 0.95
    if policy == "onsite":
        return 1.03
    return 1.0


def _remote_scope_multiplier(scope: str) -> float:
    lowered = scope.lower()
    if "global" in lowered:
        return 0.93
    if "europe" in lowered or "eu" in lowered:
        return 0.96
    return 1.0


def predict_salary_range(
    selected_factors: Mapping[str, Any], *, default_currency: str = "EUR"
) -> SalaryPrediction:
    seniority_key, base_min, base_max = _seniority_baseline(selected_factors)
    multiplier = 1.0
    adjustments: list[SalaryAdjustment] = [SalaryAdjustment("base", 1.0, seniority_key)]

    if Keys.LOCATION_CITY in selected_factors:
        loc_mult, loc_label = _location_adjustment(
            str(selected_factors[Keys.LOCATION_CITY])
        )
        multiplier *= loc_mult
        adjustments.append(SalaryAdjustment("location", loc_mult, str(loc_label)))

    if Keys.LOCATION_WORK_POLICY in selected_factors:
        policy = str(selected_factors[Keys.LOCATION_WORK_POLICY])
        policy_mult = _work_policy_multiplier(policy)
        multiplier *= policy_mult
        adjustments.append(SalaryAdjustment("work_policy", policy_mult, policy))

    if Keys.EMPLOYMENT_TYPE in selected_factors:
        emp_type = str(selected_factors[Keys.EMPLOYMENT_TYPE])
        emp_mult = _employment_multiplier(emp_type)
        multiplier *= emp_mult
        adjustments.append(SalaryAdjustment("employment_type", emp_mult, emp_type))

    if Keys.EMPLOYMENT_CONTRACT in selected_factors:
        contract = str(selected_factors[Keys.EMPLOYMENT_CONTRACT])
        contract_mult = _contract_multiplier(contract)
        multiplier *= contract_mult
        adjustments.append(SalaryAdjustment("contract_type", contract_mult, contract))

    if Keys.COMPANY_INDUSTRY in selected_factors:
        industry = str(selected_factors[Keys.COMPANY_INDUSTRY])
        industry_mult = _industry_multiplier(industry)
        multiplier *= industry_mult
        adjustments.append(SalaryAdjustment("industry", industry_mult, industry))

    if Keys.COMPANY_SIZE in selected_factors:
        size_value = str(selected_factors[Keys.COMPANY_SIZE])
        size_mult = _company_size_multiplier(size_value)
        multiplier *= size_mult
        adjustments.append(SalaryAdjustment("company_size", size_mult, size_value))

    if Keys.LOCATION_REMOTE_SCOPE in selected_factors:
        scope_value = str(selected_factors[Keys.LOCATION_REMOTE_SCOPE])
        scope_mult = _remote_scope_multiplier(scope_value)
        multiplier *= scope_mult
        adjustments.append(SalaryAdjustment("remote_scope", scope_mult, scope_value))

    currency = str(
        selected_factors.get(Keys.SALARY_CURRENCY) or default_currency
    ).upper()
    min_salary = int(base_min * multiplier)
    max_salary = int(base_max * multiplier)

    return SalaryPrediction(
        min_salary=min_salary,
        max_salary=max_salary,
        currency=currency,
        applied_factors=dict(selected_factors),
        baseline={"seniority": seniority_key, "min": base_min, "max": base_max},
        adjustments=adjustments,
    )
