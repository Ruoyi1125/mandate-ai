"""Orchestration for the phase-one audit workflow."""

from __future__ import annotations

from pathlib import Path

from mandate.authorization_engine import AuthorizationEngine
from mandate.claim_extractor import ClaimExtractor
from mandate.omission_detector import OmissionDetector
from mandate.opinion_clusterer import OpinionClusterer
from mandate.passport_generator import PassportGenerator
from mandate.providers.base import LLMProvider
from mandate.schemas import AuditPassport, AuditRequest
from mandate.source_tracer import SourceTracer


class AuditPipeline:
    """Run the audit workflow with replaceable components."""

    def __init__(self, provider: LLMProvider, rules_path: Path | str) -> None:
        self.claim_extractor = ClaimExtractor(provider)
        self.source_tracer = SourceTracer()
        self.clusterer = OpinionClusterer()
        self.omission_detector = OmissionDetector()
        self.authorization_engine = AuthorizationEngine(rules_path)
        self.passport_generator = PassportGenerator()

    def run(self, request: AuditRequest) -> AuditPassport:
        claims = self.claim_extractor.extract(request.ai_generated_summary)
        evidence_matches = self.source_tracer.trace(claims, request.source_records)
        clusters = self.clusterer.cluster(request.source_records)
        omitted_clusters = self.omission_detector.detect(
            clusters, request.ai_generated_summary
        )
        authorization = self.authorization_engine.evaluate(request)
        return self.passport_generator.generate(
            representation_mode=request.representation_mode,
            source_count=len(request.source_records),
            claims=claims,
            evidence_matches=evidence_matches,
            clusters=clusters,
            omitted_clusters=omitted_clusters,
            authorization=authorization,
        )
