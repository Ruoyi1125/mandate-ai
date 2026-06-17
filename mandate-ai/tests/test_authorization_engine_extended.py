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


def _profile() -> AuthorizationProfile:
    return AuthorizationProfile(
        authorization_id="auth-demo",
        represented_subject="anonymous students",
        authorizing_party="participants",
        authority_basis=AuthorityBasis.RESEARCH_CONSENT,
        source_type="survey",
        permitted_operations=["summarize", "audit"],
        prohibited_operations=["public_release"],
        permitted_purposes=["course_research"],
        prohibited_purposes=["commercial"],
        permitted_audiences=["course_teacher"],
        prohibited_audiences=["public"],
        allow_publication=False,
        allow_ai_processing=True,
        allow_rewriting=True,
        allow_inference=False,
        allow_identity_disclosure=False,
        allow_reuse=False,
        allow_model_training=False,
        duration="until project end",
        withdrawal_supported=True,
        withdrawal_method="email instructor",
        required_disclosures=["AI-assisted summary", "exploratory sample"],
        notes="Not authorized as formal opinion of all students.",
    )


def _request(profile: AuthorizationProfile, context: AuthorizationContext) -> AuditRequest:
    return AuditRequest(
        project_name="auth",
        representation_mode=RepresentationMode.REAL_GROUP,
        source_records=[SourceRecord(source_id="s1", text="我支持AI预警。", metadata={})],
        ai_generated_summary="学生支持AI预警。",
        authorization_profile=profile,
        authorization_context=context,
        intended_purpose=context.intended_purpose,
        intended_audience=context.intended_audience,
        is_public=context.is_public,
    )


def _engine() -> AuthorizationEngine:
    return AuthorizationEngine(Path("rules/authorization_rules.yaml"))


def test_internal_course_use_matches_authorization() -> None:
    context = AuthorizationContext(
        intended_operation="summarize",
        intended_purpose="course_research",
        intended_audience="course_teacher",
        is_public=False,
        uses_ai=True,
    )
    result = _engine().evaluate(_request(_profile(), context))
    assert result.authorization_status == AuthorizationStatus.CONDITIONAL
    assert result.permitted_use is True


def test_public_release_exceeds_authorization() -> None:
    context = AuthorizationContext(
        intended_operation="summarize",
        intended_purpose="course_research",
        intended_audience="public",
        is_public=True,
        uses_ai=True,
    )
    result = _engine().evaluate(_request(_profile(), context))
    assert result.authorization_status == AuthorizationStatus.PROHIBITED
    assert "PUBLICATION_NOT_ALLOWED" in result.rule_ids_triggered


def test_commercial_use_exceeds_authorization() -> None:
    context = AuthorizationContext(
        intended_operation="summarize",
        intended_purpose="commercial",
        intended_audience="course_teacher",
        is_public=False,
        uses_ai=True,
    )
    result = _engine().evaluate(_request(_profile(), context))
    assert result.authorization_status == AuthorizationStatus.REAUTHORIZE


def test_missing_authorization_does_not_default_allow() -> None:
    profile = AuthorizationProfile(
        represented_subject="students",
        source_type="survey",
        withdrawal_supported=False,
    )
    context = AuthorizationContext(
        intended_operation="summarize",
        intended_purpose="course_research",
        intended_audience="course_teacher",
        is_public=False,
        uses_ai=True,
    )
    result = _engine().evaluate(_request(profile, context))
    assert result.authorization_status == AuthorizationStatus.UNKNOWN
    assert result.permitted_use is False


def test_ai_summary_allowed_but_ai_inference_not_allowed() -> None:
    context = AuthorizationContext(
        intended_operation="summarize",
        intended_purpose="course_research",
        intended_audience="course_teacher",
        is_public=False,
        uses_ai=True,
        includes_inference=True,
    )
    result = _engine().evaluate(_request(_profile(), context))
    assert "INFERENCE_NOT_ALLOWED" in result.rule_ids_triggered


def test_anonymous_summary_does_not_allow_identity_disclosure() -> None:
    context = AuthorizationContext(
        intended_operation="summarize",
        intended_purpose="course_research",
        intended_audience="course_teacher",
        is_public=False,
        uses_ai=True,
        includes_identity=True,
    )
    result = _engine().evaluate(_request(_profile(), context))
    assert result.authorization_status == AuthorizationStatus.PROHIBITED
    assert "IDENTITY_DISCLOSURE_NOT_ALLOWED" in result.rule_ids_triggered


def test_current_use_allowed_but_reuse_not_allowed() -> None:
    context = AuthorizationContext(
        intended_operation="summarize",
        intended_purpose="course_research",
        intended_audience="course_teacher",
        is_public=False,
        uses_ai=True,
        downstream_reuse_planned=True,
    )
    result = _engine().evaluate(_request(_profile(), context))
    assert result.authorization_status == AuthorizationStatus.REAUTHORIZE
    assert "REUSE_NOT_ALLOWED" in result.rule_ids_triggered
