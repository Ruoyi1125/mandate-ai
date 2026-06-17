from __future__ import annotations

from pathlib import Path

from mandate.authorization_engine import AuthorizationEngine
from mandate.schemas import (
    AuditRequest,
    AuthorizationProfile,
    AuthorizationStatus,
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
            represented_subject="participants",
            source_type="survey",
            permitted_operations=["summarize"],
            prohibited_operations=["public_release"],
            permitted_purposes=["research"],
            prohibited_purposes=["advertising"],
            permitted_audiences=["internal"],
            duration="phase one",
            withdrawal_supported=True,
            required_disclosures=["Disclose AI use."],
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
    assert result.status == AuthorizationStatus.REAUTHORIZE_REQUIRED
    assert result.required_actions == ["Obtain renewed authorization."]


def test_authorization_rejects_prohibited_purpose() -> None:
    engine = AuthorizationEngine(Path("rules/authorization_rules.yaml"))
    result = engine.evaluate(_request(intended_purpose="advertising"))
    assert result.permitted_use is False
    assert "explicitly prohibited" in " ".join(result.reasons)
