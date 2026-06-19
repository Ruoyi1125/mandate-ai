"""Revision diff / faithful revision workbench component."""
from __future__ import annotations

import streamlit as st

from mandate.schemas import RevisionResult
from ui.helpers import section_header


def render_revision_diff(revision: RevisionResult | None, original_summary: str) -> None:
    section_header("FAITHFUL REVISION", "忠实修订工作台")

    if revision is None:
        st.info("修订未生成。请重新运行审计。")
        return

    col_left, col_right = st.columns(2)

    with col_left:
        st.markdown(
            '<div class="revision-panel">'
            '<div class="revision-panel-label">原 AI 总结 · Original Summary</div>'
            f'<div class="revision-text">{original_summary}</div>'
            "</div>",
            unsafe_allow_html=True,
        )

    with col_right:
        st.markdown(
            '<div class="revision-panel" style="border-color:rgba(74,127,165,0.35);'
            'background:rgba(74,127,165,0.05);">'
            '<div class="revision-panel-label" style="color:var(--accent-lt);">MANDATE 忠实修订版 · Faithful Revision</div>'
            f'<div class="revision-text">{revision.revised_summary}</div>'
            "</div>",
            unsafe_allow_html=True,
        )

    # Change log
    st.markdown(
        '<div class="mandate-label" style="margin-top:1.2rem;">修改说明</div>',
        unsafe_allow_html=True,
    )

    changes: list[tuple[str, str, list[str]]] = [
        ("删除的无来源主张", "var(--risk-lt)", revision.removed_claims),
        ("修正的主张", "var(--warn-lt)", revision.modified_claims),
        ("补回的消失主题", "var(--accent-lt)", revision.restored_clusters),
        ("新增的披露声明", "var(--ok-lt)", revision.added_disclosures),
    ]

    has_any = any(items for _, _, items in changes)

    if not has_any:
        st.markdown(
            '<div class="mandate-card" style="color:var(--muted);">未检测到需要修改的项目。</div>',
            unsafe_allow_html=True,
        )
    else:
        for label_text, color, items in changes:
            if not items:
                continue
            st.markdown(
                f'<div class="mandate-card" style="margin-bottom:0.6rem;">'
                f'<div style="font-size:0.72rem;font-weight:600;letter-spacing:0.12em;'
                f'text-transform:uppercase;color:{color};margin-bottom:0.5rem;">{label_text}</div>'
                + "".join(
                    f"<div style='font-size:0.88rem;margin-bottom:0.25rem;padding-left:0.5rem;'>"
                    f"· {item}</div>"
                    for item in items
                )
                + "</div>",
                unsafe_allow_html=True,
            )

    if revision.unresolved_issues:
        st.warning(
            "以下问题仍待人工处理：\n"
            + "\n".join(f"- {issue}" for issue in revision.unresolved_issues)
        )

    if revision.human_review_required:
        st.markdown(
            '<div class="method-note">修订版由规则引擎生成，需经人工审核后方可使用。'
            "本输出不代表最终意见，不构成任何正式声明。</div>",
            unsafe_allow_html=True,
        )
