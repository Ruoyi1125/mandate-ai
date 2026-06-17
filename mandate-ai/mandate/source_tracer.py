"""Source tracing with TF-IDF retrieval and rule-based support classification."""

from __future__ import annotations

from abc import ABC, abstractmethod
import math
from collections import Counter

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
except ModuleNotFoundError:  # pragma: no cover - exercised only without optional deps
    TfidfVectorizer = None  # type: ignore[assignment]
    cosine_similarity = None  # type: ignore[assignment]

from mandate.quantifier_checker import QuantifierChecker
from mandate.schemas import (
    AtomicClaim,
    ClaimEvidenceBundle,
    EvidenceMatch,
    SourceRecord,
    SourceTraceResult,
    SupportStatus,
)
from mandate.support_classifier import SupportClassifier


class EmbeddingRetriever(ABC):
    """Optional future interface for embedding-based retrieval."""

    @abstractmethod
    def retrieve(
        self, claim: AtomicClaim, sources: list[SourceRecord], top_k: int
    ) -> list[tuple[SourceRecord, float]]:
        """Return sources and semantic similarity scores."""


class TfidfRetriever:
    """Local TF-IDF retriever used by default."""

    def retrieve(
        self, claim: AtomicClaim, sources: list[SourceRecord], top_k: int
    ) -> list[tuple[SourceRecord, float]]:
        if not sources:
            return []
        if TfidfVectorizer is None or cosine_similarity is None:
            return self._fallback_retrieve(claim, sources, top_k)
        documents = [source.text for source in sources]
        vectorizer = TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 4))
        matrix = vectorizer.fit_transform(documents + [claim.text])
        scores = cosine_similarity(matrix[-1], matrix[:-1]).flatten()
        ranked = sorted(
            zip(sources, scores, strict=True),
            key=lambda item: item[1],
            reverse=True,
        )
        return [(source, float(score)) for source, score in ranked[:top_k]]

    def _fallback_retrieve(
        self, claim: AtomicClaim, sources: list[SourceRecord], top_k: int
    ) -> list[tuple[SourceRecord, float]]:
        claim_vector = self._char_vector(claim.text)
        ranked = [
            (source, self._cosine(claim_vector, self._char_vector(source.text)))
            for source in sources
        ]
        ranked.sort(key=lambda item: item[1], reverse=True)
        return ranked[:top_k]

    @staticmethod
    def _char_vector(text: str) -> Counter[str]:
        chars = [char for char in text if not char.isspace()]
        grams = chars + ["".join(chars[index : index + 2]) for index in range(len(chars) - 1)]
        return Counter(grams)

    @staticmethod
    def _cosine(left: Counter[str], right: Counter[str]) -> float:
        if not left or not right:
            return 0.0
        dot = sum(left[key] * right.get(key, 0) for key in left)
        left_norm = math.sqrt(sum(value * value for value in left.values()))
        right_norm = math.sqrt(sum(value * value for value in right.values()))
        if left_norm == 0.0 or right_norm == 0.0:
            return 0.0
        return dot / (left_norm * right_norm)


class SourceTracer:
    """Trace claims to candidate evidence and produce evidence bundles."""

    def __init__(
        self,
        retriever: EmbeddingRetriever | TfidfRetriever | None = None,
        support_classifier: SupportClassifier | None = None,
        quantifier_checker: QuantifierChecker | None = None,
        top_k: int = 5,
    ) -> None:
        self.retriever = retriever or TfidfRetriever()
        self.support_classifier = support_classifier or SupportClassifier()
        self.quantifier_checker = quantifier_checker or QuantifierChecker()
        self.top_k = top_k

    def trace(
        self, claims: list[AtomicClaim], sources: list[SourceRecord]
    ) -> list[EvidenceMatch]:
        """Compatibility helper returning flattened candidate matches."""

        result = self.trace_result(claims, sources)
        return [
            match
            for bundle in result.evidence_bundles
            for match in bundle.candidate_matches
        ]

    def trace_result(
        self, claims: list[AtomicClaim], sources: list[SourceRecord]
    ) -> SourceTraceResult:
        warnings = self._input_warnings(sources)
        bundles: list[ClaimEvidenceBundle] = []
        unsupported_ids: list[str] = []
        contradicted_ids: list[str] = []
        partial_ids: list[str] = []

        for claim in claims:
            candidates = self.retriever.retrieve(claim, sources, self.top_k)
            matches = [
                self.support_classifier.classify(
                    claim=claim,
                    source=source,
                    similarity_score=score,
                    rank=index + 1,
                )
                for index, (source, score) in enumerate(candidates)
            ]
            assessment = self.quantifier_checker.assess(claim, sources, matches)
            final_status = self._final_status(matches)
            bundle_warnings = self._bundle_warnings(claim, matches, assessment)

            if final_status == SupportStatus.UNSUPPORTED:
                unsupported_ids.append(claim.claim_id)
            elif final_status == SupportStatus.CONTRADICTED:
                contradicted_ids.append(claim.claim_id)
            elif final_status == SupportStatus.PARTIALLY_SUPPORTED:
                partial_ids.append(claim.claim_id)

            bundles.append(
                ClaimEvidenceBundle(
                    claim=claim,
                    candidate_matches=matches,
                    best_supporting_matches=[
                        match
                        for match in matches
                        if match.support_status
                        in {SupportStatus.DIRECTLY_SUPPORTED, SupportStatus.PARTIALLY_SUPPORTED}
                    ][:3],
                    contradicting_matches=[
                        match
                        for match in matches
                        if match.support_status == SupportStatus.CONTRADICTED
                    ],
                    final_support_status=final_status,
                    quantifier_assessment=assessment,
                    warnings=bundle_warnings,
                )
            )

        return SourceTraceResult(
            claims=claims,
            evidence_bundles=bundles,
            unsupported_claim_ids=unsupported_ids,
            contradicted_claim_ids=contradicted_ids,
            partially_supported_claim_ids=partial_ids,
            warnings=warnings,
        )

    @staticmethod
    def _final_status(matches: list[EvidenceMatch]) -> SupportStatus:
        statuses = [match.support_status for match in matches]
        if SupportStatus.CONTRADICTED in statuses:
            if any(
                status in {SupportStatus.DIRECTLY_SUPPORTED, SupportStatus.PARTIALLY_SUPPORTED}
                for status in statuses
            ):
                return SupportStatus.PARTIALLY_SUPPORTED
            return SupportStatus.CONTRADICTED
        if SupportStatus.DIRECTLY_SUPPORTED in statuses:
            return SupportStatus.DIRECTLY_SUPPORTED
        if SupportStatus.PARTIALLY_SUPPORTED in statuses:
            return SupportStatus.PARTIALLY_SUPPORTED
        if SupportStatus.INFERRED in statuses:
            return SupportStatus.INFERRED
        return SupportStatus.UNSUPPORTED

    @staticmethod
    def _input_warnings(sources: list[SourceRecord]) -> list[str]:
        warnings: list[str] = []
        if len(sources) < 3:
            warnings.append("Source sample is smaller than 3 records; quantifier findings are fragile.")
        ids = [source.source_id for source in sources]
        if len(ids) != len(set(ids)):
            warnings.append("Duplicate source_id values detected.")
        missing_participants = [source for source in sources if not source.participant_id]
        if missing_participants:
            warnings.append("Some records lack participant_id; source_id is used for participant counting.")
        return warnings

    @staticmethod
    def _bundle_warnings(
        claim: AtomicClaim,
        matches: list[EvidenceMatch],
        assessment: object,
    ) -> list[str]:
        warnings: list[str] = []
        if not matches or all(match.support_status == SupportStatus.UNSUPPORTED for match in matches):
            warnings.append("No source currently supports this claim.")
        relevant_matches = [
            match
            for match in matches
            if match.support_status != SupportStatus.UNSUPPORTED
        ]
        if any(match.condition_preserved is False for match in relevant_matches):
            warnings.append("A condition present in source material may have been removed.")
        if any(match.quantifier_supported is False for match in relevant_matches):
            warnings.append("The claim may overstate quantity, scope, or degree.")
        if any(match.support_status == SupportStatus.CONTRADICTED for match in matches):
            warnings.append("Contradicting source material is present.")
        if getattr(assessment, "supported", True) is False and claim.quantifier:
            warnings.append(getattr(assessment, "explanation", "Quantifier is not supported."))
        return list(dict.fromkeys(warnings))
