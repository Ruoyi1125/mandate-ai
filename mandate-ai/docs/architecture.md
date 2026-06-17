# Architecture

MANDATE is organized as a small pipeline with replaceable components. Phase one focuses on data contracts and orchestration rather than model quality.

## Data Flow

1. `app.py` collects a project name, representation mode, source opinions, AI summary, and simplified authorization information.
2. `schemas.py` validates the request as an `AuditRequest`.
3. `pipeline.py` orchestrates claim extraction, source tracing, opinion clustering, omission detection, authorization evaluation, and passport generation.
4. `providers/mock_provider.py` returns deterministic `AtomicClaim` objects without any API key or network call.
5. `authorization_engine.py` reads `rules/authorization_rules.yaml` and combines default policy rules with the submitted `AuthorizationProfile`.
6. `passport_generator.py` produces an `AuditPassport`.

## Module Responsibilities

- `config.py`: environment-based settings, including the rule file path.
- `schemas.py`: canonical Pydantic v2 data structures and validation.
- `providers/base.py`: provider interface for future LLM integrations.
- `providers/mock_provider.py`: deterministic local provider for tests and demos.
- `claim_extractor.py`: boundary for claim extraction.
- `source_tracer.py`: placeholder evidence matching interface.
- `opinion_clusterer.py`: placeholder clustering interface.
- `omission_detector.py`: placeholder omitted-minority detection interface.
- `authorization_engine.py`: structured authorization decision logic.
- `passport_generator.py`: final `AuditPassport` assembly.
- `revision_generator.py`: placeholder revision suggestions.
- `pipeline.py`: end-to-end workflow orchestration.

## Extension Points

Future phases can replace the mock implementations while preserving schema contracts:

- Swap `MockProvider` for a real provider implementing `LLMProvider`.
- Replace lexical source tracing with embedding retrieval.
- Replace the single mock cluster with scikit-learn or sentence-transformer clustering.
- Add export adapters for PDF, JSON-LD, or signed credentials.
