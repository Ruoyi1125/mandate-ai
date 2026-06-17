"""Rule-based extraction of opinion units from source records."""

from __future__ import annotations

import re
from abc import ABC, abstractmethod

from mandate.claim_extractor import CONDITION_MARKERS
from mandate.schemas import (
    OpinionIntensity,
    OpinionStance,
    OpinionUnit,
    SourceRecord,
)

PROCEDURAL_TERMS = ["申诉", "解释", "告知", "知情", "退出", "撤回", "复核", "人工处理", "删除", "更正", "纠错"]
OPPOSE_TERMS = ["坚决反对", "完全不同意", "反对", "不同意", "不接受", "不能", "不应"]
SUPPORT_TERMS = ["支持", "同意", "接受", "赞成", "认可", "可以"]
UNCERTAIN_TERMS = ["不确定", "需要进一步了解", "取决于", "观望", "不好说"]
HIGH_INTENSITY_TERMS = ["坚决", "完全", "必须", "严重", "强烈", "绝不", "不可"]
LOW_INTENSITY_TERMS = ["略微", "有点", "轻微", "比较"]


class OpinionProvider(ABC):
    """Optional future provider interface for opinion extraction."""

    @abstractmethod
    def extract_opinions(self, sources: list[SourceRecord]) -> list[OpinionUnit]:
        """Extract opinion units from source records."""


class RuleBasedOpinionParser:
    """Transparent local Chinese opinion parser."""

    def extract(self, sources: list[SourceRecord]) -> list[OpinionUnit]:
        if not sources:
            raise ValueError("At least one source record is required for opinion extraction.")

        units: list[OpinionUnit] = []
        for source in sources:
            for fragment in self._split(source.text):
                opinion_id = f"opinion_{len(units) + 1}"
                units.append(self._build_unit(opinion_id, source, fragment))
        return units

    def _split(self, text: str) -> list[str]:
        parts = re.split(r"。|；|;|，但|,但|但是|不过|然而|同时|并且|而且|，而|,而", text)
        fragments = [part.strip(" ，,。") for part in parts if part.strip(" ，,。")]
        expanded: list[str] = []
        for fragment in fragments:
            expanded.extend(self._split_procedural_compound(fragment))
        return expanded

    @staticmethod
    def _split_procedural_compound(fragment: str) -> list[str]:
        if "而且" not in fragment and "并且" not in fragment:
            return [fragment]
        return [
            part.strip(" ，,。")
            for part in re.split(r"而且|并且", fragment)
            if part.strip(" ，,。")
        ]

    def _build_unit(
        self, opinion_id: str, source: SourceRecord, text: str
    ) -> OpinionUnit:
        topic = self._topic(text)
        stance = self._stance(text)
        is_procedural = any(term in text for term in PROCEDURAL_TERMS)
        if is_procedural and stance == OpinionStance.NEUTRAL:
            stance = OpinionStance.CONDITIONAL_SUPPORT
        return OpinionUnit(
            opinion_id=opinion_id,
            source_id=source.source_id,
            participant_id=source.participant_id,
            text=text,
            topic=topic,
            stance=stance,
            intensity=self._intensity(text, stance),
            condition=self._condition(text),
            target=self._target(text, topic),
            is_procedural=is_procedural,
            metadata={"source_metadata": source.metadata},
        )

    @staticmethod
    def _stance(text: str) -> OpinionStance:
        has_condition = any(marker in text for marker in CONDITION_MARKERS + ["只有", "仅在"])
        if any(term in text for term in OPPOSE_TERMS):
            return OpinionStance.OPPOSE
        if any(term in text for term in SUPPORT_TERMS):
            return OpinionStance.CONDITIONAL_SUPPORT if has_condition else OpinionStance.SUPPORT
        if "担心" in text or "担忧" in text or "顾虑" in text:
            return OpinionStance.MIXED
        if any(term in text for term in UNCERTAIN_TERMS):
            return OpinionStance.UNCERTAIN
        return OpinionStance.NEUTRAL

    @staticmethod
    def _intensity(text: str, stance: OpinionStance) -> OpinionIntensity:
        if any(term in text for term in HIGH_INTENSITY_TERMS):
            return OpinionIntensity.HIGH
        if any(term in text for term in LOW_INTENSITY_TERMS):
            return OpinionIntensity.LOW
        if stance == OpinionStance.OPPOSE:
            return OpinionIntensity.MEDIUM
        return OpinionIntensity.MEDIUM

    @staticmethod
    def _condition(text: str) -> str | None:
        for marker in CONDITION_MARKERS + ["只有", "仅在"]:
            if marker in text:
                if marker == "条件下":
                    match = re.search(r"在(.{1,40}?条件下)", text)
                    return match.group(0) if match else marker
                return text[text.index(marker) :].strip(" ，,。")
        return None

    @staticmethod
    def _topic(text: str) -> str:
        if any(term in text for term in SUPPORT_TERMS) and any(
            term in text for term in ["AI预警", "学业预警", "该系统", "系统"]
        ):
            return "AI学业预警"
        topic_terms = [
            ("申诉", "申诉机制"),
            ("复核", "人工复核"),
            ("人工处理", "人工复核"),
            ("退出", "退出权"),
            ("撤回", "撤回授权"),
            ("解释", "知情与解释"),
            ("告知", "知情与解释"),
            ("知情", "知情与解释"),
            ("公开", "知情与解释"),
            ("说明", "知情与解释"),
            ("数据来源", "知情与解释"),
            ("删除", "数据删除"),
            ("更正", "纠错机制"),
            ("纠错", "纠错机制"),
            ("门禁", "门禁数据用途"),
            ("消费记录", "数据用途"),
            ("数据用途", "数据用途"),
            ("隐私", "隐私"),
            ("标签", "标签化"),
            ("误判", "误判"),
            ("少数群体", "弱势或少数群体"),
            ("转专业", "弱势或少数群体"),
            ("效率", "提高帮助效率"),
            ("早点发现", "提高帮助效率"),
            ("资源分配", "提高帮助效率"),
            ("正式上线", "无条件反对"),
            ("AI预警", "AI学业预警"),
            ("学业预警", "AI学业预警"),
        ]
        for term, topic in topic_terms:
            if term in text:
                return topic
        if "不确定" in text or "中立" in text or "取决于" in text:
            return "中立或信息不足"
        return "其他意见"

    @staticmethod
    def _target(text: str, topic: str) -> str | None:
        if topic != "其他意见":
            return topic
        return text[:24]


class OpinionExtractor:
    """Extract opinion units using a provider or local rules."""

    def __init__(self, provider: OpinionProvider | None = None) -> None:
        self.provider = provider

    def extract(self, sources: list[SourceRecord]) -> list[OpinionUnit]:
        if self.provider is None:
            return RuleBasedOpinionParser().extract(sources)
        units = self.provider.extract_opinions(sources)
        if not isinstance(units, list):
            raise TypeError("Opinion provider must return a list.")
        if not all(isinstance(unit, OpinionUnit) for unit in units):
            raise TypeError("Opinion provider returned non-OpinionUnit items.")
        return units
