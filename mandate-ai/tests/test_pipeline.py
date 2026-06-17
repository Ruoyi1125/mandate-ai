from __future__ import annotations

from pathlib import Path

from mandate.pipeline import AuditPipeline
from mandate.providers import MockProvider
from mandate.schemas import (
    AuditRequest,
    AuthorizationContext,
    AuthorizationProfile,
    AuthorityBasis,
    FinalStatus,
    RepresentationMode,
    SourceRecord,
)


def test_pipeline_returns_audit_passport() -> None:
    request = AuditRequest(
        project_name="Pipeline test",
        representation_mode=RepresentationMode.REAL_GROUP,
        source_records=[
            SourceRecord(
                source_id="s1",
                participant_id=None,
                text="Most participants support AI use with disclosure",
                metadata={},
                consent_id=None,
            ),
            SourceRecord(
                source_id="s2",
                participant_id=None,
                text="Some participants worry minority opinions are omitted",
                metadata={},
                consent_id=None,
            ),
        ],
        ai_generated_summary=(
            "Most participants support AI use with disclosure. "
            "Some participants worry minority opinions are omitted."
        ),
        authorization_profile=AuthorizationProfile(
            authorization_id="pipeline-auth",
            represented_subject="participants",
            authorizing_party="participants",
            authority_basis=AuthorityBasis.RESEARCH_CONSENT,
            source_type="workshop_notes",
            permitted_operations=["summarize", "audit"],
            prohibited_operations=["public_release"],
            permitted_purposes=["research"],
            prohibited_purposes=["advertising"],
            permitted_audiences=["internal"],
            allow_publication=False,
            allow_ai_processing=True,
            allow_rewriting=True,
            allow_inference=False,
            allow_identity_disclosure=False,
            allow_reuse=False,
            allow_model_training=False,
            duration="phase one",
            withdrawal_supported=True,
            withdrawal_method="email",
            required_disclosures=[],
        ),
        authorization_context=AuthorizationContext(
            intended_operation="summarize",
            intended_purpose="research",
            intended_audience="internal",
            is_public=False,
            uses_ai=True,
        ),
        intended_purpose="research",
        intended_audience="internal",
        is_public=False,
    )
    pipeline = AuditPipeline(
        provider=MockProvider(),
        rules_path=Path("rules/authorization_rules.yaml"),
    )

    passport = pipeline.run(request)

    assert passport.source_count == 2
    assert passport.claim_count == 2
    assert passport.cluster_count >= 1
    assert passport.omission_result is not None
    assert passport.pending_modules == []
    assert passport.final_status in {FinalStatus.ALLOWED, FinalStatus.CONDITIONAL}
