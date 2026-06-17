"""Opinion clustering placeholder."""

from __future__ import annotations

from mandate.schemas import OpinionCluster, SourceRecord


class OpinionClusterer:
    """Create a deterministic coarse cluster for phase-one audits."""

    def cluster(self, sources: list[SourceRecord]) -> list[OpinionCluster]:
        if not sources:
            return []
        quotes = [source.text[:160] for source in sources[:3]]
        return [
            OpinionCluster(
                cluster_id="cluster_1",
                label="Primary source opinions",
                description="Mock cluster containing submitted source records.",
                source_ids=[source.source_id for source in sources],
                stance_distribution={"unspecified": len(sources)},
                is_minority=False,
                representative_quotes=quotes,
            )
        ]
