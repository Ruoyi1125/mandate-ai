"""Rule-based atomic claim extraction with a provider extension point."""

from __future__ import annotations

import re

from mandate.providers.base import LLMProvider
from mandate.schemas import AtomicClaim

QUANTIFIERS = ["绝大多数", "所有", "全部", "一致", "多数", "普遍", "部分", "少数", "个别"]
DEGREE_WORDS = ["主要", "最大", "核心", "强烈", "明显", "基本", "略微"]
CONDITION_MARKERS = ["如果", "只要", "前提是", "除非", "条件下", "仅在", "只有"]
SUPPORT_TERMS = ["支持", "赞成", "认可", "同意", "利大于弊", "可以使用", "愿意"]
OPPOSE_TERMS = ["反对", "不同意", "不应", "拒绝", "不能使用", "弊大于利"]
CONCERN_TERMS = ["担心", "担忧", "顾虑", "害怕", "忧虑"]
UNCERTAIN_TERMS = ["不确定", "观望", "中立", "不好说"]


class RuleBasedClaimParser:
    """Split a summary into small claims using transparent local rules."""

    def extract(self, summary: str) -> list[AtomicClaim]:
        cleaned = summary.strip()
        if not cleaned:
            raise ValueError("AI generated summary must not be empty.")

        fragments = self._split_summary(cleaned)
        claims: list[AtomicClaim] = []
        for fragment in fragments:
            claim_texts = self._expand_compound_fragment(fragment)
            for claim_text in claim_texts:
                normalized = claim_text.strip(" ，,；;。")
                if normalized:
                    claims.append(self._build_claim(len(claims) + 1, normalized))
        return claims

    def _split_summary(self, summary: str) -> list[str]:
        parts = re.split(r"[。.!?\n；;]+", summary)
        return [part.strip() for part in parts if part.strip()]

    def _expand_compound_fragment(self, fragment: str) -> list[str]:
        if "担心" in fragment and "和" in fragment:
            prefix, rest = fragment.split("担心", 1)
            concerns = [item.strip() for item in re.split(r"和|、|以及", rest) if item.strip()]
            subject = self._infer_subject(prefix) or "参与者"
            head: list[str] = []
            if prefix.strip():
                support_piece = prefix.strip(" ，,但")
                if any(term in support_piece for term in SUPPORT_TERMS + OPPOSE_TERMS):
                    head.append(support_piece)
            return head + [f"{subject}担心{concern}" for concern in concerns]

        pieces = re.split(r"，但|,但|，(?=主要|最大|核心|整体)|但|并且|同时|且|；|;", fragment)
        return [piece.strip() for piece in pieces if piece.strip()]

    def _build_claim(self, index: int, text: str) -> AtomicClaim:
        return AtomicClaim(
            claim_id=f"claim_{index}",
            text=text,
            quantifier=self._find_first(text, QUANTIFIERS + DEGREE_WORDS),
            stance=self._infer_stance(text),
            importance=self._importance(text),
            subject=self._infer_subject(text),
            predicate=self._infer_predicate(text),
            object=self._infer_object(text),
            condition=self._infer_condition(text),
            certainty=self._find_first(text, ["明确", "可能", "认为", "觉得"]),
        )

    @staticmethod
    def _find_first(text: str, terms: list[str]) -> str | None:
        for term in terms:
            if term in text:
                return term
        return None

    @staticmethod
    def _infer_stance(text: str) -> str:
        if any(term in text for term in OPPOSE_TERMS):
            return "oppose"
        if any(term in text for term in SUPPORT_TERMS):
            return "support"
        if any(term in text for term in CONCERN_TERMS):
            return "concern"
        if any(term in text for term in UNCERTAIN_TERMS):
            return "uncertain"
        return "neutral"

    @staticmethod
    def _infer_subject(text: str) -> str | None:
        match = re.match(
            r"^(所有|全部|一致|绝大多数|多数|普遍|部分|少数|个别)?"
            r"([^支持赞成认可同意反对不同担心担忧顾虑认为觉得]+?)"
            r"(支持|赞成|认可|同意|反对|不同意|担心|担忧|顾虑|认为|觉得)",
            text,
        )
        if match:
            subject = match.group(2).strip(" ，,的")
            return subject or None
        for subject in ["学生", "参与者", "教师", "家长", "学校"]:
            if subject in text:
                return subject
        return None

    @staticmethod
    def _infer_predicate(text: str) -> str | None:
        for term in SUPPORT_TERMS + OPPOSE_TERMS + CONCERN_TERMS + UNCERTAIN_TERMS:
            if term in text:
                return term
        return None

    def _infer_object(self, text: str) -> str | None:
        predicate = self._infer_predicate(text)
        if not predicate or predicate not in text:
            return None
        return text.split(predicate, 1)[1].strip(" ，,。") or None

    @staticmethod
    def _infer_condition(text: str) -> str | None:
        for marker in CONDITION_MARKERS:
            if marker in text:
                if marker == "条件下":
                    match = re.search(r"在(.{1,40}?条件下)", text)
                    return match.group(0) if match else marker
                return text[text.index(marker) :].strip(" ，,。")
        return None

    @staticmethod
    def _importance(text: str) -> float:
        if any(term in text for term in ["主要", "最大", "核心", "所有", "一致", "绝大多数"]):
            return 0.9
        if any(term in text for term in ["多数", "普遍", "强烈", "明显"]):
            return 0.8
        return 0.6


class ClaimExtractor:
    """Extract atomic claims through the configured provider."""

    def __init__(self, provider: LLMProvider | None = None) -> None:
        self.provider = provider

    def extract(self, summary: str) -> list[AtomicClaim]:
        if self.provider is None:
            return RuleBasedClaimParser().extract(summary)

        claims = self.provider.extract_claims(summary)
        if not isinstance(claims, list):
            raise TypeError("Provider extract_claims must return a list.")
        if not all(isinstance(claim, AtomicClaim) for claim in claims):
            raise TypeError("Provider returned non-AtomicClaim items.")
        if not claims and summary.strip():
            raise ValueError("Provider returned no claims for a non-empty summary.")
        return claims
