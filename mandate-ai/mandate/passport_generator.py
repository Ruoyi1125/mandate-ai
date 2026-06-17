"""Audit passport assembly."""

from __future__ import annotations

from mandate.schemas import (
    AuditPassport,
    AtomicClaim,
    AuthorizationResult,
    AuthorizationStatus,
    EvidenceMatch,
    FinalStatus,
    OpinionCluster,
    RepresentationMode,
    SupportStatus,
)


class PassportGenerator:
    """Build the final structured audit passport."""

    def generate(
        self,
        representation_mode: RepresentationMode,
        source_count: int,
        claims: list[AtomicClaim],
        evidence_matches: list[EvidenceMatch],
        clusters: list[OpinionCluster],
        omitted_clusters: list[OpinionCluster],
        authorization: AuthorizationResult,
    ) -> AuditPassport:
        unsupported_claims = [
            match.claim_id
            for match in evidence_matches
            if match.support_status
            in {SupportStatus.UNSUPPORTED, SupportStatus.CONTRADICTED}
        ]
        traceable_claim_ids = {
            match.claim_id
            for match in evidence_matches
            if match.support_status
            in {SupportStatus.DIRECTLY_SUPPORTED, SupportStatus.PARTIALLY_SUPPORTED}
        }
        minority_clusters = [cluster for cluster in clusters if cluster.is_minority]
        final_status = self._final_status(
            representation_mode=representation_mode,
            authorization=authorization,
            unsupported_claims=unsupported_claims,
            omitted_clusters=omitted_clusters,
        )
        return AuditPassport(
            representation_mode=representation_mode,
            source_count=source_count,
            claim_count=len(claims),
            traceable_claim_count=len(traceable_claim_ids),
            unsupported_claims=unsupported_claims,
            cluster_count=len(clusters),
            represented_clusters=[cluster.cluster_id for cluster in clusters],
            omitted_clusters=[cluster.cluster_id for cluster in omitted_clusters],
            minority_clusters_total=len(minority_clusters),
            minority_clusters_retained=len(minority_clusters) - len(omitted_clusters),
            authorization_status=authorization.status,
            permitted_use=authorization.permitted_use,
            required_actions=authorization.required_actions,
            required_disclosures=authorization.required_disclosures,
            final_status=final_status,
        )

    @staticmethod
    def _final_status(
        representation_mode: RepresentationMode,
        authorization: AuthorizationResult,
        unsupported_claims: list[str],
        omitted_clusters: list[OpinionCluster],
    ) -> FinalStatus:
        if representation_mode == RepresentationMode.SYNTHETIC_GROUP:
            return FinalStatus.SYNTHETIC_ONLY
        if authorization.status == AuthorizationStatus.REAUTHORIZE_REQUIRED:
            return FinalStatus.REAUTHORIZE
        if authorization.status == AuthorizationStatus.PROHIBITED:
            return FinalStatus.PROHIBITED
        if unsupported_claims or omitted_clusters or authorization.required_actions:
            return FinalStatus.CONDITIONAL
        return FinalStatus.ALLOWED
