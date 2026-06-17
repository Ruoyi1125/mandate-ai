from __future__ import annotations

from mandate.opinion_extractor import OpinionExtractor
from mandate.opinion_clusterer import OpinionClusterer
from mandate.schemas import SourceRecord


def test_same_participant_repeated_opinions_count_once() -> None:
    sources = [
        SourceRecord(source_id="s1", participant_id="p1", text="我支持AI预警。", metadata={}),
        SourceRecord(source_id="s2", participant_id="p1", text="我也支持AI预警。", metadata={}),
    ]
    units = OpinionExtractor().extract(sources)
    clusters = OpinionClusterer().cluster(units, total_participant_count=1)

    ai_cluster = next(cluster for cluster in clusters if cluster.label.startswith("学业帮助"))
    assert ai_cluster.unique_participant_count == 1


def test_support_and_opposition_can_share_one_topic_cluster() -> None:
    sources = [
        SourceRecord(source_id="s1", participant_id="p1", text="我支持AI预警。", metadata={}),
        SourceRecord(source_id="s2", participant_id="p2", text="我反对AI预警。", metadata={}),
    ]
    units = OpinionExtractor().extract(sources)
    clusters = OpinionClusterer().cluster(units, total_participant_count=2)

    cluster = next(cluster for cluster in clusters if cluster.label.startswith("学业帮助"))
    assert cluster.stance_distribution["SUPPORT"] == 1
    assert cluster.stance_distribution["OPPOSE"] == 1
