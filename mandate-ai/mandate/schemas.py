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


class OpinionStance(StrEnum):
    """Allowed stance labels for extracted opinion units."""

    SUPPORT = "SUPPORT"
    CONDITIONAL_SUPPORT = "CONDITIONAL_SUPPORT"
    OPPOSE = "OPPOSE"
    NEUTRAL = "NEUTRAL"
    UNCERTAIN = "UNCERTAIN"
    MIXED = "MIXED"


class OpinionIntensity(StrEnum):
    """Allowed intensity labels for extracted opinion units."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class CoverageStatus(StrEnum):
    """Coverage relation between original opinion clusters and the summary."""

    COVERED = "COVERED"
    WEAKENED = "WEAKENED"
    DISTORTED = "DISTORTED"
    OMITTED = "OMITTED"


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

    ALLOWED = "ALLOWED"
    REAUTHORIZE = "REAUTHORIZE"
    INTERNAL_ONLY = "INTERNAL_ONLY"
    SYNTHETIC_ONLY = "SYNTHETIC_ONLY"
    UNKNOWN = "UNKNOWN"
    PERMITTED = "PERMITTED"
    CONDITIONAL = "CONDITIONAL"
    REAUTHORIZE_REQUIRED = "REAUTHORIZE_REQUIRED"
    PROHIBITED = "PROHIBITED"


class AuthorityBasis(StrEnum):
    """Declared basis for authorization."""

    DIRECT_CONSENT = "DIRECT_CONSENT"
    ORGANIZATIONAL_AUTHORITY = "ORGANIZATIONAL_AUTHORITY"
    DATA_CONTROLLER_INSTRUCTION = "DATA_CONTROLLER_INSTRUCTION"
    RESEARCH_CONSENT = "RESEARCH_CONSENT"
    PUBLIC_MATERIAL = "PUBLIC_MATERIAL"
    SYNTHETIC_NO_REAL_SUBJECT = "SYNTHETIC_NO_REAL_SUBJECT"
    UNKNOWN = "UNKNOWN"


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
    subject: str | None = None
    predicate: str | None = None
    object: str | None = None
    condition: str | None = None
    certainty: str | None = None

    _claim_id_not_empty = field_validator("claim_id")(_strip_required)
    _text_not_empty = field_validator("text")(_strip_required)


class EvidenceMatch(StrictModel):
    """A relationship between one atomic claim and one source record."""

    claim_id: str
    source_id: str
    similarity_score: float = Field(ge=0.0, le=1.0)
    support_status: SupportStatus
    explanation: str
    matched_text: str = ""
    source_text: str = ""
    rank: int = Field(default=1, ge=1)
    condition_preserved: bool | None = None
    stance_aligned: bool | None = None
    quantifier_supported: bool | None = None
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)

    _claim_id_not_empty = field_validator("claim_id")(_strip_required)
    _source_id_not_empty = field_validator("source_id")(_strip_required)
    _explanation_not_empty = field_validator("explanation")(_strip_required)


class OpinionCluster(StrictModel):
    """A group of source records with a shared position or theme."""

    cluster_id: str
    label: str
    description: str
    opinion_ids: list[str] = Field(default_factory=list)
    source_ids: list[str] = Field(min_length=1)
    unique_participant_count: int = Field(default=0, ge=0)
    stance_distribution: dict[str, int] = Field(default_factory=dict)
    intensity_distribution: dict[str, int] = Field(default_factory=dict)
    condition_summary: str | None = None
    is_minority: bool
    is_procedural: bool = False
    participant_ratio: float = Field(default=0.0, ge=0.0, le=1.0)
    is_numerical_minority: bool = False
    is_normatively_salient: bool = False
    salience_reasons: list[str] = Field(default_factory=list)
    representative_quotes: list[str] = Field(default_factory=list)
    canonical_topic: str | None = None
    subtopics: list[str] = Field(default_factory=list)
    merged_from_cluster_ids: list[str] = Field(default_factory=list)
    merge_explanation: str | None = None

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

    authorization_id: str | None = None
    represented_subject: str
    authorizing_party: str | None = None
    authority_basis: AuthorityBasis = AuthorityBasis.UNKNOWN
    source_type: str
    permitted_operations: list[str] = Field(default_factory=list)
    prohibited_operations: list[str] = Field(default_factory=list)
    permitted_purposes: list[str] = Field(default_factory=list)
    prohibited_purposes: list[str] = Field(default_factory=list)
    permitted_audiences: list[str] = Field(default_factory=list)
    prohibited_audiences: list[str] = Field(default_factory=list)
    permitted_data_types: list[str] = Field(default_factory=list)
    prohibited_data_types: list[str] = Field(default_factory=list)
    allow_publication: bool | None = None
    allow_ai_processing: bool | None = None
    allow_rewriting: bool | None = None
    allow_inference: bool | None = None
    allow_identity_disclosure: bool | None = None
    allow_reuse: bool | None = None
    allow_model_training: bool | None = None
    valid_from: str | None = None
    valid_until: str | None = None
    duration: str | None = None
    duration_description: str | None = None
    withdrawal_supported: bool
    withdrawal_method: str | None = None
    required_disclosures: list[str] = Field(default_factory=list)
    notes: str | None = None

    _represented_subject_not_empty = field_validator("represented_subject")(_strip_required)
    _source_type_not_empty = field_validator("source_type")(_strip_required)

    @field_validator(
        "permitted_operations",
        "prohibited_operations",
        "permitted_purposes",
        "prohibited_purposes",
        "permitted_audiences",
        "prohibited_audiences",
        "permitted_data_types",
        "prohibited_data_types",
        "required_disclosures",
    )
    @classmethod
    def clean_string_list(cls, value: list[str]) -> list[str]:
        cleaned = [_strip_required(item) for item in value]
        if len(set(cleaned)) != len(cleaned):
            raise ValueError("list values must be unique")
        return cleaned


class AuthorizationContext(StrictModel):
    """Actual intended use for this audit run."""

    intended_operation: str
    intended_purpose: str
    intended_audience: str
    is_public: bool
    includes_identity: bool = False
    includes_sensitive_data: bool = False
    uses_ai: bool = True
    includes_inference: bool = False
    allows_human_review: bool = True
    retention_period: str | None = None
    downstream_reuse_planned: bool = False
    data_types: list[str] = Field(default_factory=list)

    _operation_not_empty = field_validator("intended_operation")(_strip_required)
    _context_purpose_not_empty = field_validator("intended_purpose")(_strip_required)
    _context_audience_not_empty = field_validator("intended_audience")(_strip_required)


class AuditRequest(StrictModel):
    """Input payload for an audit run."""

    project_name: str
    representation_mode: RepresentationMode
    source_records: list[SourceRecord] = Field(default_factory=list)
    ai_generated_summary: str
    authorization_profile: AuthorizationProfile
    intended_purpose: str
    intended_audience: str
    is_public: bool
    authorization_context: AuthorizationContext | None = None

    _project_name_not_empty = field_validator("project_name")(_strip_required)
    _purpose_not_empty = field_validator("intended_purpose")(_strip_required)
    _audience_not_empty = field_validator("intended_audience")(_strip_required)

    @field_validator("ai_generated_summary")
    @classmethod
    def clean_summary(cls, value: str) -> str:
        return value.strip()

class AuthorizationResult(StrictModel):
    """Rule engine result used by the audit pipeline."""

    status: AuthorizationStatus
    permitted_use: bool
    required_actions: list[str] = Field(default_factory=list)
    required_disclosures: list[str] = Field(default_factory=list)
    reasons: list[str] = Field(default_factory=list)


class AuthorizationAssessment(StrictModel):
    """Deterministic authorization rule result for the current use."""

    authorization_status: AuthorizationStatus
    matched_permissions: list[str] = Field(default_factory=list)
    violated_restrictions: list[str] = Field(default_factory=list)
    missing_information: list[str] = Field(default_factory=list)
    required_actions: list[str] = Field(default_factory=list)
    required_disclosures: list[str] = Field(default_factory=list)
    permitted_use_description: str = ""
    prohibited_use_description: str = ""
    explanation: str = ""
    rule_ids_triggered: list[str] = Field(default_factory=list)
    permitted_use: bool = False
    prohibited_use: bool = False

    @property
    def status(self) -> AuthorizationStatus:
        return self.authorization_status

    @property
    def reasons(self) -> list[str]:
        return [self.explanation] if self.explanation else []


class OpinionUnit(StrictModel):
    """A single separable opinion extracted from a source record."""

    opinion_id: str
    source_id: str
    participant_id: str | None = None
    text: str
    topic: str
    stance: OpinionStance
    intensity: OpinionIntensity
    condition: str | None = None
    target: str | None = None
    is_procedural: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)

    _opinion_id_not_empty = field_validator("opinion_id")(_strip_required)
    _opinion_source_id_not_empty = field_validator("source_id")(_strip_required)
    _opinion_text_not_empty = field_validator("text")(_strip_required)
    _opinion_topic_not_empty = field_validator("topic")(_strip_required)


class QuantifierAssessment(StrictModel):
    """Assessment of whether a claim's quantifier is supported in uploaded sources."""

    claim_id: str
    quantifier: str | None = None
    supported: bool
    supporting_participant_count: int = Field(ge=0)
    opposing_participant_count: int = Field(ge=0)
    total_participant_count: int = Field(ge=0)
    observed_ratio: float = Field(ge=0.0, le=1.0)
    explanation: str

    _claim_id_not_empty = field_validator("claim_id")(_strip_required)
    _explanation_not_empty = field_validator("explanation")(_strip_required)


class ClaimEvidenceBundle(StrictModel):
    """Evidence chain and risk assessment for one atomic claim."""

    claim: AtomicClaim
    candidate_matches: list[EvidenceMatch] = Field(default_factory=list)
    best_supporting_matches: list[EvidenceMatch] = Field(default_factory=list)
    contradicting_matches: list[EvidenceMatch] = Field(default_factory=list)
    final_support_status: SupportStatus
    quantifier_assessment: QuantifierAssessment | None = None
    warnings: list[str] = Field(default_factory=list)


class SourceTraceResult(StrictModel):
    """Complete source tracing output without a single truth score."""

    claims: list[AtomicClaim] = Field(default_factory=list)
    evidence_bundles: list[ClaimEvidenceBundle] = Field(default_factory=list)
    unsupported_claim_ids: list[str] = Field(default_factory=list)
    contradicted_claim_ids: list[str] = Field(default_factory=list)
    partially_supported_claim_ids: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class ClusterCoverageAssessment(StrictModel):
    """Coverage assessment for one original opinion cluster."""

    cluster_id: str
    status: CoverageStatus
    matched_claim_ids: list[str] = Field(default_factory=list)
    semantic_similarity: float = Field(ge=0.0, le=1.0)
    stance_preserved: bool
    intensity_preserved: bool
    condition_preserved: bool
    quantifier_preserved: bool
    explanation: str
    representative_quotes: list[str] = Field(default_factory=list)
    participant_count: int = Field(ge=0)
    participant_ratio: float = Field(ge=0.0, le=1.0)
    is_minority: bool
    is_normatively_salient: bool

    _coverage_cluster_id_not_empty = field_validator("cluster_id")(_strip_required)
    _coverage_explanation_not_empty = field_validator("explanation")(_strip_required)


class OmissionResult(StrictModel):
    """Opinion omission and disappeared voice analysis output."""

    opinion_units: list[OpinionUnit] = Field(default_factory=list)
    clusters: list[OpinionCluster] = Field(default_factory=list)
    coverage_assessments: list[ClusterCoverageAssessment] = Field(default_factory=list)
    covered_cluster_ids: list[str] = Field(default_factory=list)
    weakened_cluster_ids: list[str] = Field(default_factory=list)
    distorted_cluster_ids: list[str] = Field(default_factory=list)
    omitted_cluster_ids: list[str] = Field(default_factory=list)
    omitted_minority_cluster_ids: list[str] = Field(default_factory=list)
    omitted_salient_cluster_ids: list[str] = Field(default_factory=list)
    procedural_cluster_ids: list[str] = Field(default_factory=list)
    procedural_clusters_omitted: list[str] = Field(default_factory=list)
    topic_coverage_numerator: int = Field(default=0, ge=0)
    topic_coverage_denominator: int = Field(default=0, ge=0)
    minority_retention_numerator: int = Field(default=0, ge=0)
    minority_retention_denominator: int = Field(default=0, ge=0)
    procedural_issue_retention_numerator: int = Field(default=0, ge=0)
    procedural_issue_retention_denominator: int = Field(default=0, ge=0)
    condition_preservation_numerator: int = Field(default=0, ge=0)
    condition_preservation_denominator: int = Field(default=0, ge=0)
    warnings: list[str] = Field(default_factory=list)


class RevisionResult(StrictModel):
    """Faithful revision generated from verified project materials."""

    original_summary: str
    revised_summary: str
    removed_claims: list[str] = Field(default_factory=list)
    modified_claims: list[str] = Field(default_factory=list)
    restored_clusters: list[str] = Field(default_factory=list)
    added_disclosures: list[str] = Field(default_factory=list)
    source_citations: dict[str, list[str]] = Field(default_factory=dict)
    unresolved_issues: list[str] = Field(default_factory=list)
    human_review_required: bool = True


class AuditPassport(StrictModel):
    """Structured output credential for an audit run."""

    representation_mode: RepresentationMode
    source_count: int = Field(ge=0)
    claim_count: int = Field(ge=0)
    traceable_claim_count: int = Field(ge=0)
    unsupported_claims: list[str] = Field(default_factory=list)
    unsupported_claim_ids: list[str] = Field(default_factory=list)
    contradicted_claim_ids: list[str] = Field(default_factory=list)
    partially_supported_claim_ids: list[str] = Field(default_factory=list)
    quantifier_warnings: list[str] = Field(default_factory=list)
    cluster_count: int = Field(ge=0)
    represented_clusters: list[str] = Field(default_factory=list)
    covered_clusters: list[str] = Field(default_factory=list)
    weakened_clusters: list[str] = Field(default_factory=list)
    distorted_clusters: list[str] = Field(default_factory=list)
    omitted_clusters: list[str] = Field(default_factory=list)
    minority_clusters_total: int = Field(ge=0)
    minority_clusters_retained: int = Field(ge=0)
    omitted_salient_clusters: list[str] = Field(default_factory=list)
    procedural_clusters_total: int = Field(default=0, ge=0)
    procedural_clusters_omitted: list[str] = Field(default_factory=list)
    condition_preservation_count: str = "0/0"
    authorization_status: AuthorizationStatus
    permitted_use: bool
    prohibited_use: bool = False
    missing_authorization_information: list[str] = Field(default_factory=list)
    required_actions: list[str] = Field(default_factory=list)
    required_disclosures: list[str] = Field(default_factory=list)
    triggered_rule_ids: list[str] = Field(default_factory=list)
    final_status: FinalStatus
    source_trace_result: SourceTraceResult | None = None
    omission_result: OmissionResult | None = None
    authorization_assessment: AuthorizationAssessment | None = None
    revision_result: RevisionResult | None = None
    pending_modules: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def counts_are_consistent(self) -> AuditPassport:
        if self.traceable_claim_count > self.claim_count:
            raise ValueError("traceable_claim_count cannot exceed claim_count")
        if self.minority_clusters_retained > self.minority_clusters_total:
            raise ValueError(
                "minority_clusters_retained cannot exceed minority_clusters_total"
            )
        return self
