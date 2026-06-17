"""Claim extraction boundary."""

from __future__ import annotations

from mandate.providers.base import LLMProvider
from mandate.schemas import AtomicClaim


class ClaimExtractor:
    """Extract atomic claims through the configured provider."""

    def __init__(self, provider: LLMProvider) -> None:
        self.provider = provider

    def extract(self, summary: str) -> list[AtomicClaim]:
        return self.provider.extract_claims(summary)
