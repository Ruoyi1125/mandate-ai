"""Deterministic provider used for local development and tests."""

from __future__ import annotations

from mandate.claim_extractor import RuleBasedClaimParser
from mandate.providers.base import LLMProvider
from mandate.schemas import AtomicClaim


class MockProvider(LLMProvider):
    """A deterministic stand-in for a real model provider."""

    def extract_claims(self, summary: str) -> list[AtomicClaim]:
        return RuleBasedClaimParser().extract(summary)
