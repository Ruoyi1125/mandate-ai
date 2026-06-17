"""Deterministic provider used for local development and tests."""

from __future__ import annotations

import re

from mandate.providers.base import LLMProvider
from mandate.schemas import AtomicClaim


class MockProvider(LLMProvider):
    """A small deterministic stand-in for a real model provider."""

    def extract_claims(self, summary: str) -> list[AtomicClaim]:
        sentences = [
            part.strip()
            for part in re.split(r"[。.!?\n]+", summary)
            if part.strip()
        ]
        if not sentences:
            return []
        return [
            AtomicClaim(
                claim_id=f"claim_{index + 1}",
                text=sentence,
                quantifier=self._guess_quantifier(sentence),
                stance=None,
                importance=0.7,
            )
            for index, sentence in enumerate(sentences[:5])
        ]

    @staticmethod
    def _guess_quantifier(text: str) -> str | None:
        for token in ("一致", "多数", "部分", "少数"):
            if token in text:
                return token
        return None
