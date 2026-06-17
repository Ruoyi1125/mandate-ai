"""Audit passport assembly and export."""

from __future__ import annotations

from mandate.schemas import (
    AuditPassport,
    AtomicClaim,
    AuthorizationAssessment,
    AuthorizationStatus,
    EvidenceMatch,
    FinalStatus,
    OmissionResult,
    OpinionCluster,
    RepresentationMode,
    SourceTraceResult,
    SupportStatus,
)


class PassportGenerator:
    """Build the structured representation passport."""

    def generate(
        self,
        representation_mode: RepresentationMode,
        source_count: int,
        claims: list[AtomicClaim],
        evidence_matches: list[EvidenceMatch],
        clusters: list[OpinionCluster],
        omitted_clusters: list[OpinionCluster],
        authorization: AuthorizationAssessment,
        source_trace_result: SourceTraceResult | None = None,
        omission_result: OmissionResult | None = None,
        pending_modules: list[str] | None = None,
    ) -> AuditPassport:
        unsupported = source_trace_result.unsupported_claim_ids if source_trace_result else []
        contradicted = source_trace_result.contradicted_claim_ids if source_trace_result else []
        partial = source_trace_result.partially_supported_claim_ids if source_trace_result else []
        quantifier_warnings = self._quantifier_warnings(source_trace_result)
        traceable_claim_ids = {
            match.claim_id
            for match in evidence_matches
            if match.support_status
            in {SupportStatus.DIRECTLY_SUPPORTED, SupportStatus.PARTIALLY_SUPPORTED, SupportStatus.INFERRED}
        }
        minority_total = len([cluster for cluster in clusters if cluster.is_minority])
        minority_retained = (
            omission_result.minority_retention_numerator
            if omission_result is not None
            else minority_total
        )
        final_status = self._final_status(
            representation_mode=representation_mode,
            authorization=authorization,
            unsupported_claims=unsupported,
            contradicted_claims=contradicted,
            omission_result=omission_result,
        )
        return AuditPassport(
            representation_mode=representation_mode,
            source_count=source_count,
            claim_count=len(claims),
            traceable_claim_count=len(traceable_claim_ids),
            unsupported_claims=unsupported,
            unsupported_claim_ids=unsupported,
            contradicted_claim_ids=contradicted,
            partially_supported_claim_ids=partial,
            quantifier_warnings=quantifier_warnings,
            cluster_count=len(clusters),
            represented_clusters=[cluster.cluster_id for cluster in clusters],
            covered_clusters=omission_result.covered_cluster_ids if omission_result else [],
            weakened_clusters=omission_result.weakened_cluster_ids if omission_result else [],
            distorted_clusters=omission_result.distorted_cluster_ids if omission_result else [],
            omitted_clusters=omission_result.omitted_cluster_ids if omission_result else [cluster.cluster_id for cluster in omitted_clusters],
            minority_clusters_total=minority_total,
            minority_clusters_retained=minority_retained,
            omitted_salient_clusters=omission_result.omitted_salient_cluster_ids if omission_result else [],
            procedural_clusters_total=(
                len(omission_result.procedural_cluster_ids) if omission_result else 0
            ),
            procedural_clusters_omitted=(
                omission_result.procedural_clusters_omitted if omission_result else []
            ),
            condition_preservation_count=(
                f"{omission_result.condition_preservation_numerator}/"
                f"{omission_result.condition_preservation_denominator}"
                if omission_result else "0/0"
            ),
            authorization_status=authorization.authorization_status,
            permitted_use=authorization.permitted_use,
            prohibited_use=authorization.prohibited_use,
            missing_authorization_information=authorization.missing_information,
            required_actions=authorization.required_actions,
            required_disclosures=authorization.required_disclosures,
            triggered_rule_ids=authorization.rule_ids_triggered,
            final_status=final_status,
            source_trace_result=source_trace_result,
            omission_result=omission_result,
            authorization_assessment=authorization,
            pending_modules=pending_modules or [],
        )

    @staticmethod
    def _quantifier_warnings(source_trace_result: SourceTraceResult | None) -> list[str]:
        if source_trace_result is None:
            return []
        warnings: list[str] = []
        for bundle in source_trace_result.evidence_bundles:
            assessment = bundle.quantifier_assessment
            if assessment is not None and not assessment.supported and assessment.quantifier:
                warnings.append(f"{bundle.claim.claim_id}: {assessment.explanation}")
        return warnings

    @staticmethod
    def _final_status(
        representation_mode: RepresentationMode,
        authorization: AuthorizationAssessment,
        unsupported_claims: list[str],
        contradicted_claims: list[str],
        omission_result: OmissionResult | None,
    ) -> FinalStatus:
        if representation_mode == RepresentationMode.SYNTHETIC_GROUP:
            return FinalStatus.SYNTHETIC_ONLY
        if authorization.authorization_status == AuthorizationStatus.PROHIBITED:
            return FinalStatus.PROHIBITED
        if authorization.authorization_status in {
            AuthorizationStatus.REAUTHORIZE,
            AuthorizationStatus.REAUTHORIZE_REQUIRED,
            AuthorizationStatus.UNKNOWN,
        }:
            return FinalStatus.REAUTHORIZE
        if contradicted_claims or unsupported_claims:
            return FinalStatus.CONDITIONAL
        if omission_result and (
            omission_result.omitted_salient_cluster_ids
            or omission_result.procedural_clusters_omitted
            or omission_result.weakened_cluster_ids
            or omission_result.distorted_cluster_ids
        ):
            return FinalStatus.CONDITIONAL
        if authorization.required_actions or authorization.required_disclosures:
            return FinalStatus.CONDITIONAL
        return FinalStatus.ALLOWED


class PassportExporter:
    """Export representation passports as JSON, Markdown, or HTML."""

    def to_json(self, passport: AuditPassport) -> str:
        return passport.model_dump_json(indent=2)

    def to_markdown(self, passport: AuditPassport) -> str:
        lines = [
            "# MANDATE",
            "## REPRESENTATION PASSPORT",
            "",
            f"表达类型：{passport.representation_mode.value}",
            f"原始材料：{passport.source_count}条",
            f"可追溯主张：{passport.traceable_claim_count}/{passport.claim_count}",
            f"意见主题：{passport.cluster_count}",
            f"忠实覆盖：{len(passport.covered_clusters)}/{passport.cluster_count}",
            f"被弱化：{len(passport.weakened_clusters)}",
            f"被扭曲：{len(passport.distorted_clusters)}",
            f"被遗漏：{len(passport.omitted_clusters)}",
            f"少数主题保留：{passport.minority_clusters_retained}/{passport.minority_clusters_total}",
            f"程序性主题保留：{passport.procedural_clusters_total - len(passport.procedural_clusters_omitted)}/{passport.procedural_clusters_total}",
            "",
            f"授权状态：{passport.authorization_status.value}",
            f"允许使用：{'是' if passport.permitted_use else '否'}",
            f"最终状态：{passport.final_status.value}",
            "",
            "### 提交前必须",
        ]
        actions = passport.required_actions or ["No required actions recorded."]
        lines.extend(f"{index}. {action}" for index, action in enumerate(actions, start=1))
        if passport.required_disclosures:
            lines.append("")
            lines.append("### 必要披露")
            lines.extend(f"- {item}" for item in passport.required_disclosures)
        return "\n".join(lines)

    def to_html(self, passport: AuditPassport) -> str:
        markdown = self.to_markdown(passport)
        items = "".join(f"<p>{line}</p>" for line in markdown.splitlines() if line)
        return f"<!doctype html><html><body>{items}</body></html>"
