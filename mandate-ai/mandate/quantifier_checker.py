"""Quantifier and scope risk checks for claims."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from mandate.claim_extractor import DEGREE_WORDS
from mandate.schemas import AtomicClaim, EvidenceMatch, QuantifierAssessment, SourceRecord, SupportStatus


class QuantifierChecker:
    """Check whether a claim's quantifier is warranted by uploaded records."""

    def __init__(self, rules_path: Path | str | None = None) -> None:
        self.rules = self._load_rules(rules_path)
        self.supermajority_threshold = float(
            self.rules.get("quantifier_thresholds", {}).get("supermajority", 0.75)
        )
        self.partial_min_count = int(
            self.rules.get("quantifier_thresholds", {}).get("partial_min_count", 2)
        )

    def assess(
        self,
        claim: AtomicClaim,
        sources: list[SourceRecord],
        matches: list[EvidenceMatch],
    ) -> QuantifierAssessment:
        participants = self._participants(sources)
        total = len(participants)
        supporting = self._participants_for_status(
            sources, matches, {SupportStatus.DIRECTLY_SUPPORTED, SupportStatus.PARTIALLY_SUPPORTED}
        )
        opposing = self._participants_for_status(sources, matches, {SupportStatus.CONTRADICTED})
        support_count = len(supporting)
        opposing_count = len(opposing)
        ratio = support_count / total if total else 0.0
        quantifier = claim.quantifier

        if quantifier in DEGREE_WORDS:
            return QuantifierAssessment(
                claim_id=claim.claim_id,
                quantifier=quantifier,
                supported=False,
                supporting_participant_count=support_count,
                opposing_participant_count=opposing_count,
                total_participant_count=total,
                observed_ratio=round(ratio, 3),
                explanation=f"'{quantifier}' requires comparison across themes; current source tracing cannot prove it.",
            )

        supported = self._is_supported(quantifier, support_count, opposing_count, total, ratio)
        explanation = self._explain(quantifier, supported, support_count, opposing_count, total, ratio)
        return QuantifierAssessment(
            claim_id=claim.claim_id,
            quantifier=quantifier,
            supported=supported,
            supporting_participant_count=support_count,
            opposing_participant_count=opposing_count,
            total_participant_count=total,
            observed_ratio=round(ratio, 3),
            explanation=explanation,
        )

    def _is_supported(
        self,
        quantifier: str | None,
        support_count: int,
        opposing_count: int,
        total: int,
        ratio: float,
    ) -> bool:
        if total == 0:
            return False
        if quantifier in {"所有", "全部", "一致"}:
            return support_count == total and opposing_count == 0
        if quantifier == "绝大多数":
            return ratio >= self.supermajority_threshold and opposing_count == 0
        if quantifier in {"多数", "普遍"}:
            return ratio > 0.5
        if quantifier == "部分":
            return support_count >= self.partial_min_count
        if quantifier in {"少数", "个别"}:
            return 0 < support_count <= total / 2
        if quantifier is None:
            return support_count > 0
        return False

    @staticmethod
    def _explain(
        quantifier: str | None,
        supported: bool,
        support_count: int,
        opposing_count: int,
        total: int,
        ratio: float,
    ) -> str:
        prefix = "在当前上传材料中"
        result = "有依据" if supported else "依据不足"
        return (
            f"{prefix}，该数量表述{result}：支持 {support_count}/{total}，"
            f"反对 {opposing_count}/{total}，观察比例 {ratio:.2f}。"
        )

    @staticmethod
    def _participants(sources: list[SourceRecord]) -> set[str]:
        return {
            source.participant_id or source.source_id
            for source in sources
        }

    def _participants_for_status(
        self,
        sources: list[SourceRecord],
        matches: list[EvidenceMatch],
        statuses: set[SupportStatus],
    ) -> set[str]:
        source_lookup = {source.source_id: source for source in sources}
        participants: set[str] = set()
        for match in matches:
            if match.support_status not in statuses:
                continue
            source = source_lookup.get(match.source_id)
            if source is not None:
                participants.add(source.participant_id or source.source_id)
        return participants

    @staticmethod
    def _load_rules(rules_path: Path | str | None) -> dict[str, Any]:
        if rules_path is None:
            return {}
        path = Path(rules_path)
        if not path.exists():
            return {}
        with path.open("r", encoding="utf-8") as file:
            data = yaml.safe_load(file) or {}
        if not isinstance(data, dict):
            return {}
        return data
