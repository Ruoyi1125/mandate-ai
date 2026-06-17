from __future__ import annotations

import pytest

from mandate.claim_extractor import ClaimExtractor, RuleBasedClaimParser
from mandate.providers.base import LLMProvider
from mandate.schemas import AtomicClaim


def test_rule_extractor_splits_compound_chinese_claim() -> None:
    claims = RuleBasedClaimParser().extract("多数学生支持AI预警，但担心隐私泄露和被错误标签化。")
    assert [claim.text for claim in claims] == [
        "多数学生支持AI预警",
        "学生担心隐私泄露",
        "学生担心被错误标签化",
    ]
    assert claims[0].quantifier == "多数"
    assert claims[0].stance == "support"
    assert claims[1].stance == "concern"


class BadProvider(LLMProvider):
    def extract_claims(self, summary: str) -> list[AtomicClaim]:  # type: ignore[override]
        return ["not a claim"]  # type: ignore[list-item]


def test_mock_provider_output_format_error_is_rejected() -> None:
    with pytest.raises(TypeError):
        ClaimExtractor(BadProvider()).extract("多数学生支持AI预警。")
