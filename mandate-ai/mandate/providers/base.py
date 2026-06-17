"""Abstract provider contracts."""

from __future__ import annotations

from abc import ABC, abstractmethod

from mandate.schemas import AtomicClaim


class LLMProvider(ABC):
    """Minimal provider interface for later LLM-backed components."""

    @abstractmethod
    def extract_claims(self, summary: str) -> list[AtomicClaim]:
        """Extract atomic claims from a summary."""
