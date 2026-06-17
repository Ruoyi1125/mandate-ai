from __future__ import annotations

from pathlib import Path

from mandate.authorization_engine import AuthorizationEngine
from mandate.schemas import (
    AuditRequest,
    AuthorizationContext,
    AuthorizationProfile,
    AuthorizationStatus,
    AuthorityBasis,
    RepresentationMode,
    SourceRecord,
)


def _request(
    intended_purpose: str = "research",
    intended_audience: str = "internal",
    is_public: bool = False,
) -> AuditRequest:
    return AuditRequest(
        project_name="Authorization test",
        representation_mode=RepresentationMode.REAL_GROUP,
        source_records=[SourceRecord(source_id="s1", text="Source text", metadata={})],
        ai_generated_summary="Source text",
        authorization_profile=AuthorizationProfile(
            authorization_id="auth-test",
            represented_subject="participants",
            authorizing_party="participants",
            authority_basis=AuthorityBasis.RESEARCH_CONSENT,
            source_type="survey",
            permitted_operations=["summarize"],
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
            required_disclosures=["Disclose AI use."],
        ),
        authorization_context=AuthorizationContext(
            intended_operation="summarize",
            intended_purpose=intended_purpose,
            intended_audience=intended_audience,
            is_public=is_public,
            uses_ai=True,
        ),
        intended_purpose=intended_purpose,
        intended_audience=intended_audience,
        is_public=is_public,
    )


def test_authorization_permits_matching_internal_use() -> None:
    engine = AuthorizationEngine(Path("rules/authorization_rules.yaml"))
    result = engine.evaluate(_request())
    assert result.permitted_use is True
    assert result.status == AuthorizationStatus.CONDITIONAL


def test_authorization_requires_reauthorization_for_public_release() -> None:
    engine = AuthorizationEngine(Path("rules/authorization_rules.yaml"))
    result = engine.evaluate(_request(is_public=True))
    assert result.permitted_use is False
    assert result.status == AuthorizationStatus.PROHIBITED
    assert "PUBLICATION_NOT_ALLOWED" in result.rule_ids_triggered


def test_authorization_rejects_prohibited_purpose() -> None:
    engine = AuthorizationEngine(Path("rules/authorization_rules.yaml"))
    result = engine.evaluate(_request(intended_purpose="advertising"))
    assert result.permitted_use is False
    assert "PURPOSE_OUT_OF_SCOPE" in result.rule_ids_triggered
