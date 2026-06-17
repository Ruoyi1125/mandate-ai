"""Source tracing placeholder with deterministic lexical matching."""

from __future__ import annotations

from mandate.schemas import AtomicClaim, EvidenceMatch, SourceRecord, SupportStatus


class SourceTracer:
    """Trace claims to source records using a simple token overlap heuristic."""

    def trace(
        self, claims: list[AtomicClaim], sources: list[SourceRecord]
    ) -> list[EvidenceMatch]:
        matches: list[EvidenceMatch] = []
        for claim in claims:
            best_source: SourceRecord | None = None
            best_score = 0.0
            for source in sources:
                score = self._overlap_score(claim.text, source.text)
                if score > best_score:
                    best_score = score
                    best_source = source
            if best_source is None:
                continue
            status = (
                SupportStatus.PARTIALLY_SUPPORTED
                if best_score >= 0.2
                else SupportStatus.UNSUPPORTED
            )
            matches.append(
                EvidenceMatch(
                    claim_id=claim.claim_id,
                    source_id=best_source.source_id,
                    similarity_score=round(best_score, 3),
                    support_status=status,
                    explanation="Mock lexical overlap evidence trace.",
                )
            )
        return matches

    @staticmethod
    def _overlap_score(left: str, right: str) -> float:
        left_tokens = set(left.lower().split())
        right_tokens = set(right.lower().split())
        if not left_tokens or not right_tokens:
            return 0.0
        return len(left_tokens & right_tokens) / len(left_tokens | right_tokens)
