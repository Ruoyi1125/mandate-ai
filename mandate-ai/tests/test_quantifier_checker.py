from __future__ import annotations

from mandate.claim_extractor import RuleBasedClaimParser
from mandate.quantifier_checker import QuantifierChecker
from mandate.schemas import SourceRecord
from mandate.source_tracer import SourceTracer


def test_same_participant_multiple_sources_counts_once() -> None:
    claim = RuleBasedClaimParser().extract("多数学生支持AI预警。")[0]
    sources = [
        SourceRecord(source_id="s1", participant_id="p1", text="学生支持AI预警。", metadata={}),
        SourceRecord(source_id="s2", participant_id="p1", text="我也支持AI预警。", metadata={}),
    ]
    bundle = SourceTracer(quantifier_checker=QuantifierChecker()).trace_result([claim], sources).evidence_bundles[0]
    assert bundle.quantifier_assessment is not None
    assert bundle.quantifier_assessment.total_participant_count == 1
    assert bundle.quantifier_assessment.supporting_participant_count == 1


def test_major_concern_cannot_be_proven_without_theme_comparison() -> None:
    claim = RuleBasedClaimParser().extract("主要担忧集中在隐私保护。")[0]
    sources = [
        SourceRecord(source_id="s1", text="学生担心隐私保护。", metadata={}),
        SourceRecord(source_id="s2", text="学生担心误判和申诉。", metadata={}),
    ]
    bundle = SourceTracer(quantifier_checker=QuantifierChecker()).trace_result([claim], sources).evidence_bundles[0]
    assert bundle.quantifier_assessment is not None
    assert bundle.quantifier_assessment.supported is False
    assert "requires comparison" in bundle.quantifier_assessment.explanation
