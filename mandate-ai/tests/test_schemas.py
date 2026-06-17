from __future__ import annotations

import pytest
from pydantic import ValidationError

from mandate.schemas import (
    AtomicClaim,
    AuditPassport,
    AuditRequest,
    AuthorizationProfile,
    AuthorizationStatus,
    EvidenceMatch,
    FinalStatus,
    OpinionCluster,
    RepresentationMode,
    SourceRecord,
    SupportStatus,
)


def _profile() -> AuthorizationProfile:
    return AuthorizationProfile(
        represented_subject="participants",
        source_type="interview",
        permitted_operations=["summarize"],
        prohibited_operations=["public_release"],
        permitted_purposes=["research"],
        prohibited_purposes=["advertising"],
        permitted_audiences=["internal"],
        duration="2026 course project",
        withdrawal_supported=True,
        required_disclosures=["AI summary"],
    )


def test_source_record_requires_text() -> None:
    with pytest.raises(ValidationError):
        SourceRecord(source_id="s1", text=" ", metadata={}, consent_id=None)


def test_atomic_claim_importance_range() -> None:
    with pytest.raises(ValidationError):
        AtomicClaim(claim_id="c1", text="A claim", importance=1.5)


def test_evidence_match_support_status_enum() -> None:
    match = EvidenceMatch(
        claim_id="c1",
        source_id="s1",
        similarity_score=0.9,
        support_status=SupportStatus.DIRECTLY_SUPPORTED,
        explanation="Exact statement.",
    )
    assert match.support_status == SupportStatus.DIRECTLY_SUPPORTED


def test_opinion_cluster_rejects_duplicate_source_ids() -> None:
    with pytest.raises(ValidationError):
        OpinionCluster(
            cluster_id="cl1",
            label="Label",
            description="Description",
            source_ids=["s1", "s1"],
            stance_distribution={"support": 2},
            is_minority=False,
            representative_quotes=[],
        )


def test_audit_request_rejects_duplicate_sources() -> None:
    source = SourceRecord(source_id="s1", text="Opinion", metadata={})
    with pytest.raises(ValidationError):
        AuditRequest(
            project_name="Project",
            representation_mode=RepresentationMode.REAL_GROUP,
            source_records=[source, source],
            ai_generated_summary="Summary",
            authorization_profile=_profile(),
            intended_purpose="research",
            intended_audience="internal",
            is_public=False,
        )


def test_audit_passport_count_consistency() -> None:
    with pytest.raises(ValidationError):
        AuditPassport(
            representation_mode=RepresentationMode.REAL_GROUP,
            source_count=1,
            claim_count=1,
            traceable_claim_count=2,
            unsupported_claims=[],
            cluster_count=0,
            represented_clusters=[],
            omitted_clusters=[],
            minority_clusters_total=0,
            minority_clusters_retained=0,
            authorization_status=AuthorizationStatus.PERMITTED,
            permitted_use=True,
            required_actions=[],
            required_disclosures=[],
            final_status=FinalStatus.ALLOWED,
        )
