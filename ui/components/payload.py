"""Typed payload handling for the pipeline runner UI."""

from __future__ import annotations

from typing import Any, Mapping

from pydantic import AliasChoices, BaseModel, ConfigDict, Field

from src.keys import Keys


class PipelinePayload(BaseModel):
    """Normalized payload expected by the deterministic pipeline.

    This model collapses legacy session-state keys like ``extracted_company``
    or ``parsed_title`` into the canonical schema fields used throughout the
    backend (e.g., ``company_name``, ``job_title``, ``seniority``).
    """

    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    company_name: str | None = Field(
        default=None,
        validation_alias=AliasChoices(
            "company_name", "company", "extracted_company", "parsed_company"
        ),
    )
    job_title: str | None = Field(
        default=None,
        validation_alias=AliasChoices(
            "job_title", "title", "parsed_title", "jobTitle", "extracted_title"
        ),
    )
    seniority: str | None = Field(
        default=None,
        validation_alias=AliasChoices("seniority", "parsed_seniority", "level"),
    )
    contract_type: str | None = None
    employment_type: str | None = None
    start_date: str | None = None
    primary_city: str | None = Field(
        default=None, validation_alias=AliasChoices("primary_city", "city")
    )

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any] | None) -> "PipelinePayload":
        """Build the payload from session state or other mappings."""

        if not isinstance(payload, Mapping):
            return cls()
        return cls.model_validate(payload)

    def to_canonical_dict(self) -> dict[str, Any]:
        """Return payload using canonical field names only."""

        canonical_map = {
            "company_name": Keys.COMPANY_NAME,
            "job_title": Keys.POSITION_TITLE,
            "seniority": Keys.POSITION_SENIORITY,
            "contract_type": Keys.EMPLOYMENT_CONTRACT,
            "employment_type": Keys.EMPLOYMENT_TYPE,
            "start_date": Keys.EMPLOYMENT_START,
            "primary_city": Keys.LOCATION_CITY,
        }

        raw_payload = self.model_dump(exclude_none=True)
        return {
            canonical_map.get(key, key): value for key, value in raw_payload.items()
        }
