import logging
from typing import Any, List, Mapping, TypedDict

from src.field_registry import required_field_keys

logger = logging.getLogger(__name__)


def _value_for_field(payload: Mapping[str, Any], field: str) -> Any:
    if field in payload:
        return payload.get(field)
    underscored = field.replace(".", "_")
    return payload.get(underscored)


REQUIRED: List[str] = sorted(required_field_keys())


class ValidationResult(TypedDict):
    """Structured validation output."""

    missing_required: List[str]
    confidence: float


def validate_required_fields(payload: Mapping[str, Any]) -> ValidationResult:
    """Return missing required fields and a confidence score.

    Confidence is calculated as ``1.0 - missing/total`` for the required fields
    and rounded to two decimal places. When every required field is missing, the
    score bottoms out at ``0.0``.
    """

    logger.debug("Validating required fields: %s", list(payload.keys()))

    missing_required = [
        field for field in REQUIRED if not _value_for_field(payload, field)
    ]
    total_required = len(REQUIRED)

    if total_required == 0:
        confidence = 1.0
    else:
        confidence = max(0.0, round(1.0 - len(missing_required) / total_required, 2))

    logger.debug(
        "Validation result -> missing: %s, confidence: %s", missing_required, confidence
    )

    return {"missing_required": missing_required, "confidence": confidence}
