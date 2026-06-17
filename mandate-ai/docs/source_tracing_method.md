# Source Tracing Method

## Similarity Is Not Support

MANDATE first retrieves candidate evidence using local TF-IDF. Similarity only means that a source record shares lexical or semantic material with a claim. It does not mean the source supports the claim.

For example, "students oppose AI warning systems" may be highly similar to "students support AI warning systems" because both mention the same topic. The support classifier must still inspect stance, conditions, quantifiers, and contradiction.

## No Truth Percentage

The system does not ask a model to produce a single truth percentage. A percentage would hide the evidence chain and can imply a level of certainty the uploaded materials do not justify.

Instead, each claim receives:

- candidate source records;
- a support relation label;
- quantifier assessment;
- warnings for condition deletion, exaggeration, unsupported additions, and contradiction.

`EvidenceMatch.confidence` only describes confidence in the classifier's label. It is not a score for whether the claim is true.

## Quantifier Checks

Quantifier checks are limited to the uploaded materials:

- `所有` / `全部` / `一致`: every unique participant must support the claim, with no contradiction.
- `多数`: supporting unique participants must exceed half of the uploaded participant count.
- `绝大多数`: supporting ratio must meet the YAML threshold, currently `0.75`.
- `部分`: at least the configured minimum number of independent participants must support the claim.
- `少数` / `个别`: support must exist but remain below or equal to half.
- `主要` / `最大` / `核心`: requires comparison across themes. If theme statistics are unavailable, the system marks it as not proven.

Multiple source records from the same `participant_id` are counted once. Missing `participant_id` values fall back to `source_id`.

## Current Limits

- Claim extraction is rule-based and may miss complex syntax.
- TF-IDF retrieval can miss paraphrases without shared wording.
- The support classifier uses transparent heuristics, not a formally verified logic system.
- Theme comparison for "main" or "largest" concerns is not implemented.
- The system does not provide legal advice and does not decide formal authorization validity.

## Human Review Needed

Human review is still required when:

- source wording is ambiguous;
- a claim combines multiple subjects or conditions;
- the uploaded sources are not representative;
- authorization terms are legally or institutionally binding;
- a final public statement will be issued on behalf of a real group.
