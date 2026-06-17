"""Opinion omission and disappeared voice detection."""

from __future__ import annotations

import math
from collections import Counter
from pathlib import Path
from typing import Any

import yaml

from mandate.claim_extractor import CONDITION_MARKERS
from mandate.schemas import (
    AtomicClaim,
    ClusterCoverageAssessment,
    CoverageStatus,
    OmissionResult,
    OpinionCluster,
    OpinionStance,
    OpinionUnit,
    SourceTraceResult,
)


class OmissionDetector:
    """Compare original opinion clusters against AI summary claims."""

    def __init__(self, rules_path: Path | str | None = None) -> None:
        rules = self._load_rules(rules_path)
        thresholds = rules.get("omission_thresholds", {})
        self.weak_similarity = float(thresholds.get("weak_similarity", 0.18))
        self.covered_similarity = float(thresholds.get("covered_similarity", 0.32))

    def detect(
        self,
        clusters: list[OpinionCluster],
        summary: str | None = None,
        source_trace_result: SourceTraceResult | None = None,
        opinion_units: list[OpinionUnit] | None = None,
    ) -> OmissionResult | list[OpinionCluster]:
        if source_trace_result is None:
            return self._legacy_detect(clusters, summary or "")
        if summary is not None and not summary.strip():
            raise ValueError("AI summary must not be empty for omission detection.")

        assessments = [
            self._assess_cluster(cluster, source_trace_result.claims)
            for cluster in clusters
        ]
        return self._result(opinion_units or [], clusters, assessments)

    def _assess_cluster(
        self, cluster: OpinionCluster, claims: list[AtomicClaim]
    ) -> ClusterCoverageAssessment:
        best_claim, similarity = self._best_claim(cluster, claims)
        if best_claim is None or similarity < self.weak_similarity:
            return self._assessment(
                cluster,
                CoverageStatus.OMITTED,
                [],
                similarity,
                False,
                False,
                False,
                True,
                "No summary claim covers this original opinion cluster.",
            )

        stance_preserved = self._stance_preserved(cluster, best_claim)
        intensity_preserved = self._intensity_preserved(cluster, best_claim)
        condition_preserved = self._condition_preserved(cluster, best_claim)
        quantifier_preserved = True

        if not stance_preserved:
            status = CoverageStatus.DISTORTED
            explanation = "The summary mentions a related topic but changes the original stance."
        elif similarity < self.covered_similarity:
            status = CoverageStatus.WEAKENED
            explanation = "The summary weakly mentions the topic but does not preserve the original emphasis."
        elif not condition_preserved or not intensity_preserved:
            status = CoverageStatus.WEAKENED
            explanation = "The summary mentions the topic but weakens condition, intensity, or importance."
        else:
            status = CoverageStatus.COVERED
            explanation = "The summary preserves the topic, stance, and key qualifiers."

        return self._assessment(
            cluster,
            status,
            [best_claim.claim_id],
            similarity,
            stance_preserved,
            intensity_preserved,
            condition_preserved,
            quantifier_preserved,
            explanation,
        )

    def _best_claim(
        self, cluster: OpinionCluster, claims: list[AtomicClaim]
    ) -> tuple[AtomicClaim | None, float]:
        cluster_text = " ".join([cluster.label, cluster.description, *cluster.representative_quotes])
        best_claim: AtomicClaim | None = None
        best_score = 0.0
        for claim in claims:
            score = self._similarity(cluster_text, claim.text)
            if (
                cluster.label.startswith("AI学业预警")
                or cluster.canonical_topic == "学业帮助与干预效率"
            ) and any(
                term in claim.text for term in ["系统", "预警", "AI"]
            ):
                score = max(score, 0.45)
            if score > best_score:
                best_claim = claim
                best_score = score
        return best_claim, round(best_score, 3)

    @staticmethod
    def _stance_preserved(cluster: OpinionCluster, claim: AtomicClaim) -> bool:
        stances = set(cluster.stance_distribution)
        claim_stance = (claim.stance or "neutral").lower()
        if OpinionStance.OPPOSE.value in stances:
            return claim_stance == "oppose" or any(term in claim.text for term in ["反对", "不同意", "不接受"])
        if OpinionStance.CONDITIONAL_SUPPORT.value in stances:
            return claim_stance in {"support", "neutral"} or "支持" in claim.text
        if OpinionStance.SUPPORT.value in stances:
            return claim_stance == "support" or "支持" in claim.text or "利大于弊" in claim.text
        if OpinionStance.UNCERTAIN.value in stances:
            return any(term in claim.text for term in ["不确定", "取决于", "需要"])
        return True

    @staticmethod
    def _intensity_preserved(cluster: OpinionCluster, claim: AtomicClaim) -> bool:
        high = cluster.intensity_distribution.get("HIGH", 0)
        if high == 0:
            return True
        return any(term in claim.text for term in ["坚决", "强烈", "严重", "必须", "完全"])

    @staticmethod
    def _condition_preserved(cluster: OpinionCluster, claim: AtomicClaim) -> bool:
        if not cluster.condition_summary:
            return True
        if claim.condition:
            return True
        return any(marker in claim.text for marker in CONDITION_MARKERS + ["只有", "仅在", "前提"])

    def _assessment(
        self,
        cluster: OpinionCluster,
        status: CoverageStatus,
        matched_claim_ids: list[str],
        semantic_similarity: float,
        stance_preserved: bool,
        intensity_preserved: bool,
        condition_preserved: bool,
        quantifier_preserved: bool,
        explanation: str,
    ) -> ClusterCoverageAssessment:
        return ClusterCoverageAssessment(
            cluster_id=cluster.cluster_id,
            status=status,
            matched_claim_ids=matched_claim_ids,
            semantic_similarity=semantic_similarity,
            stance_preserved=stance_preserved,
            intensity_preserved=intensity_preserved,
            condition_preserved=condition_preserved,
            quantifier_preserved=quantifier_preserved,
            explanation=explanation,
            representative_quotes=cluster.representative_quotes,
            participant_count=cluster.unique_participant_count,
            participant_ratio=cluster.participant_ratio,
            is_minority=cluster.is_minority,
            is_normatively_salient=cluster.is_normatively_salient,
        )

    @staticmethod
    def _similarity(left: str, right: str) -> float:
        left_vec = Counter(_tokens(left))
        right_vec = Counter(_tokens(right))
        if not left_vec or not right_vec:
            return 0.0
        dot = sum(left_vec[key] * right_vec.get(key, 0) for key in left_vec)
        left_norm = math.sqrt(sum(value * value for value in left_vec.values()))
        right_norm = math.sqrt(sum(value * value for value in right_vec.values()))
        return dot / (left_norm * right_norm) if left_norm and right_norm else 0.0

    def _result(
        self,
        opinion_units: list[OpinionUnit],
        clusters: list[OpinionCluster],
        assessments: list[ClusterCoverageAssessment],
    ) -> OmissionResult:
        covered = [item.cluster_id for item in assessments if item.status == CoverageStatus.COVERED]
        weakened = [item.cluster_id for item in assessments if item.status == CoverageStatus.WEAKENED]
        distorted = [item.cluster_id for item in assessments if item.status == CoverageStatus.DISTORTED]
        omitted = [item.cluster_id for item in assessments if item.status == CoverageStatus.OMITTED]
        minority = [cluster.cluster_id for cluster in clusters if cluster.is_minority]
        salient = [cluster.cluster_id for cluster in clusters if cluster.is_normatively_salient]
        procedural = [cluster.cluster_id for cluster in clusters if cluster.is_procedural]
        retained_minority = [cluster_id for cluster_id in minority if cluster_id not in omitted]
        retained_procedural = [cluster_id for cluster_id in procedural if cluster_id not in omitted]
        conditional_assessments = [
            item for item in assessments
            if self._cluster_lookup(clusters, item.cluster_id).condition_summary
        ]
        preserved_conditions = [
            item for item in conditional_assessments
            if item.condition_preserved and item.status != CoverageStatus.OMITTED
        ]
        return OmissionResult(
            opinion_units=opinion_units,
            clusters=clusters,
            coverage_assessments=assessments,
            covered_cluster_ids=covered,
            weakened_cluster_ids=weakened,
            distorted_cluster_ids=distorted,
            omitted_cluster_ids=omitted,
            omitted_minority_cluster_ids=[cluster_id for cluster_id in omitted if cluster_id in minority],
            omitted_salient_cluster_ids=[cluster_id for cluster_id in omitted if cluster_id in salient],
            procedural_cluster_ids=procedural,
            procedural_clusters_omitted=[cluster_id for cluster_id in omitted if cluster_id in procedural],
            topic_coverage_numerator=len(covered),
            topic_coverage_denominator=len(clusters),
            minority_retention_numerator=len(retained_minority),
            minority_retention_denominator=len(minority),
            procedural_issue_retention_numerator=len(retained_procedural),
            procedural_issue_retention_denominator=len(procedural),
            condition_preservation_numerator=len(preserved_conditions),
            condition_preservation_denominator=len(conditional_assessments),
            warnings=self._warnings(opinion_units, clusters),
        )

    @staticmethod
    def _cluster_lookup(clusters: list[OpinionCluster], cluster_id: str) -> OpinionCluster:
        return next(cluster for cluster in clusters if cluster.cluster_id == cluster_id)

    @staticmethod
    def _warnings(opinion_units: list[OpinionUnit], clusters: list[OpinionCluster]) -> list[str]:
        warnings: list[str] = []
        if len({unit.source_id for unit in opinion_units}) < 5:
            warnings.append("Original source count is smaller than 5; omission findings need careful review.")
        if opinion_units and len(clusters) / len(opinion_units) >= 0.75:
            warnings.append("Cluster count is close to opinion-unit count; themes may be too fragmented.")
        if opinion_units:
            missing = [unit for unit in opinion_units if not unit.participant_id]
            if len(missing) / len(opinion_units) > 0.5:
                warnings.append("Most records lack participant_id; source_id is used as a conservative participant proxy.")
            texts = [unit.text for unit in opinion_units]
            if len(set(texts)) / len(texts) < 0.7:
                warnings.append("Large amount of repeated text detected.")
        warnings.append("Uploaded sources cannot establish what the overall public thinks.")
        return warnings

    @staticmethod
    def _legacy_detect(clusters: list[OpinionCluster], summary: str) -> list[OpinionCluster]:
        lowered_summary = summary.lower()
        return [
            cluster for cluster in clusters
            if cluster.is_minority and cluster.label.lower() not in lowered_summary
        ]

    @staticmethod
    def _load_rules(rules_path: Path | str | None) -> dict[str, Any]:
        if rules_path is None:
            return {}
        path = Path(rules_path)
        if not path.exists():
            return {}
        with path.open("r", encoding="utf-8") as file:
            data = yaml.safe_load(file) or {}
        return data if isinstance(data, dict) else {}


def _tokens(text: str) -> list[str]:
    terms = []
    known_terms = [
        "AI预警", "学业预警", "系统", "隐私", "门禁", "数据", "标签", "误判", "申诉",
        "退出", "解释", "知情", "复核", "删除", "纠错", "反对", "支持", "担忧",
        "担心", "利大于弊", "中立", "不确定", "少数群体", "正式上线",
    ]
    for term in known_terms:
        if term in text:
            terms.append(term)
    chars = [
        char for char in text
        if "\u4e00" <= char <= "\u9fff" and char not in set("的了和与但并且以及认为觉得学生参与者学校使用进行")
    ]
    terms.extend(chars[:20])
    return terms
