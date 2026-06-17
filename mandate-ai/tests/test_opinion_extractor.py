from __future__ import annotations

import pytest

from mandate.opinion_extractor import OpinionExtractor
from mandate.schemas import OpinionStance, SourceRecord


def test_one_source_splits_support_opposition_and_procedural_demand() -> None:
    source = SourceRecord(
        source_id="s1",
        participant_id="p1",
        text="我支持学校提供预警，但不能使用门禁数据，而且被误判后必须允许申诉。",
        metadata={},
    )

    units = OpinionExtractor().extract([source])

    assert len(units) == 3
    assert any(unit.stance == OpinionStance.SUPPORT for unit in units)
    assert any(unit.stance == OpinionStance.OPPOSE and unit.topic == "门禁数据用途" for unit in units)
    assert any(unit.is_procedural and unit.topic == "申诉机制" for unit in units)


def test_opinion_extractor_rejects_empty_sources() -> None:
    with pytest.raises(ValueError, match="source record"):
        OpinionExtractor().extract([])
