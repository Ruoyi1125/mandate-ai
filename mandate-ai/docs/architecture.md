# Architecture

MANDATE is organized as a small pipeline with replaceable components. The current phase focuses on `REAL_GROUP` source tracing plus opinion omission detection, while export and advanced authorization remain out of scope.

## Data Flow

1. `app.py` collects source opinions, optional CSV input, AI summary, and simplified authorization information.
2. `schemas.py` validates the request as an `AuditRequest`.
3. `pipeline.py` validates non-empty source tracing inputs.
4. `claim_extractor.py` decomposes the AI summary into `AtomicClaim` objects through `MockProvider` and local rules.
5. `source_tracer.py` retrieves Top 5 candidate sources for each claim.
6. `support_classifier.py` labels candidate evidence as directly supported, partially supported, inferred, unsupported, or contradicted.
7. `quantifier_checker.py` checks whether quantifiers and degree terms are warranted within the uploaded materials.
8. `authorization_engine.py` reads `rules/authorization_rules.yaml` and evaluates current use against the submitted `AuthorizationProfile`.
9. `opinion_extractor.py` splits original source records into `OpinionUnit` objects.
10. `opinion_clusterer.py` groups opinion units into topic clusters with stance, intensity, minority, and salience metadata.
11. `omission_detector.py` compares original clusters against summary claims and produces an `OmissionResult`.
12. `authorization_engine.py` evaluates declared authorization against the current use.
13. `passport_generator.py` produces an `AuditPassport` with nested `SourceTraceResult`, `OmissionResult`, and `AuthorizationAssessment`.
14. `revision_generator.py` produces a conservative faithful revision.

## Module Responsibilities

- `config.py`: environment-based settings, including the rule file path.
- `schemas.py`: canonical Pydantic v2 data structures and validation.
- `input_loader.py`: line-based and CSV source parsing.
- `providers/base.py`: provider interface for future LLM integrations.
- `providers/mock_provider.py`: deterministic local provider for tests and demos.
- `claim_extractor.py`: rule-based atomic claim extraction and provider output validation.
- `source_tracer.py`: TF-IDF candidate retrieval, evidence bundle assembly, and future `EmbeddingRetriever` interface.
- `support_classifier.py`: rule-based support relation classification.
- `quantifier_checker.py`: quantifier and degree-word assessment using unique participant counts.
- `opinion_extractor.py`: rule-based extraction of independent opinion units from original sources.
- `opinion_clusterer.py`: topic aggregation, participant de-duplication, minority checks, and normative salience tagging.
- `omission_detector.py`: coverage classification for original clusters: covered, weakened, distorted, or omitted.
- `authorization_engine.py`: structured authorization decision logic.
- `passport_generator.py`: final `AuditPassport` assembly plus JSON, Markdown, and HTML export.
- `revision_generator.py`: conservative template-based revision.
- `pipeline.py`: end-to-end workflow orchestration.

## Extension Points

- Swap `MockProvider` for a real provider implementing `LLMProvider`.
- Replace lexical source tracing with an `EmbeddingRetriever`.
- Reuse `SourceTraceResult.evidence_bundles` and `OmissionResult.coverage_assessments` for future credential generation.
- Add export adapters for PDF, JSON-LD, or signed credentials.

## Independent Outputs

The system does not compute a single representativeness score. It reports separate counts and ratios such as topic coverage, minority retention, procedural issue retention, and condition preservation, each with numerator and denominator.
