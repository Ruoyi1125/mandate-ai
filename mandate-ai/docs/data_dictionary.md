# Data Dictionary

## SourceRecord

- `source_id`: Unique source record identifier.
- `participant_id`: Optional participant identifier; may be anonymous. Multiple records with the same value count as one participant for quantifier checks.
- `text`: Original opinion or testimony text.
- `metadata`: Additional structured metadata.
- `consent_id`: Optional consent or authorization record identifier.

## AtomicClaim

- `claim_id`: Unique claim identifier.
- `text`: Minimal checkable claim text.
- `quantifier`: Optional quantity or degree marker such as `部分`, `多数`, `普遍`, `主要`, or `最大`.
- `stance`: Optional position label such as `support`, `oppose`, `concern`, `uncertain`, or `neutral`.
- `importance`: Claim importance from `0.0` to `1.0`.
- `subject`: Inferred claim subject.
- `predicate`: Inferred relation or attitude term.
- `object`: Inferred object or topic.
- `condition`: Optional condition that qualifies the claim.
- `certainty`: Optional certainty marker.

## EvidenceMatch

- `claim_id`: Claim being checked.
- `source_id`: Source record used as evidence.
- `similarity_score`: Lexical or semantic relatedness from `0.0` to `1.0`; this is not a truth score.
- `support_status`: One of `DIRECTLY_SUPPORTED`, `PARTIALLY_SUPPORTED`, `INFERRED`, `UNSUPPORTED`, `CONTRADICTED`.
- `explanation`: Human-readable reason for the match.
- `matched_text`: Source text segment currently matched; this phase uses the full source text.
- `source_text`: Original source text for display.
- `rank`: Candidate rank from retrieval.
- `condition_preserved`: Whether a condition in source material is preserved in the claim.
- `stance_aligned`: Whether claim and source stance align.
- `quantifier_supported`: Whether the candidate supports the claim's quantifier or degree.
- `confidence`: Classifier confidence in its own label; this is not claim truth.

## QuantifierAssessment

- `claim_id`: Claim being assessed.
- `quantifier`: Quantity or degree expression being checked.
- `supported`: Whether the uploaded materials support the expression.
- `supporting_participant_count`: Unique participants with supporting evidence.
- `opposing_participant_count`: Unique participants with contradicting evidence.
- `total_participant_count`: Unique participants in the uploaded materials.
- `observed_ratio`: Supporting ratio within uploaded materials only.
- `explanation`: Plain-language assessment.

## ClaimEvidenceBundle

- `claim`: The `AtomicClaim`.
- `candidate_matches`: Top candidate evidence matches.
- `best_supporting_matches`: Supporting or partially supporting matches selected for display.
- `contradicting_matches`: Matches that contradict the claim.
- `final_support_status`: Claim-level support status after reviewing candidates.
- `quantifier_assessment`: Optional quantifier assessment.
- `warnings`: Risk notices for the claim.

## SourceTraceResult

- `claims`: Extracted atomic claims.
- `evidence_bundles`: Evidence bundle for each claim.
- `unsupported_claim_ids`: Claims with no supporting source.
- `contradicted_claim_ids`: Claims contradicted by source material.
- `partially_supported_claim_ids`: Claims needing qualification.
- `warnings`: Input-level warnings such as small samples or duplicate IDs.

## OpinionUnit

- `opinion_id`: Unique opinion-unit identifier.
- `source_id`: Source record from which the opinion was extracted.
- `participant_id`: Optional participant identifier.
- `text`: Text fragment for the opinion.
- `topic`: Inferred topic label.
- `stance`: One of `SUPPORT`, `CONDITIONAL_SUPPORT`, `OPPOSE`, `NEUTRAL`, `UNCERTAIN`, `MIXED`.
- `intensity`: One of `LOW`, `MEDIUM`, `HIGH`.
- `condition`: Optional condition attached to the opinion.
- `target`: Optional target of the opinion.
- `is_procedural`: Whether the opinion asks for procedural safeguards such as appeal, explanation, exit, review, deletion, or correction.
- `metadata`: Additional structured metadata.

## OpinionCluster

- `cluster_id`: Unique cluster identifier.
- `label`: Short cluster name.
- `description`: Cluster description.
- `source_ids`: Source records included in the cluster.
- `stance_distribution`: Counts by stance label.
- `is_minority`: Whether the cluster is considered a minority opinion.
- `is_procedural`: Whether the cluster includes procedural demands.
- `participant_ratio`: Unique participants in this cluster divided by total unique participants.
- `is_numerical_minority`: Whether the ratio falls below the configured threshold.
- `is_normatively_salient`: Whether the topic is important despite low frequency.
- `salience_reasons`: Rights, privacy, safety, procedural, or other salience reasons.
- `representative_quotes`: Example quotes from sources.

## ClusterCoverageAssessment

- `cluster_id`: Opinion cluster being assessed.
- `status`: One of `COVERED`, `WEAKENED`, `DISTORTED`, `OMITTED`.
- `matched_claim_ids`: Summary claims matched to the cluster.
- `semantic_similarity`: Lexical or semantic relatedness; not a representativeness score.
- `stance_preserved`: Whether stance was preserved.
- `intensity_preserved`: Whether intensity was preserved.
- `condition_preserved`: Whether conditions were preserved.
- `quantifier_preserved`: Whether quantity or scope was preserved.
- `explanation`: Human-readable reason for the status.
- `representative_quotes`: Original source quotes.
- `participant_count`: Unique participants represented by the cluster.
- `participant_ratio`: Cluster participant ratio.
- `is_minority`: Whether the cluster is minority or salient.
- `is_normatively_salient`: Whether the cluster is normatively important.

## OmissionResult

- `opinion_units`: Extracted original opinion units.
- `clusters`: Opinion clusters built from original materials.
- `coverage_assessments`: Coverage assessment per cluster.
- `covered_cluster_ids`: Clusters faithfully covered.
- `weakened_cluster_ids`: Clusters weakened in the summary.
- `distorted_cluster_ids`: Clusters whose stance or meaning changed.
- `omitted_cluster_ids`: Clusters absent from the summary.
- `omitted_minority_cluster_ids`: Omitted clusters marked minority.
- `omitted_salient_cluster_ids`: Omitted clusters with normative salience.
- `procedural_cluster_ids`: Clusters involving procedural safeguards.
- `procedural_clusters_omitted`: Procedural clusters omitted from the summary.
- `topic_coverage_numerator` / `topic_coverage_denominator`: Topic coverage count.
- `minority_retention_numerator` / `minority_retention_denominator`: Minority retention count.
- `procedural_issue_retention_numerator` / `procedural_issue_retention_denominator`: Procedural issue retention count.
- `condition_preservation_numerator` / `condition_preservation_denominator`: Condition preservation count.
- `warnings`: Review warnings.

## AuthorizationProfile

- `authorization_id`: Optional declared authorization identifier.
- `represented_subject`: Person or group being represented.
- `authorizing_party`: Party who provided or controls the authorization.
- `authority_basis`: Declared basis such as `DIRECT_CONSENT`, `RESEARCH_CONSENT`, or `UNKNOWN`.
- `source_type`: Type of source material.
- `permitted_operations`: Allowed operations.
- `prohibited_operations`: Disallowed operations.
- `permitted_purposes`: Allowed purposes.
- `prohibited_purposes`: Disallowed purposes.
- `permitted_audiences`: Allowed audiences.
- `prohibited_audiences`: Disallowed audiences.
- `permitted_data_types`: Allowed data types.
- `prohibited_data_types`: Disallowed data types.
- `allow_publication`: Whether public release is allowed.
- `allow_ai_processing`: Whether AI processing is allowed.
- `allow_rewriting`: Whether rewriting is allowed.
- `allow_inference`: Whether inferring attitudes beyond source text is allowed.
- `allow_identity_disclosure`: Whether identities may be disclosed.
- `allow_reuse`: Whether downstream reuse is allowed.
- `allow_model_training`: Whether model training is allowed.
- `valid_from`: Optional validity start.
- `valid_until`: Optional validity end.
- `duration`: Authorization duration.
- `duration_description`: Human-readable duration description.
- `withdrawal_supported`: Whether withdrawal is supported.
- `withdrawal_method`: How withdrawal can be exercised.
- `required_disclosures`: Required notices or caveats.
- `notes`: Additional authorization notes.

## AuthorizationContext

- `intended_operation`: Current operation.
- `intended_purpose`: Current purpose.
- `intended_audience`: Current audience.
- `is_public`: Whether use is public.
- `includes_identity`: Whether identities are included.
- `includes_sensitive_data`: Whether sensitive data is included.
- `uses_ai`: Whether AI processing is used.
- `includes_inference`: Whether inferred attitudes are included.
- `allows_human_review`: Whether human review is available.
- `retention_period`: Intended retention period.
- `downstream_reuse_planned`: Whether reuse is planned.
- `data_types`: Data types used.

## AuthorizationAssessment

- `authorization_status`: One of `ALLOWED`, `CONDITIONAL`, `REAUTHORIZE`, `INTERNAL_ONLY`, `SYNTHETIC_ONLY`, `PROHIBITED`, `UNKNOWN`.
- `matched_permissions`: Declared permissions that match current use.
- `violated_restrictions`: Restrictions violated by current use.
- `missing_information`: Required authorization fields not provided.
- `required_actions`: Actions needed before use.
- `required_disclosures`: Disclosures needed before use.
- `permitted_use_description`: Plain-language permitted scope.
- `prohibited_use_description`: Plain-language prohibited scope.
- `explanation`: Rule-based explanation.
- `rule_ids_triggered`: Rule IDs triggered by the current use.

## AuditRequest

- `project_name`: Audit project name.
- `representation_mode`: One of `INDIVIDUAL`, `REAL_GROUP`, `SYNTHETIC_GROUP`.
- `source_records`: Original source records.
- `ai_generated_summary`: AI-generated summary to audit.
- `authorization_profile`: Authorization constraints.
- `intended_purpose`: Purpose of the current use.
- `intended_audience`: Audience for the current use.
- `is_public`: Whether the use is public.

## AuditPassport

- `representation_mode`: Representation mode being audited.
- `source_count`: Number of source records.
- `claim_count`: Number of extracted claims.
- `traceable_claim_count`: Claims with traceable support or inference.
- `unsupported_claims`: Claim IDs without adequate support.
- `cluster_count`: Number of opinion clusters; currently `0` because clustering is pending.
- `represented_clusters`: Cluster IDs represented in the output.
- `omitted_clusters`: Cluster IDs detected as omitted.
- `minority_clusters_total`: Total number of minority clusters.
- `minority_clusters_retained`: Minority clusters retained in the summary.
- `authorization_status`: Structured authorization result.
- `permitted_use`: Whether the intended use is permitted.
- `required_actions`: Actions required before use.
- `required_disclosures`: Disclosures required before use.
- `final_status`: One of `ALLOWED`, `CONDITIONAL`, `REAUTHORIZE`, `INTERNAL_ONLY`, `SYNTHETIC_ONLY`, `PROHIBITED`.
- `source_trace_result`: Full source tracing result.
- `omission_result`: Full opinion omission result.
- `authorization_assessment`: Full authorization assessment.
- `revision_result`: Faithful revision result.
- `pending_modules`: Modules intentionally not run in the current phase.

## RevisionResult

- `original_summary`: Original AI summary.
- `revised_summary`: Conservative revised summary.
- `removed_claims`: Claim IDs removed or downgraded.
- `modified_claims`: Claim IDs modified.
- `restored_clusters`: Omitted cluster IDs restored.
- `added_disclosures`: Required disclosures added.
- `source_citations`: Mapping from claim or cluster IDs to source IDs.
- `unresolved_issues`: Issues requiring review.
- `human_review_required`: Whether human review is required.
