"""YAML-backed authorization checks."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from mandate.schemas import (
    AuditRequest,
    AuthorizationResult,
    AuthorizationStatus,
)


class AuthorizationEngine:
    """Evaluate intended use against profile fields and YAML defaults."""

    def __init__(self, rules_path: Path | str) -> None:
        self.rules_path = Path(rules_path)
        self.rules = self._load_rules()

    def evaluate(self, request: AuditRequest) -> AuthorizationResult:
        profile = request.authorization_profile
        reasons: list[str] = []
        required_actions: list[str] = list(
            self.rules.get("default_required_actions", [])
        )
        required_disclosures: list[str] = list(profile.required_disclosures)

        if profile.prohibited_purposes and request.intended_purpose in profile.prohibited_purposes:
            reasons.append("Intended purpose is explicitly prohibited.")
        if (
            profile.permitted_purposes
            and request.intended_purpose not in profile.permitted_purposes
        ):
            reasons.append("Intended purpose is outside permitted purposes.")
        if (
            profile.permitted_audiences
            and request.intended_audience not in profile.permitted_audiences
        ):
            reasons.append("Intended audience is outside permitted audiences.")
        if request.is_public and "public_release" in profile.prohibited_operations:
            reasons.append("Public release is explicitly prohibited.")

        public_rule = self.rules.get("public_use", {})
        if request.is_public and public_rule.get("requires_disclosure", True):
            disclosure = str(public_rule.get("disclosure_text", "AI-generated summary"))
            if disclosure not in required_disclosures:
                required_disclosures.append(disclosure)

        if reasons:
            return AuthorizationResult(
                status=AuthorizationStatus.REAUTHORIZE_REQUIRED,
                permitted_use=False,
                required_actions=["Obtain renewed authorization."],
                required_disclosures=required_disclosures,
                reasons=reasons,
            )

        if required_actions or required_disclosures:
            return AuthorizationResult(
                status=AuthorizationStatus.CONDITIONAL,
                permitted_use=True,
                required_actions=required_actions,
                required_disclosures=required_disclosures,
                reasons=["Use is permitted if required actions are completed."],
            )

        return AuthorizationResult(
            status=AuthorizationStatus.PERMITTED,
            permitted_use=True,
            required_actions=[],
            required_disclosures=[],
            reasons=["Use matches authorization profile."],
        )

    def _load_rules(self) -> dict[str, Any]:
        if not self.rules_path.exists():
            return {}
        with self.rules_path.open("r", encoding="utf-8") as file:
            data = yaml.safe_load(file) or {}
        if not isinstance(data, dict):
            raise ValueError("authorization rules YAML must contain a mapping")
        return data
