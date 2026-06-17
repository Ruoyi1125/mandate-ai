# Revision Method

The revision generator is conservative and template-based. It may only use:

- uploaded source records;
- source tracing evidence;
- opinion clusters and representative quotes;
- omission results;
- authorization assessment and required disclosures.

It does not invent balancing viewpoints. If no source supports a view, that view is removed or downgraded.

## Revision Rules

- Unsupported claims are removed or replaced with uncertainty.
- Overstated quantifiers are downgraded to what the uploaded materials support.
- Deleted conditions are restored.
- Omitted salient clusters are restored, especially appeal, correction, exit rights, door-access data opposition, labelling, and severe misclassification.
- Required disclosures are prepended.

Every restored cluster carries source citations through `RevisionResult.source_citations`.

## Human Review

The generated revision favors fidelity over style. Human review is required before publication, formal group representation, or any decision-making use.
