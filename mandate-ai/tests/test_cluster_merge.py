from __future__ import annotations

from pathlib import Path

from mandate.input_loader import source_records_from_csv
from mandate.opinion_clusterer import OpinionClusterer
from mandate.opinion_extractor import OpinionExtractor


def test_demo_clusters_are_merged_to_reasonable_range() -> None:
    sources = source_records_from_csv(Path("data/demo/school_ai_warning_sources.csv").read_text(encoding="utf-8"))
    units = OpinionExtractor().extract(sources)
    clusters = OpinionClusterer(Path("rules/authorization_rules.yaml")).cluster(
        units,
        total_participant_count=24,
    )

    labels = {cluster.label for cluster in clusters}
    assert 7 <= len(clusters) <= 10
    assert "申诉、纠错与人工复核" in labels
    assert "退出权与自主选择" in labels
    assert "门禁等数据的用途边界" in labels
    appeal = next(cluster for cluster in clusters if cluster.label == "申诉、纠错与人工复核")
    assert {"申诉机制", "纠错机制"} <= set(appeal.subtopics)
    assert appeal.representative_quotes
    assert appeal.unique_participant_count == 3
