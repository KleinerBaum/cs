from __future__ import annotations

from state import AppState, app_state_from_profile, apply_app_state_to_profile


def _sample_profile() -> dict[str, object]:
    return {
        "company": {"name": "Acme Corp"},
        "location": {"primary_city": "Berlin", "work_policy": "hybrid"},
        "employment": {
            "employment_type": "full_time",
            "contract_type": "permanent",
            "start_date": "2024-01-01",
            "work_schedule": "40h",
            "visa_sponsorship": True,
        },
        "position": {
            "job_title": "Senior Engineer",
            "seniority_level": "senior",
            "role_summary": "Build things",
            "direct_reports": 2,
        },
        "team": {"department_name": "Platform"},
        "responsibilities": {"items": ["Design", "Implement"]},
        "requirements": {
            "hard_skills_required": ["Python", "APIs"],
            "hard_skills_optional": ["Docker"],
        },
        "compensation": {
            "salary_min": 70000,
            "salary_max": 90000,
            "currency": "EUR",
            "variable_pct": 10,
            "relocation": True,
        },
        "benefits": {"items": ["Coffee", "Gym"]},
    }


def test_app_state_from_profile_sets_all_known_fields():
    profile = _sample_profile()

    state = app_state_from_profile(profile)

    assert state.profile.company_name == "Acme Corp"
    assert state.profile.primary_city == "Berlin"
    assert state.profile.remote_policy == "hybrid"
    assert state.role.job_title == "Senior Engineer"
    assert state.role.seniority == "senior"
    assert state.role.department == "Platform"
    assert state.role.direct_reports == 2
    assert state.role.work_schedule == "40h"
    assert state.skills.tasks == ["Design", "Implement"]
    assert state.skills.must_have == ["Python", "APIs"]
    assert state.skills.nice_to_have == ["Docker"]
    assert state.compensation.salary_min == 70000
    assert state.compensation.salary_max == 90000
    assert state.compensation.currency == "EUR"
    assert state.compensation.variable_pct == 10
    assert state.compensation.relocation is True
    assert state.compensation.visa is True
    assert state.compensation.benefits == ["Coffee", "Gym"]


def test_profile_round_trip_preserves_mapped_fields():
    profile = _sample_profile()
    app_state = app_state_from_profile(profile)

    assert isinstance(app_state, AppState)

    round_tripped = apply_app_state_to_profile(app_state)

    assert round_tripped == profile
