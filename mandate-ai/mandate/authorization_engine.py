"""Deterministic YAML-backed authorization checks."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from mandate.schemas import (
    AuditRequest,
    AuthorizationAssessment,
    AuthorizationContext,
    AuthorizationProfile,
    AuthorizationStatus,
    AuthorityBasis,
)


class AuthorizationEngine:
    """Evaluate intended use against declared authorization fields."""

    def __init__(self, rules_path: Path | str) -> None:
        self.rules_path = Path(rules_path)
        self.rules = self._load_rules()
        self.rule_definitions = {
            str(rule.get("rule_id")): rule
            for rule in self.rules.get("authorization_rules", [])
            if isinstance(rule, dict) and rule.get("rule_id")
        }

    def evaluate(self, request: AuditRequest) -> AuthorizationAssessment:
        profile = request.authorization_profile
        context = request.authorization_context or AuthorizationContext(
            intended_operation="summarize",
            intended_purpose=request.intended_purpose,
            intended_audience=request.intended_audience,
            is_public=request.is_public,
            includes_identity=False,
            includes_sensitive_data=False,
            uses_ai=True,
            includes_inference=False,
            allows_human_review=True,
            retention_period=None,
            downstream_reuse_planned=False,
        )

        matched_permissions: list[str] = []
        violations: list[str] = []
        missing: list[str] = []
        required_actions: list[str] = []
        disclosures: list[str] = list(profile.required_disclosures)
        triggered: list[str] = []

        if self._missing_authorization(profile):
            self._trigger("AUTHORIZATION_MISSING", triggered, required_actions, disclosures)
            missing.extend(["authority_basis", "authorizing_party"])

        if context.intended_operation in profile.permitted_operations:
            matched_permissions.append(f"operation:{context.intended_operation}")
        elif profile.permitted_operations:
            self._trigger("PURPOSE_OUT_OF_SCOPE", triggered, required_actions, disclosures)
            violations.append(f"operation:{context.intended_operation}")

        if context.intended_purpose in profile.permitted_purposes:
            matched_permissions.append(f"purpose:{context.intended_purpose}")
        elif profile.permitted_purposes or context.intended_purpose in profile.prohibited_purposes:
            self._trigger("PURPOSE_OUT_OF_SCOPE", triggered, required_actions, disclosures)
            violations.append(f"purpose:{context.intended_purpose}")

        if context.intended_audience in profile.permitted_audiences:
            matched_permissions.append(f"audience:{context.intended_audience}")
        elif profile.permitted_audiences or context.intended_audience in profile.prohibited_audiences:
            self._trigger("AUDIENCE_OUT_OF_SCOPE", triggered, required_actions, disclosures)
            violations.append(f"audience:{context.intended_audience}")

        if context.is_public and profile.allow_publication is not True:
            self._trigger("PUBLICATION_NOT_ALLOWED", triggered, required_actions, disclosures)
            violations.append("publication")
        if context.uses_ai and profile.allow_ai_processing is False:
            self._trigger("AI_PROCESSING_NOT_ALLOWED", triggered, required_actions, disclosures)
            violations.append("ai_processing")
        elif context.uses_ai and profile.allow_ai_processing is None:
            missing.append("allow_ai_processing")
        if context.includes_inference and profile.allow_inference is not True:
            self._trigger("INFERENCE_NOT_ALLOWED", triggered, required_actions, disclosures)
            violations.append("inference")
        if context.includes_identity and profile.allow_identity_disclosure is False:
            self._trigger("IDENTITY_DISCLOSURE_NOT_ALLOWED", triggered, required_actions, disclosures)
            violations.append("identity_disclosure")
        elif context.includes_identity and profile.allow_identity_disclosure is None:
            missing.append("allow_identity_disclosure")
        if context.downstream_reuse_planned and profile.allow_reuse is not True:
            self._trigger("REUSE_NOT_ALLOWED", triggered, required_actions, disclosures)
            violations.append("reuse")
        if profile.allow_model_training is False:
            matched_permissions.append("model_training:not_allowed")

        if profile.withdrawal_supported and not profile.withdrawal_method:
            self._trigger("WITHDRAWAL_MECHANISM_MISSING", triggered, required_actions, disclosures)
            missing.append("withdrawal_method")

        if self._universal_representation(context, profile):
            self._trigger("UNIVERSAL_REPRESENTATION_NOT_AUTHORIZED", triggered, required_actions, disclosures)
            violations.append("universal_representation")

        if disclosures:
            self._trigger("REQUIRED_DISCLOSURE_MISSING", triggered, required_actions, disclosures)

        status = self._status(triggered, missing)
        permitted = status in {AuthorizationStatus.ALLOWED, AuthorizationStatus.CONDITIONAL, AuthorizationStatus.INTERNAL_ONLY}
        prohibited = status == AuthorizationStatus.PROHIBITED
        return AuthorizationAssessment(
            authorization_status=status,
            matched_permissions=list(dict.fromkeys(matched_permissions)),
            violated_restrictions=list(dict.fromkeys(violations)),
            missing_information=list(dict.fromkeys(missing)),
            required_actions=list(dict.fromkeys(required_actions)),
            required_disclosures=list(dict.fromkeys(disclosures)),
            permitted_use_description=self._permitted_description(profile, context, permitted),
            prohibited_use_description=self._prohibited_description(violations),
            explanation=self._explanation(status, triggered),
            rule_ids_triggered=list(dict.fromkeys(triggered)),
            permitted_use=permitted and not prohibited,
            prohibited_use=prohibited,
        )

    @staticmethod
    def _missing_authorization(profile: AuthorizationProfile) -> bool:
        return (
            profile.authority_basis == AuthorityBasis.UNKNOWN
            or not profile.authorizing_party
            or not profile.authorization_id
        )

    @staticmethod
    def _universal_representation(
        context: AuthorizationContext,
        profile: AuthorizationProfile,
    ) -> bool:
        text = " ".join([context.intended_purpose, context.intended_audience, profile.notes or ""])
        return any(term in text for term in ["全体", "全部学生", "正式意见", "代表所有"])

    def _trigger(
        self,
        rule_id: str,
        triggered: list[str],
        actions: list[str],
        disclosures: list[str],
    ) -> None:
        rule = self.rule_definitions.get(rule_id, {})
        triggered.append(rule_id)
        action = rule.get("required_action")
        disclosure = rule.get("required_disclosure")
        if action:
            actions.append(str(action))
        if disclosure:
            disclosures.append(str(disclosure))

    def _status(self, triggered: list[str], missing: list[str]) -> AuthorizationStatus:
        statuses = [
            str(self.rule_definitions.get(rule_id, {}).get("status", "CONDITIONAL"))
            for rule_id in triggered
        ]
        if "PROHIBITED" in statuses:
            return AuthorizationStatus.PROHIBITED
        if "REAUTHORIZE" in statuses:
            return AuthorizationStatus.REAUTHORIZE
        if "UNKNOWN" in statuses or missing:
            return AuthorizationStatus.UNKNOWN
        if "CONDITIONAL" in statuses:
            return AuthorizationStatus.CONDITIONAL
        return AuthorizationStatus.ALLOWED

    @staticmethod
    def _permitted_description(
        profile: AuthorizationProfile,
        context: AuthorizationContext,
        permitted: bool,
    ) -> str:
        if not permitted:
            return "Current use is not permitted without additional authorization."
        return (
            f"Permitted for {context.intended_purpose} by {context.intended_audience} "
            f"within declared authorization scope."
        )

    @staticmethod
    def _prohibited_description(violations: list[str]) -> str:
        if not violations:
            return ""
        return "Out-of-scope items: " + ", ".join(violations)

    @staticmethod
    def _explanation(status: AuthorizationStatus, triggered: list[str]) -> str:
        if not triggered:
            return "Declared authorization matches the current use."
        return f"Authorization status {status.value}; triggered rules: {', '.join(dict.fromkeys(triggered))}."

    def _load_rules(self) -> dict[str, Any]:
        if not self.rules_path.exists():
            return {}
        with self.rules_path.open("r", encoding="utf-8") as file:
            data = yaml.safe_load(file) or {}
        if not isinstance(data, dict):
            raise ValueError("authorization rules YAML must contain a mapping")
        return data
