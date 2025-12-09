"""Pydantic models for vacancy processing."""
from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class RawInput(BaseModel):
    """Raw job description payload before any parsing.

    The ``text`` field is required so that downstream stages always
    have a source string to work with.
    """

    model_config = ConfigDict(extra="forbid")

    text: str
    source: Optional[str] = None
    language: Optional[str] = None


class VacancyCore(BaseModel):
    """Core vacancy fields extracted from the raw input."""

    model_config = ConfigDict(extra="forbid")

    title: Optional[str] = None
    company: Optional[str] = None
    location: Optional[str] = None

    responsibilities: List[str] = Field(default_factory=list)
    requirements: List[str] = Field(default_factory=list)
    benefits: List[str] = Field(default_factory=list)
    languages: List[str] = Field(default_factory=list)
    tools: List[str] = Field(default_factory=list)


class VacancyValidated(VacancyCore):
    """Validated vacancy with optional notes about the checks performed."""

    validation_notes: List[str] = Field(default_factory=list)
    validated: bool = False


class Enrichment(BaseModel):
    """Optional enrichment data from external sources (e.g., ESCO)."""

    model_config = ConfigDict(extra="forbid")

    tags: List[str] = Field(default_factory=list)
    esco_skills: List[str] = Field(default_factory=list)
    suggestions: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
