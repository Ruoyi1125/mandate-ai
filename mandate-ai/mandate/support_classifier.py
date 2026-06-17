"""Rule-based support relation classifier for source tracing."""

from __future__ import annotations

from mandate.claim_extractor import (
    CONDITION_MARKERS,
    CONCERN_TERMS,
    DEGREE_WORDS,
    OPPOSE_TERMS,
    QUANTIFIERS,
    SUPPORT_TERMS,
)
from mandate.schemas import AtomicClaim, EvidenceMatch, SourceRecord, SupportStatus

QUANTIFIER_STRENGTH = {
    None: 0,
    "个别": 1,
    "少数": 1,
    "部分": 2,
    "多数": 3,
    "普遍": 4,
    "绝大多数": 4,
    "一致": 5,
    "所有": 5,
    "全部": 5,
}


class SupportClassifier:
    """Classify whether a candidate source supports, weakens, or contradicts a claim."""

    def classify(
        self,
        claim: AtomicClaim,
        source: SourceRecord,
        similarity_score: float,
        rank: int,
    ) -> EvidenceMatch:
        source_stance = self._infer_stance(source.text)
        stance_aligned = claim.stance == source_stance
        topic_related = self._topic_related(claim, source.text) or similarity_score >= 0.12
        condition_preserved = self._condition_preserved(claim, source.text)
        quantifier_supported = self._quantifier_supported(claim, source.text)

        if topic_related and self._opposes(claim.stance, source_stance):
            status = SupportStatus.CONTRADICTED
            explanation = "Candidate discusses the same topic but takes an opposing stance."
            confidence = 0.78
        elif not topic_related:
            status = SupportStatus.UNSUPPORTED
            explanation = "Candidate is lexically related too weakly to support the claim."
            confidence = 0.62
        elif stance_aligned and condition_preserved and quantifier_supported:
            status = SupportStatus.DIRECTLY_SUPPORTED
            explanation = "Subject, topic, stance, condition, and quantifier are aligned."
            confidence = 0.76
        elif stance_aligned and (not condition_preserved or not quantifier_supported):
            status = SupportStatus.PARTIALLY_SUPPORTED
            risks = []
            if not condition_preserved:
                risks.append("condition was weakened or removed")
            if not quantifier_supported:
                risks.append("quantifier or degree term is stronger than the source")
            explanation = "Candidate is relevant but only partially supports the claim: " + ", ".join(risks) + "."
            confidence = 0.72
        elif topic_related and source_stance in {"neutral", "uncertain"}:
            status = SupportStatus.INFERRED
            explanation = "Candidate discusses the topic, but does not directly assert the claim."
            confidence = 0.56
        else:
            status = SupportStatus.UNSUPPORTED
            explanation = "Candidate is related to the topic but does not support the conclusion."
            confidence = 0.58

        return EvidenceMatch(
            claim_id=claim.claim_id,
            source_id=source.source_id,
            similarity_score=round(similarity_score, 3),
            support_status=status,
            explanation=explanation,
            matched_text=source.text,
            source_text=source.text,
            rank=rank,
            condition_preserved=condition_preserved,
            stance_aligned=stance_aligned,
            quantifier_supported=quantifier_supported,
            confidence=confidence,
        )

    @staticmethod
    def _infer_stance(text: str) -> str:
        if any(term in text for term in OPPOSE_TERMS):
            return "oppose"
        if any(term in text for term in SUPPORT_TERMS):
            return "support"
        if any(term in text for term in CONCERN_TERMS):
            return "concern"
        if any(term in text for term in ["不确定", "观望", "中立"]):
            return "uncertain"
        return "neutral"

    @staticmethod
    def _opposes(claim_stance: str | None, source_stance: str) -> bool:
        return (claim_stance == "support" and source_stance == "oppose") or (
            claim_stance == "oppose" and source_stance == "support"
        )

    def _topic_related(self, claim: AtomicClaim, source_text: str) -> bool:
        if "利大于弊" in claim.text and "利大于弊" not in source_text:
            return False
        topic = claim.object or claim.text
        keywords = self._keywords(topic)
        if not keywords:
            return False
        return any(keyword in source_text for keyword in keywords)

    @staticmethod
    def _keywords(text: str) -> list[str]:
        stop = set("的了和与但并且以及认为觉得学生参与者多数部分少数普遍支持反对担心担忧主要最大核心")
        terms: list[str] = []
        for token in ["AI", "预警", "隐私", "标签", "误判", "申诉", "数据", "用途", "利大于弊", "退出"]:
            if token in text:
                terms.append(token)
        chinese_chunks = [char for char in text if "\u4e00" <= char <= "\u9fff" and char not in stop]
        terms.extend(chinese_chunks[:8])
        return list(dict.fromkeys(terms))

    @staticmethod
    def _condition_preserved(claim: AtomicClaim, source_text: str) -> bool:
        source_has_condition = any(marker in source_text for marker in CONDITION_MARKERS)
        claim_has_condition = bool(claim.condition) or any(
            marker in claim.text for marker in CONDITION_MARKERS
        )
        if source_has_condition and not claim_has_condition:
            return False
        return True

    @staticmethod
    def _quantifier_supported(claim: AtomicClaim, source_text: str) -> bool:
        if claim.quantifier in DEGREE_WORDS:
            return False
        source_quantifier = next((term for term in QUANTIFIERS if term in source_text), None)
        claim_strength = QUANTIFIER_STRENGTH.get(claim.quantifier, 0)
        source_strength = QUANTIFIER_STRENGTH.get(source_quantifier, 0)
        if claim_strength == 0:
            return True
        if source_strength == 0:
            return claim_strength <= 2
        return source_strength >= claim_strength
