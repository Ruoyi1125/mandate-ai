from __future__ import annotations

from mandate.claim_extractor import RuleBasedClaimParser
from mandate.schemas import SourceRecord, SupportStatus
from mandate.source_tracer import SourceTracer
from mandate.support_classifier import SupportClassifier


def _claim(text: str):
    return RuleBasedClaimParser().extract(text)[0]


def test_partial_support_does_not_support_majority_quantifier() -> None:
    claim = _claim("多数学生支持AI预警。")
    source = SourceRecord(source_id="s1", text="部分学生支持AI预警。", metadata={})
    match = SupportClassifier().classify(claim, source, similarity_score=0.9, rank=1)
    assert match.support_status == SupportStatus.PARTIALLY_SUPPORTED
    assert match.quantifier_supported is False


def test_deleted_condition_is_partial_not_direct_support() -> None:
    claim = _claim("学生支持AI预警。")
    source = SourceRecord(
        source_id="s1",
        text="学生支持AI预警，但前提是允许退出和申诉。",
        metadata={},
    )
    match = SupportClassifier().classify(claim, source, similarity_score=0.9, rank=1)
    assert match.support_status == SupportStatus.PARTIALLY_SUPPORTED
    assert match.condition_preserved is False


def test_explicit_contradiction_is_exposed() -> None:
    claim = _claim("学生支持AI预警。")
    source = SourceRecord(source_id="s1", text="学生反对AI预警。", metadata={})
    match = SupportClassifier().classify(claim, source, similarity_score=0.9, rank=1)
    assert match.support_status == SupportStatus.CONTRADICTED


def test_support_and_opposition_are_both_visible() -> None:
    claim = _claim("学生支持AI预警。")
    sources = [
        SourceRecord(source_id="s1", text="学生支持AI预警。", metadata={}),
        SourceRecord(source_id="s2", text="学生反对AI预警。", metadata={}),
    ]
    result = SourceTracer().trace_result([claim], sources)
    bundle = result.evidence_bundles[0]
    assert bundle.final_support_status == SupportStatus.PARTIALLY_SUPPORTED
    assert bundle.best_supporting_matches
    assert bundle.contradicting_matches
