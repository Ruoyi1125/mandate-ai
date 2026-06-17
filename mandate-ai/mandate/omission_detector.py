"""Minority omission detection placeholder."""

from __future__ import annotations

from mandate.schemas import OpinionCluster


class OmissionDetector:
    """Identify clusters that should be considered omitted."""

    def detect(self, clusters: list[OpinionCluster], summary: str) -> list[OpinionCluster]:
        omitted: list[OpinionCluster] = []
        lowered_summary = summary.lower()
        for cluster in clusters:
            if cluster.is_minority and cluster.label.lower() not in lowered_summary:
                omitted.append(cluster)
        return omitted
