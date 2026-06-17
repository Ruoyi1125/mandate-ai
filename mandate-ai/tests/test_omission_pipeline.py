from __future__ import annotations

from pathlib import Path

import pytest

from mandate.input_loader import source_records_from_csv
from mandate.pipeline import AuditPipeline
from mandate.providers import MockProvider
from mandate.schemas import AuditRequest, AuthorizationProfile, RepresentationMode, SourceRecord


def _profile() -> AuthorizationProfile:
    return AuthorizationProfile(
        represented_subject="students",
        source_type="survey",
        permitted_operations=["summarize", "audit"],
        prohibited_operations=["public_release"],
        permitted_purposes=["research"],
        prohibited_purposes=["advertising"],
        permitted_audiences=["internal"],
        duration="phase three",
        withdrawal_supported=True,
        required_disclosures=[],
    )


def _request(summary: str, sources: list[SourceRecord]) -> AuditRequest:
    return AuditRequest(
        project_name="omission pipeline",
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


def test_pipeline_rejects_empty_summary() -> None:
    with pytest.raises(ValueError, match="summary"):
        _pipeline().run(_request(" ", [SourceRecord(source_id="s1", text="我支持AI预警。", metadata={})]))


def test_pipeline_rejects_empty_raw_sources() -> None:
    with pytest.raises(ValueError, match="source record"):
        _pipeline().run(_request("学生支持AI预警。", []))


def test_large_repeated_text_warning() -> None:
    sources = [
        SourceRecord(source_id=f"s{index}", text="我支持AI预警。", metadata={})
        for index in range(6)
    ]
    passport = _pipeline().run(_request("学生支持AI预警。", sources))

    assert passport.omission_result is not None
    assert any("repeated text" in warning for warning in passport.omission_result.warnings)


def test_single_source_warning() -> None:
    passport = _pipeline().run(
        _request("学生支持AI预警。", [SourceRecord(source_id="s1", text="我支持AI预警。", metadata={})])
    )

    assert passport.omission_result is not None
    assert any("smaller than 5" in warning for warning in passport.omission_result.warnings)


def test_demo_detects_appeal_exit_and_door_access_opposition() -> None:
    sources = source_records_from_csv(Path("data/demo/school_ai_warning_sources.csv").read_text(encoding="utf-8"))
    summary = Path("data/demo/problematic_summary.txt").read_text(encoding="utf-8")
    passport = _pipeline().run(_request(summary, sources))

    assert passport.omission_result is not None
    omission = passport.omission_result
    omitted_labels = {
        cluster.label
        for cluster in omission.clusters
        if cluster.cluster_id in omission.omitted_cluster_ids
    }
    assert "申诉、纠错与人工复核" in omitted_labels
    assert "退出权与自主选择" in omitted_labels
    assert "门禁等数据的用途边界" in omitted_labels
    assert omission.procedural_clusters_omitted
