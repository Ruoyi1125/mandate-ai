# Data Dictionary

## SourceRecord

- `source_id`: Unique source record identifier.
- `participant_id`: Optional participant identifier; may be anonymous.
- `text`: Original opinion or testimony text.
- `metadata`: Additional structured metadata.
- `consent_id`: Optional consent or authorization record identifier.

## AtomicClaim

- `claim_id`: Unique claim identifier.
- `text`: Minimal checkable claim text.
- `quantifier`: Optional quantity marker such as `部分`, `多数`, or `一致`.
- `stance`: Optional position label.
- `importance`: Claim importance from `0.0` to `1.0`.

## EvidenceMatch

- `claim_id`: Claim being checked.
- `source_id`: Source record used as evidence.
- `similarity_score`: Match score from `0.0` to `1.0`.
- `support_status`: One of `DIRECTLY_SUPPORTED`, `PARTIALLY_SUPPORTED`, `INFERRED`, `UNSUPPORTED`, `CONTRADICTED`.
- `explanation`: Human-readable reason for the match.

## OpinionCluster

- `cluster_id`: Unique cluster identifier.
- `label`: Short cluster name.
- `description`: Cluster description.
- `source_ids`: Source records included in the cluster.
- `stance_distribution`: Counts by stance label.
- `is_minority`: Whether the cluster is considered a minority opinion.
- `representative_quotes`: Example quotes from sources.

## AuthorizationProfile

- `represented_subject`: Person or group being represented.
- `source_type`: Type of source material.
- `permitted_operations`: Allowed operations.
- `prohibited_operations`: Disallowed operations.
- `permitted_purposes`: Allowed purposes.
- `prohibited_purposes`: Disallowed purposes.
- `permitted_audiences`: Allowed audiences.
- `duration`: Authorization duration.
- `withdrawal_supported`: Whether withdrawal is supported.
- `required_disclosures`: Required notices or caveats.

## AuditRequest

- `project_name`: Audit project name.
- `representation_mode`: One of `INDIVIDUAL`, `REAL_GROUP`, `SYNTHETIC_GROUP`.
- `source_records`: Validated original source records.
- `ai_generated_summary`: AI-generated summary to audit.
- `authorization_profile`: Authorization constraints.
- `intended_purpose`: Purpose of the current use.
- `intended_audience`: Audience for the current use.
- `is_public`: Whether the use is public.

## AuditPassport

- `representation_mode`: Representation mode being audited.
- `source_count`: Number of source records.
- `claim_count`: Number of extracted claims.
- `traceable_claim_count`: Claims with traceable support.
- `unsupported_claims`: Claim IDs without adequate support.
- `cluster_count`: Number of opinion clusters.
- `represented_clusters`: Cluster IDs represented in the output.
- `omitted_clusters`: Cluster IDs detected as omitted.
- `minority_clusters_total`: Total number of minority clusters.
- `minority_clusters_retained`: Minority clusters retained in the summary.
- `authorization_status`: Structured authorization result.
- `permitted_use`: Whether the intended use is permitted.
- `required_actions`: Actions required before use.
- `required_disclosures`: Disclosures required before use.
- `final_status`: One of `ALLOWED`, `CONDITIONAL`, `REAUTHORIZE`, `INTERNAL_ONLY`, `SYNTHETIC_ONLY`, `PROHIBITED`.
