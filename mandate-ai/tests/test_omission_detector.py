from __future__ import annotations

from mandate.claim_extractor import RuleBasedClaimParser
from mandate.omission_detector import OmissionDetector
from mandate.opinion_clusterer import OpinionClusterer
from mandate.opinion_extractor import OpinionExtractor
from mandate.schemas import CoverageStatus, SourceRecord, SourceTraceResult


def _omission(summary: str, sources: list[SourceRecord]):
    claims = RuleBasedClaimParser().extract(summary)
    units = OpinionExtractor().extract(sources)
    clusters = OpinionClusterer().cluster(
        units,
        total_participant_count=len({source.participant_id or source.source_id for source in sources}),
    )
    return OmissionDetector().detect(
        clusters=clusters,
        summary=summary,
        source_trace_result=SourceTraceResult(claims=claims),
        opinion_units=units,
    )


def test_conditional_support_summarized_as_unconditional_is_weakened() -> None:
    result = _omission(
        "学生支持该系统。",
        [SourceRecord(source_id="s1", text="只有在允许学生退出的条件下，我才支持该系统。", metadata={})],
    )
    assert result.weakened_cluster_ids
    assessment = result.coverage_assessments[0]
    assert assessment.status == CoverageStatus.WEAKENED
    assert assessment.condition_preserved is False


def test_strong_opposition_rewritten_as_light_concern_is_distorted() -> None:
    result = _omission(
        "部分学生对数据使用略有担忧。",
        [SourceRecord(source_id="s1", text="我坚决反对使用门禁数据。", metadata={})],
    )
    assert result.coverage_assessments[0].status == CoverageStatus.DISTORTED


def test_appeal_topic_fully_omitted() -> None:
    result = _omission(
        "学生支持AI预警。",
        [SourceRecord(source_id="s1", text="被误判后必须允许申诉。", metadata={})],
    )
    assert result.omitted_cluster_ids
    assert result.procedural_clusters_omitted


def test_keyword_coverage_with_changed_stance_is_distorted() -> None:
    result = _omission(
        "学生支持使用门禁数据进行预警。",
        [SourceRecord(source_id="s1", text="我反对使用门禁数据进行预警。", metadata={})],
    )
    assert result.coverage_assessments[0].status == CoverageStatus.DISTORTED


def test_summary_mentions_topic_but_deletes_condition() -> None:
    result = _omission(
        "学生支持AI预警。",
        [SourceRecord(source_id="s1", text="如果允许退出，我支持AI预警。", metadata={})],
    )
    assert result.coverage_assessments[0].status == CoverageStatus.WEAKENED
