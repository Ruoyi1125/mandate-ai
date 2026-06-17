"""Opinion clustering for omission analysis."""

from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import yaml

try:
    from sklearn.cluster import KMeans
    from sklearn.feature_extraction.text import TfidfVectorizer
except ModuleNotFoundError:  # pragma: no cover - depends on optional environment
    KMeans = None  # type: ignore[assignment]
    TfidfVectorizer = None  # type: ignore[assignment]

from mandate.schemas import (
    OpinionCluster,
    OpinionIntensity,
    OpinionStance,
    OpinionUnit,
    SourceRecord,
)


class OpinionClusterer:
    """Aggregate opinion units into topic clusters with salience metadata."""

    def __init__(
        self,
        rules_path: Path | str | None = None,
        minority_ratio_threshold: float | None = None,
        normative_terms: list[str] | None = None,
    ) -> None:
        rules = self._load_rules(rules_path)
        thresholds = rules.get("omission_thresholds", {})
        self.minority_ratio_threshold = (
            minority_ratio_threshold
            if minority_ratio_threshold is not None
            else float(
                thresholds.get(
                    "numerical_minority_threshold",
                    thresholds.get("numerical_minority_ratio", 0.2),
                )
            )
        )
        self.maximum_recommended_clusters = int(thresholds.get("maximum_recommended_clusters", 10))
        self.minimum_cluster_size = int(thresholds.get("minimum_cluster_size", 1))
        self.merge_similarity_threshold = float(thresholds.get("merge_similarity_threshold", 0.72))
        self.normative_terms = normative_terms or list(
            rules.get(
                "normative_salience_terms",
                ["隐私", "申诉", "退出", "复核", "纠错", "严重误判", "坚决反对"],
            )
        )

    def cluster(
        self,
        items: list[OpinionUnit] | list[SourceRecord],
        total_participant_count: int | None = None,
        requested_cluster_count: int | None = None,
    ) -> list[OpinionCluster]:
        if not items:
            return []
        if isinstance(items[0], SourceRecord):
            from mandate.opinion_extractor import OpinionExtractor

            opinion_units = OpinionExtractor().extract(items)  # type: ignore[arg-type]
        else:
            opinion_units = items  # type: ignore[assignment]

        participant_total = total_participant_count or len(
            {unit.participant_id or unit.source_id for unit in opinion_units}
        )
        grouped: dict[str, list[OpinionUnit]]
        if requested_cluster_count is not None and requested_cluster_count > 0:
            grouped = self._cluster_with_tfidf(opinion_units, requested_cluster_count)
        else:
            grouped = defaultdict(list)
            for unit in opinion_units:
                grouped[self._canonical_topic(unit.topic)].append(unit)

        clusters: list[OpinionCluster] = []
        for index, (topic, units) in enumerate(sorted(grouped.items()), start=1):
            clusters.append(
                self._build_cluster(
                    index=index,
                    topic=topic,
                    units=units,
                    participant_total=participant_total,
                )
            )
        return clusters

    def _cluster_with_tfidf(
        self, opinion_units: list[OpinionUnit], requested_cluster_count: int
    ) -> dict[str, list[OpinionUnit]]:
        if (
            KMeans is None
            or TfidfVectorizer is None
            or len(opinion_units) <= requested_cluster_count
        ):
            grouped: dict[str, list[OpinionUnit]] = defaultdict(list)
            for unit in opinion_units:
                grouped[self._canonical_topic(unit.topic)].append(unit)
            return grouped

        vectorizer = TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 4))
        matrix = vectorizer.fit_transform([unit.text for unit in opinion_units])
        model = KMeans(n_clusters=requested_cluster_count, n_init=10, random_state=13)
        labels = model.fit_predict(matrix)
        grouped = defaultdict(list)
        for label, unit in zip(labels, opinion_units, strict=True):
            grouped[f"tfidf_cluster_{label}"].append(unit)
        return {
            self._canonical_topic(self._dominant_topic(units)): units
            for units in grouped.values()
        }

    def _build_cluster(
        self,
        index: int,
        topic: str,
        units: list[OpinionUnit],
        participant_total: int,
    ) -> OpinionCluster:
        participants = {unit.participant_id or unit.source_id for unit in units}
        ratio = len(participants) / participant_total if participant_total else 0.0
        stance_counts = Counter(unit.stance.value for unit in units)
        intensity_counts = Counter(unit.intensity.value for unit in units)
        is_procedural = any(unit.is_procedural for unit in units)
        salience_reasons = self._salience_reasons(units, is_procedural)
        is_numerical_minority = ratio < self.minority_ratio_threshold
        is_normatively_salient = bool(salience_reasons)
        subtopics = sorted({unit.topic for unit in units})
        merged_from = [f"premerge:{topic}" for topic in subtopics]
        return OpinionCluster(
            cluster_id=f"cluster_{index}",
            label=self._label(topic, stance_counts),
            description=self._description(topic, units),
            opinion_ids=[unit.opinion_id for unit in units],
            source_ids=list(dict.fromkeys(unit.source_id for unit in units)),
            unique_participant_count=len(participants),
            stance_distribution=dict(stance_counts),
            intensity_distribution=dict(intensity_counts),
            condition_summary=self._condition_summary(units),
            is_minority=is_numerical_minority or is_normatively_salient,
            is_procedural=is_procedural,
            participant_ratio=round(ratio, 3),
            is_numerical_minority=is_numerical_minority,
            is_normatively_salient=is_normatively_salient,
            salience_reasons=salience_reasons,
            representative_quotes=[unit.text for unit in units[:3]],
            canonical_topic=topic,
            subtopics=subtopics,
            merged_from_cluster_ids=merged_from,
            merge_explanation=(
                f"Merged subtopics into canonical topic '{topic}'."
                if len(subtopics) > 1
                else None
            ),
        )

    @staticmethod
    def _dominant_topic(units: list[OpinionUnit]) -> str:
        return Counter(unit.topic for unit in units).most_common(1)[0][0]

    @staticmethod
    def _canonical_topic(topic: str) -> str:
        mapping = {
            "提高帮助效率": "学业帮助与干预效率",
            "AI学业预警": "学业帮助与干预效率",
            "隐私": "隐私与数据收集",
            "数据删除": "隐私与数据收集",
            "数据用途": "隐私与数据收集",
            "门禁数据用途": "门禁等数据的用途边界",
            "误判": "误判与标签化",
            "标签化": "误判与标签化",
            "弱势或少数群体": "误判与标签化",
            "知情与解释": "解释、知情与透明",
            "申诉机制": "申诉、纠错与人工复核",
            "纠错机制": "申诉、纠错与人工复核",
            "人工复核": "申诉、纠错与人工复核",
            "退出权": "退出权与自主选择",
            "撤回授权": "退出权与自主选择",
            "无条件反对": "无条件反对或对学校的不信任",
            "中立或信息不足": "信息不足或中立态度",
            "其他意见": "无条件反对或对学校的不信任",
        }
        return mapping.get(topic, topic)

    @staticmethod
    def _label(topic: str, stance_counts: Counter[str]) -> str:
        if OpinionStance.OPPOSE.value in stance_counts and OpinionStance.SUPPORT.value in stance_counts:
            return f"{topic}（立场分歧）"
        return topic

    @staticmethod
    def _description(topic: str, units: list[OpinionUnit]) -> str:
        return f"{len(units)} 条观点涉及 {topic}。"

    @staticmethod
    def _condition_summary(units: list[OpinionUnit]) -> str | None:
        conditions = [unit.condition for unit in units if unit.condition]
        if not conditions:
            return None
        return "；".join(list(dict.fromkeys(conditions))[:3])

    def _salience_reasons(self, units: list[OpinionUnit], is_procedural: bool) -> list[str]:
        text = " ".join(unit.text for unit in units)
        reasons = [term for term in self.normative_terms if term in text]
        if is_procedural and "程序救济" not in reasons:
            reasons.append("程序救济")
        if any(unit.intensity == OpinionIntensity.HIGH for unit in units) and "强烈表达" not in reasons:
            reasons.append("强烈表达")
        return list(dict.fromkeys(reasons))

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
