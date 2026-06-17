from __future__ import annotations

from mandate.claim_extractor import RuleBasedClaimParser
from mandate.schemas import SourceRecord, SupportStatus
from mandate.source_tracer import SourceTracer


def test_tfidf_retriever_returns_top_five_candidates() -> None:
    claim = RuleBasedClaimParser().extract("学生担心隐私泄露。")[0]
    sources = [
        SourceRecord(source_id=f"s{index}", text=f"学生意见 {index} 隐私 数据 AI", metadata={})
        for index in range(7)
    ]
    result = SourceTracer().trace_result([claim], sources)
    matches = result.evidence_bundles[0].candidate_matches
    assert len(matches) == 5
    assert [match.rank for match in matches] == [1, 2, 3, 4, 5]


def test_one_source_adds_small_sample_warning() -> None:
    claim = RuleBasedClaimParser().extract("学生支持AI预警。")[0]
    result = SourceTracer().trace_result(
        [claim],
        [SourceRecord(source_id="s1", text="学生支持AI预警", metadata={})],
    )
    assert any("smaller than 3" in warning for warning in result.warnings)
    assert result.evidence_bundles[0].final_support_status == SupportStatus.DIRECTLY_SUPPORTED
