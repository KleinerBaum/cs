from core.validator import REQUIRED
from src.field_registry import field_specs, required_field_keys
from src.question_engine import question_bank


def test_question_bank_uses_registry_keys() -> None:
    spec_keys = {spec.key for spec in field_specs() if spec.input_type}
    question_keys = {question.path for question in question_bank()}

    assert question_keys == spec_keys


def test_required_sets_are_in_sync() -> None:
    assert set(REQUIRED) == required_field_keys()
