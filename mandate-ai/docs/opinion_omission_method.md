# Opinion Omission Method

## Low Frequency Is Not Low Importance

MANDATE separates numerical frequency from normative importance. A topic can involve few participants and still be highly important when it concerns privacy, appeal rights, exit rights, discrimination, severe misclassification, irreversible consequences, safety, minors, or procedural remedies.

This is why `OpinionCluster` has both:

- `is_numerical_minority`: participant ratio below the configured threshold;
- `is_normatively_salient`: rights, risk, or procedural importance detected in the original material.

The interface should describe such clusters as "minority but important" rather than merely "low frequency."

## Opinion Units

One `SourceRecord` may contain several positions. The extractor splits contrastive and compound sentences so a sentence like:

`我支持学校提供预警，但不能使用门禁数据，而且被误判后必须允许申诉。`

becomes:

- support for warning;
- opposition to door-access data;
- procedural demand for appeal.

This prevents a single support word from swallowing the rest of the sentence.

## Coverage Status

- `COVERED`: Topic, stance, intensity, and conditions are preserved.
- `WEAKENED`: Topic is mentioned, but conditions, strength, or importance are weakened.
- `DISTORTED`: Topic is mentioned, but stance or meaning changes.
- `OMITTED`: Topic exists in the original material but disappears from the summary.

## Keywords Are Not Enough

Mentioning a keyword does not mean the view was faithfully preserved. For example, a summary that says "students have slight concerns about data" does not cover an original statement saying "I strongly oppose using door-access data." The topic overlaps, but stance and intensity changed.

## Clustering Needs Review

The default clusterer uses deterministic topic rules and local text similarity patterns. It does not download large models. This makes the system auditable and testable, but it also means humans should review clusters when language is ambiguous, topics overlap, or sources use unusual wording.

## No Population Inference

MANDATE only evaluates the uploaded materials. It cannot infer what the whole student body, the public, or another external population believes. Counts such as `minority_retention_ratio` must be shown with numerator and denominator, for example `1/3`, not as a standalone mandate or popularity score.
