"""Faithful revision generation from verified audit materials."""

from __future__ import annotations

from mandate.schemas import (
    AuditPassport,
    CoverageStatus,
    RevisionResult,
    SupportStatus,
)


class RevisionGenerator:
    """Generate a conservative revised summary from verified evidence only."""

    def generate(self, passport: AuditPassport, original_summary: str) -> RevisionResult:
        trace = passport.source_trace_result
        omission = passport.omission_result
        removed_claims: list[str] = []
        modified_claims: list[str] = []
        restored_clusters: list[str] = []
        citations: dict[str, list[str]] = {}
        paragraphs: list[str] = []

        disclosures = list(dict.fromkeys(passport.required_disclosures + [
            f"以下结果基于{passport.source_count}条匿名意见，并由AI辅助整理。",
            "该结果仅反映当前探索性样本，不代表全体学生立场。",
        ]))

        if trace is not None:
            for bundle in trace.evidence_bundles:
                if bundle.final_support_status == SupportStatus.UNSUPPORTED:
                    removed_claims.append(bundle.claim.claim_id)
                elif bundle.final_support_status in {
                    SupportStatus.PARTIALLY_SUPPORTED,
                    SupportStatus.INFERRED,
                    SupportStatus.CONTRADICTED,
                }:
                    modified_claims.append(bundle.claim.claim_id)

        if omission is not None:
            for assessment in omission.coverage_assessments:
                cluster = next(
                    item for item in omission.clusters if item.cluster_id == assessment.cluster_id
                )
                if assessment.status == CoverageStatus.COVERED:
                    paragraphs.append(self._covered_sentence(cluster.label, cluster.unique_participant_count))
                    citations[cluster.cluster_id] = cluster.source_ids
                elif assessment.status in {CoverageStatus.WEAKENED, CoverageStatus.DISTORTED}:
                    paragraphs.append(self._qualified_sentence(cluster.label, cluster.representative_quotes))
                    modified_claims.extend(assessment.matched_claim_ids)
                    citations[cluster.cluster_id] = cluster.source_ids
                elif (
                    assessment.status == CoverageStatus.OMITTED
                    and (cluster.is_normatively_salient or cluster.is_procedural)
                ):
                    paragraphs.append(self._restored_sentence(cluster.label, cluster.representative_quotes))
                    restored_clusters.append(cluster.cluster_id)
                    citations[cluster.cluster_id] = cluster.source_ids

        if not paragraphs:
            paragraphs.append("本次材料不足以生成忠实的群体意见总结。")

        revised = " ".join(disclosures + paragraphs)
        unresolved = []
        if passport.unsupported_claim_ids:
            unresolved.append("Original summary contains unsupported claims that were removed or downgraded.")
        if passport.omitted_salient_clusters:
            unresolved.append("Original summary omitted normatively salient topics.")
        return RevisionResult(
            original_summary=original_summary,
            revised_summary=revised,
            removed_claims=list(dict.fromkeys(removed_claims)),
            modified_claims=list(dict.fromkeys(modified_claims)),
            restored_clusters=list(dict.fromkeys(restored_clusters)),
            added_disclosures=disclosures,
            source_citations=citations,
            unresolved_issues=unresolved,
            human_review_required=True,
        )

    def suggest(self, passport: AuditPassport) -> list[str]:
        suggestions: list[str] = []
        if passport.unsupported_claim_ids:
            suggestions.append("Delete or downgrade unsupported claims.")
        if passport.quantifier_warnings:
            suggestions.append("Correct overstated quantifiers.")
        if passport.procedural_clusters_omitted:
            suggestions.append("Restore omitted procedural safeguards.")
        if passport.required_actions:
            suggestions.extend(passport.required_actions)
        return suggestions

    @staticmethod
    def _covered_sentence(label: str, count: int) -> str:
        return f"当前材料中有{count}名参与者表达了与“{label}”相关的意见。"

    @staticmethod
    def _qualified_sentence(label: str, quotes: list[str]) -> str:
        quote = quotes[0] if quotes else label
        return f"关于“{label}”，应保留限定条件和原始强度，例如：{quote}"

    @staticmethod
    def _restored_sentence(label: str, quotes: list[str]) -> str:
        quote = quotes[0] if quotes else label
        return f"原始材料还包含“{label}”这一重要声音，例如：{quote}"
