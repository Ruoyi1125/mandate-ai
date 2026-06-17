"""Pydantic data structures for the MANDATE audit workflow."""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class SupportStatus(StrEnum):
    """Allowed evidence support labels."""

    DIRECTLY_SUPPORTED = "DIRECTLY_SUPPORTED"
    PARTIALLY_SUPPORTED = "PARTIALLY_SUPPORTED"
    INFERRED = "INFERRED"
    UNSUPPORTED = "UNSUPPORTED"
    CONTRADICTED = "CONTRADICTED"


class RepresentationMode(StrEnum):
    """Allowed representation modes."""

    INDIVIDUAL = "INDIVIDUAL"
    REAL_GROUP = "REAL_GROUP"
    SYNTHETIC_GROUP = "SYNTHETIC_GROUP"


class FinalStatus(StrEnum):
    """Allowed final audit outcomes."""

    ALLOWED = "ALLOWED"
    CONDITIONAL = "CONDITIONAL"
    REAUTHORIZE = "REAUTHORIZE"
    INTERNAL_ONLY = "INTERNAL_ONLY"
    SYNTHETIC_ONLY = "SYNTHETIC_ONLY"
    PROHIBITED = "PROHIBITED"


class AuthorizationStatus(StrEnum):
    """Structured authorization status from the rule engine."""

    PERMITTED = "PERMITTED"
    CONDITIONAL = "CONDITIONAL"
    REAUTHORIZE_REQUIRED = "REAUTHORIZE_REQUIRED"
    PROHIBITED = "PROHIBITED"


class StrictModel(BaseModel):
    """Base model with strict field handling."""

    model_config = ConfigDict(extra="forbid", validate_assignment=True)


def _strip_required(value: str) -> str:
    stripped = value.strip()
    if not stripped:
        raise ValueError("must not be empty")
    return stripped


class SourceRecord(StrictModel):
    """A single source opinion or testimony record."""

    source_id: str
    participant_id: str | None = None
    text: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    consent_id: str | None = None

    _source_id_not_empty = field_validator("source_id")(_strip_required)
    _text_not_empty = field_validator("text")(_strip_required)

    @field_validator("participant_id", "consent_id")
    @classmethod
    def optional_strings_not_blank(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        return stripped or None


class AtomicClaim(StrictModel):
    """A minimal checkable claim extracted from an AI summary."""

    claim_id: str
    text: str
    quantifier: str | None = None
    stance: str | None = None
    importance: float = Field(ge=0.0, le=1.0)

    _claim_id_not_empty = field_validator("claim_id")(_strip_required)
    _text_not_empty = field_validator("text")(_strip_required)


class EvidenceMatch(StrictModel):
    """A relationship between one atomic claim and one source record."""

    claim_id: str
    source_id: str
    similarity_score: float = Field(ge=0.0, le=1.0)
    support_status: SupportStatus
    explanation: str

    _claim_id_not_empty = field_validator("claim_id")(_strip_required)
    _source_id_not_empty = field_validator("source_id")(_strip_required)
    _explanation_not_empty = field_validator("explanation")(_strip_required)


class OpinionCluster(StrictModel):
    """A group of source records with a shared position or theme."""

    cluster_id: str
    label: str
    description: str
    source_ids: list[str] = Field(min_length=1)
    stance_distribution: dict[str, int] = Field(default_factory=dict)
    is_minority: bool
    representative_quotes: list[str] = Field(default_factory=list)

    _cluster_id_not_empty = field_validator("cluster_id")(_strip_required)
    _label_not_empty = field_validator("label")(_strip_required)
    _description_not_empty = field_validator("description")(_strip_required)

    @field_validator("source_ids")
    @classmethod
    def source_ids_unique(cls, value: list[str]) -> list[str]:
        cleaned = [_strip_required(item) for item in value]
        if len(set(cleaned)) != len(cleaned):
            raise ValueError("source_ids must be unique")
        return cleaned

    @field_validator("stance_distribution")
    @classmethod
    def stance_counts_non_negative(cls, value: dict[str, int]) -> dict[str, int]:
        if any(count < 0 for count in value.values()):
            raise ValueError("stance_distribution counts must be non-negative")
        return value


class AuthorizationProfile(StrictModel):
    """Declared authorization constraints for a representation use case."""

    represented_subject: str
    source_type: str
    permitted_operations: list[str] = Field(default_factory=list)
    prohibited_operations: list[str] = Field(default_factory=list)
    permitted_purposes: list[str] = Field(default_factory=list)
    prohibited_purposes: list[str] = Field(default_factory=list)
    permitted_audiences: list[str] = Field(default_factory=list)
    duration: str
    withdrawal_supported: bool
    required_disclosures: list[str] = Field(default_factory=list)

    _represented_subject_not_empty = field_validator("represented_subject")(_strip_required)
    _source_type_not_empty = field_validator("source_type")(_strip_required)
    _duration_not_empty = field_validator("duration")(_strip_required)

    @field_validator(
        "permitted_operations",
        "prohibited_operations",
        "permitted_purposes",
        "prohibited_purposes",
        "permitted_audiences",
        "required_disclosures",
    )
    @classmethod
    def clean_string_list(cls, value: list[str]) -> list[str]:
        cleaned = [_strip_required(item) for item in value]
        if len(set(cleaned)) != len(cleaned):
            raise ValueError("list values must be unique")
        return cleaned


class AuditRequest(StrictModel):
    """Input payload for an audit run."""

    project_name: str
    representation_mode: RepresentationMode
    source_records: list[SourceRecord] = Field(min_length=1)
    ai_generated_summary: str
    authorization_profile: AuthorizationProfile
    intended_purpose: str
    intended_audience: str
    is_public: bool

    _project_name_not_empty = field_validator("project_name")(_strip_required)
    _summary_not_empty = field_validator("ai_generated_summary")(_strip_required)
    _purpose_not_empty = field_validator("intended_purpose")(_strip_required)
    _audience_not_empty = field_validator("intended_audience")(_strip_required)

    @model_validator(mode="after")
    def source_ids_unique(self) -> AuditRequest:
        ids = [record.source_id for record in self.source_records]
        if len(set(ids)) != len(ids):
            raise ValueError("source_records must have unique source_id values")
        return self


class AuthorizationResult(StrictModel):
    """Rule engine result used by the audit pipeline."""

    status: AuthorizationStatus
    permitted_use: bool
    required_actions: list[str] = Field(default_factory=list)
    required_disclosures: list[str] = Field(default_factory=list)
    reasons: list[str] = Field(default_factory=list)


class AuditPassport(StrictModel):
    """Structured output credential for an audit run."""

    representation_mode: RepresentationMode
    source_count: int = Field(ge=0)
    claim_count: int = Field(ge=0)
    traceable_claim_count: int = Field(ge=0)
    unsupported_claims: list[str] = Field(default_factory=list)
    cluster_count: int = Field(ge=0)
    represented_clusters: list[str] = Field(default_factory=list)
    omitted_clusters: list[str] = Field(default_factory=list)
    minority_clusters_total: int = Field(ge=0)
    minority_clusters_retained: int = Field(ge=0)
    authorization_status: AuthorizationStatus
    permitted_use: bool
    required_actions: list[str] = Field(default_factory=list)
    required_disclosures: list[str] = Field(default_factory=list)
    final_status: FinalStatus

    @model_validator(mode="after")
    def counts_are_consistent(self) -> AuditPassport:
        if self.traceable_claim_count > self.claim_count:
            raise ValueError("traceable_claim_count cannot exceed claim_count")
        if self.minority_clusters_retained > self.minority_clusters_total:
            raise ValueError(
                "minority_clusters_retained cannot exceed minority_clusters_total"
            )
        return self
