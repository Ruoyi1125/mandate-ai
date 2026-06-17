"""Orchestration for the phase-one audit workflow."""

from __future__ import annotations

from pathlib import Path

from mandate.authorization_engine import AuthorizationEngine
from mandate.claim_extractor import ClaimExtractor
from mandate.omission_detector import OmissionDetector
from mandate.opinion_clusterer import OpinionClusterer
from mandate.opinion_extractor import OpinionExtractor
from mandate.passport_generator import PassportGenerator
from mandate.providers.base import LLMProvider
from mandate.quantifier_checker import QuantifierChecker
from mandate.revision_generator import RevisionGenerator
from mandate.schemas import AuditPassport, AuditRequest
from mandate.source_tracer import SourceTracer


class AuditPipeline:
    """Run the audit workflow with replaceable components."""

    def __init__(self, provider: LLMProvider, rules_path: Path | str) -> None:
        self.claim_extractor = ClaimExtractor(provider)
        self.source_tracer = SourceTracer(quantifier_checker=QuantifierChecker(rules_path))
        self.opinion_extractor = OpinionExtractor()
        self.opinion_clusterer = OpinionClusterer(rules_path)
        self.omission_detector = OmissionDetector(rules_path)
        self.authorization_engine = AuthorizationEngine(rules_path)
        self.passport_generator = PassportGenerator()
        self.revision_generator = RevisionGenerator()

    def run(self, request: AuditRequest) -> AuditPassport:
        if not request.ai_generated_summary.strip():
            raise ValueError("AI generated summary must not be empty.")
        if not request.source_records:
            raise ValueError("At least one source record is required for source tracing.")

        claims = self.claim_extractor.extract(request.ai_generated_summary)
        source_trace_result = self.source_tracer.trace_result(claims, request.source_records)
        opinion_units = self.opinion_extractor.extract(request.source_records)
        participant_total = len(
            {source.participant_id or source.source_id for source in request.source_records}
        )
        clusters = self.opinion_clusterer.cluster(
            opinion_units,
            total_participant_count=participant_total,
        )
        omission_result = self.omission_detector.detect(
            clusters=clusters,
            summary=request.ai_generated_summary,
            source_trace_result=source_trace_result,
            opinion_units=opinion_units,
        )
        if len(request.ai_generated_summary.strip()) < 20:
            omission_result.warnings.append("AI summary is very short and may not cover major themes.")
        if len(claims) > 8 and len(source_trace_result.unsupported_claim_ids) >= 3:
            omission_result.warnings.append("AI summary appears long and includes multiple unsupported claims.")
        if len(clusters) > self.opinion_clusterer.maximum_recommended_clusters:
            omission_result.warnings.append(
                "Cluster count exceeds the recommended range; review topic fragmentation."
            )
        evidence_matches = [
            match
            for bundle in source_trace_result.evidence_bundles
            for match in bundle.candidate_matches
        ]
        authorization = self.authorization_engine.evaluate(request)
        passport = self.passport_generator.generate(
            representation_mode=request.representation_mode,
            source_count=len(request.source_records),
            claims=claims,
            evidence_matches=evidence_matches,
            clusters=clusters,
            omitted_clusters=[],
            authorization=authorization,
            source_trace_result=source_trace_result,
            omission_result=omission_result,
            pending_modules=[],
        )
        passport.revision_result = self.revision_generator.generate(
            passport,
            request.ai_generated_summary,
        )
        return passport
