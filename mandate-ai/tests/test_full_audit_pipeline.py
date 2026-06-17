from __future__ import annotations

from tests.test_passport_generator import _passport


def test_full_real_group_pipeline_is_stable() -> None:
    first = _passport().model_dump(mode="json")
    second = _passport().model_dump(mode="json")
    assert first["cluster_count"] == second["cluster_count"]
    assert first["omitted_clusters"] == second["omitted_clusters"]
    assert first["final_status"] == second["final_status"]


def test_full_pipeline_generates_passport_and_revision() -> None:
    passport = _passport()
    assert passport.source_trace_result is not None
    assert passport.omission_result is not None
    assert passport.revision_result is not None
