# Authorization Method

MANDATE does not guess authorization. The engine only uses explicit fields in `AuthorizationProfile` and the actual-use fields in `AuthorizationContext`.

Missing authorization information returns `UNKNOWN` or requires reauthorization. It never defaults to allowed.

## Independent Dimension

Authorization is separate from source support and representativeness. A summary can be well supported but unauthorized for public release. A use can be authorized internally while the content still needs revision because it omits salient voices.

## Deterministic Rules

Rules are stored in `rules/authorization_rules.yaml`. Each rule has:

- `rule_id`
- `description`
- `condition`
- `status`
- `required_action`
- `required_disclosure`
- `severity`

The engine currently checks purpose, audience, publication, AI processing, inference, identity disclosure, reuse, model training, missing authorization, withdrawal method, required disclosures, and universal representation claims.

## No Legal Opinion

The result describes whether the declared authorization appears to cover the current configured use. It is not a formal legal opinion and does not decide whether a contract or consent form is legally valid.
