"""Revision suggestion placeholder."""

from __future__ import annotations

from mandate.schemas import AuditPassport


class RevisionGenerator:
    """Produce minimal revision guidance for later UI use."""

    def suggest(self, passport: AuditPassport) -> list[str]:
        suggestions: list[str] = []
        if passport.unsupported_claims:
            suggestions.append("Remove or qualify unsupported claims.")
        if passport.omitted_clusters:
            suggestions.append("Add disclosed coverage of omitted opinion clusters.")
        if passport.required_actions:
            suggestions.extend(passport.required_actions)
        return suggestions
