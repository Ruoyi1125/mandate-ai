from __future__ import annotations

from mandate.opinion_extractor import OpinionExtractor
from mandate.opinion_clusterer import OpinionClusterer
from mandate.schemas import SourceRecord


def test_minority_privacy_issue_is_normatively_salient() -> None:
    sources = [
        SourceRecord(source_id="s1", participant_id="p1", text="我担心隐私泄露。", metadata={}),
        SourceRecord(source_id="s2", participant_id="p2", text="我支持AI预警。", metadata={}),
        SourceRecord(source_id="s3", participant_id="p3", text="我支持AI预警。", metadata={}),
        SourceRecord(source_id="s4", participant_id="p4", text="我支持AI预警。", metadata={}),
        SourceRecord(source_id="s5", participant_id="p5", text="我支持AI预警。", metadata={}),
        SourceRecord(source_id="s6", participant_id="p6", text="我支持AI预警。", metadata={}),
    ]
    clusters = OpinionClusterer().cluster(
        OpinionExtractor().extract(sources),
        total_participant_count=6,
    )

    privacy = next(cluster for cluster in clusters if cluster.label == "隐私与数据收集")
    assert privacy.is_numerical_minority is True
    assert privacy.is_normatively_salient is True


def test_low_frequency_ordinary_preference_is_not_salient() -> None:
    sources = [
        SourceRecord(source_id="s1", participant_id="p1", text="我希望界面颜色更柔和。", metadata={}),
        SourceRecord(source_id="s2", participant_id="p2", text="我支持AI预警。", metadata={}),
        SourceRecord(source_id="s3", participant_id="p3", text="我支持AI预警。", metadata={}),
        SourceRecord(source_id="s4", participant_id="p4", text="我支持AI预警。", metadata={}),
        SourceRecord(source_id="s5", participant_id="p5", text="我支持AI预警。", metadata={}),
    ]
    clusters = OpinionClusterer().cluster(
        OpinionExtractor().extract(sources),
        total_participant_count=5,
    )

    ordinary = next(cluster for cluster in clusters if "无条件反对" in cluster.label)
    privacy_or_rights = [cluster for cluster in clusters if cluster.is_normatively_salient]
    assert ordinary.is_numerical_minority is False or ordinary.is_normatively_salient is False
    assert ordinary.salience_reasons == []
    assert ordinary.cluster_id not in {cluster.cluster_id for cluster in privacy_or_rights}
