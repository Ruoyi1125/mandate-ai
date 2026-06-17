from __future__ import annotations

from tests.test_passport_generator import _passport


def test_revision_removes_unsupported_claims_and_restores_conditions() -> None:
    passport = _passport()
    revision = passport.revision_result

    assert revision is not None
    assert revision.removed_claims
    assert "整体认为该系统利大于弊" not in revision.revised_summary
    assert "限定条件" in revision.revised_summary or "条件" in revision.revised_summary


def test_revision_restores_appeal_exit_and_door_access_without_new_views() -> None:
    passport = _passport()
    revision = passport.revision_result

    assert revision is not None
    assert "申诉" in revision.revised_summary
    assert "退出" in revision.revised_summary
    assert "门禁" in revision.revised_summary
    assert "停车费" not in revision.revised_summary
    assert revision.source_citations
