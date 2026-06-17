from __future__ import annotations

from pathlib import Path

from mandate.input_loader import source_records_from_csv
from mandate.passport_generator import PassportExporter
from mandate.pipeline import AuditPipeline
from mandate.providers import MockProvider
from mandate.schemas import (
    AuditRequest,
    AuthorizationContext,
    AuthorizationProfile,
    AuthorityBasis,
    FinalStatus,
    RepresentationMode,
)


def _passport():
    sources = source_records_from_csv(Path("data/demo/school_ai_warning_sources.csv").read_text(encoding="utf-8"))
    summary = Path("data/demo/problematic_summary.txt").read_text(encoding="utf-8")
    profile = AuthorizationProfile(
        authorization_id="passport-auth",
        represented_subject="students",
        authorizing_party="participants",
        authority_basis=AuthorityBasis.RESEARCH_CONSENT,
        source_type="survey",
        permitted_operations=["summarize", "audit"],
        permitted_purposes=["course_research"],
        permitted_audiences=["course_teacher"],
        allow_publication=False,
        allow_ai_processing=True,
        allow_inference=False,
        allow_identity_disclosure=False,
        allow_reuse=False,
        allow_model_training=False,
        withdrawal_supported=True,
        withdrawal_method="email",
        required_disclosures=["AI-assisted summary"],
    )
    context = AuthorizationContext(
        intended_operation="summarize",
        intended_purpose="course_research",
        intended_audience="course_teacher",
        is_public=False,
        uses_ai=True,
    )
    return AuditPipeline(MockProvider(), Path("rules/authorization_rules.yaml")).run(
        AuditRequest(
            project_name="passport",
            representation_mode=RepresentationMode.REAL_GROUP,
            source_records=sources,
            ai_generated_summary=summary,
            authorization_profile=profile,
            authorization_context=context,
            intended_purpose="course_research",
            intended_audience="course_teacher",
            is_public=False,
        )
    )


def test_passport_has_no_single_ethics_score_and_has_dimensions() -> None:
    passport = _passport()
    dumped = passport.model_dump()
    assert "score" not in dumped
    assert passport.source_trace_result is not None
    assert passport.omission_result is not None
    assert passport.authorization_assessment is not None
    assert passport.final_status == FinalStatus.CONDITIONAL


def test_passport_export_json_markdown_html() -> None:
    passport = _passport()
    exporter = PassportExporter()
    assert "REPRESENTATION PASSPORT" in exporter.to_markdown(passport)
    assert exporter.to_json(passport).startswith("{")
    assert exporter.to_html(passport).startswith("<!doctype html>")
