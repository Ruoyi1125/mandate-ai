from __future__ import annotations

from pathlib import Path

import pytest

from mandate.input_loader import source_records_from_csv
from mandate.pipeline import AuditPipeline
from mandate.providers import MockProvider
from mandate.schemas import (
    AuditRequest,
    AuthorizationProfile,
    RepresentationMode,
    SourceRecord,
    SupportStatus,
)


def _profile() -> AuthorizationProfile:
    return AuthorizationProfile(
        represented_subject="students",
        source_type="survey",
        permitted_operations=["summarize", "audit"],
        prohibited_operations=["public_release"],
        permitted_purposes=["research"],
        prohibited_purposes=["advertising"],
        permitted_audiences=["internal"],
        duration="phase two",
        withdrawal_supported=True,
        required_disclosures=[],
    )


def _request(summary: str, sources: list[SourceRecord]) -> AuditRequest:
    return AuditRequest(
        project_name="source tracing",
        representation_mode=RepresentationMode.REAL_GROUP,
        source_records=sources,
        ai_generated_summary=summary,
        authorization_profile=_profile(),
        intended_purpose="research",
        intended_audience="internal",
        is_public=False,
    )


def _pipeline() -> AuditPipeline:
    return AuditPipeline(MockProvider(), Path("rules/authorization_rules.yaml"))


def test_summary_adds_new_unsupported_conclusion() -> None:
    passport = _pipeline().run(
        _request(
            "学生整体认为该系统利大于弊。",
            [SourceRecord(source_id="s1", text="学生担心隐私泄露。", metadata={})],
        )
    )
    trace = passport.source_trace_result
    assert trace is not None
    assert trace.unsupported_claim_ids


def test_empty_summary_gets_readable_pipeline_error() -> None:
    with pytest.raises(ValueError, match="summary"):
        _pipeline().run(
            _request(
                " ",
                [SourceRecord(source_id="s1", text="学生支持AI预警。", metadata={})],
            )
        )


def test_empty_sources_get_readable_pipeline_error() -> None:
    with pytest.raises(ValueError, match="source record"):
        _pipeline().run(_request("学生支持AI预警。", []))


def test_csv_input_field_error() -> None:
    with pytest.raises(ValueError, match="source_id"):
        source_records_from_csv("id,text\ns1,学生支持AI预警\n")


def test_duplicate_source_id_warning_flows_to_trace_result() -> None:
    passport = _pipeline().run(
        _request(
            "学生支持AI预警。",
            [
                SourceRecord(source_id="s1", text="学生支持AI预警。", metadata={}),
                SourceRecord(source_id="s1", text="学生反对AI预警。", metadata={}),
            ],
        )
    )
    trace = passport.source_trace_result
    assert trace is not None
    assert any("Duplicate source_id" in warning for warning in trace.warnings)


def test_problematic_demo_detects_multiple_risks() -> None:
    sources = source_records_from_csv(Path("data/demo/school_ai_warning_sources.csv").read_text(encoding="utf-8"))
    summary = Path("data/demo/problematic_summary.txt").read_text(encoding="utf-8")
    passport = _pipeline().run(_request(summary, sources))
    trace = passport.source_trace_result
    assert trace is not None
    all_warnings = "\n".join(
        warning
        for bundle in trace.evidence_bundles
        for warning in bundle.warnings
    )
    statuses = {bundle.final_support_status for bundle in trace.evidence_bundles}
    assert SupportStatus.PARTIALLY_SUPPORTED in statuses or SupportStatus.CONTRADICTED in statuses
    assert "overstate" in all_warnings or "依据不足" in all_warnings
