"""Claim evidence card component."""
from __future__ import annotations

import streamlit as st

from mandate.schemas import ClaimEvidenceBundle, SupportStatus
from ui.helpers import (
    SUPPORT_BADGE,
    SUPPORT_LABEL,
    badge,
    section_header,
)


def _card_class(status: SupportStatus) -> str:
    mapping = {
        SupportStatus.DIRECTLY_SUPPORTED: "ok",
        SupportStatus.PARTIALLY_SUPPORTED: "warn",
        SupportStatus.INFERRED: "accent",
        SupportStatus.UNSUPPORTED: "risk",
        SupportStatus.CONTRADICTED: "risk",
    }
    return mapping.get(status, "")


def render_claim_card(bundle: ClaimEvidenceBundle, idx: int) -> None:
    status = bundle.final_support_status
    label_zh = SUPPORT_LABEL[status]
    badge_cls = SUPPORT_BADGE[status]
    card_cls = _card_class(status)

    with st.expander(
        f"主张 {idx + 1}  ·  {bundle.claim.text[:60]}{'…' if len(bundle.claim.text) > 60 else ''}",
        expanded=(status in {SupportStatus.UNSUPPORTED, SupportStatus.CONTRADICTED}),
    ):
        # Status + quantifier row
        col_a, col_b = st.columns([3, 1])
        with col_a:
            st.markdown(
                f'<div class="claim-text">{bundle.claim.text}</div>',
                unsafe_allow_html=True,
            )
        with col_b:
            st.markdown(
                f'<div style="text-align:right;margin-top:0.3rem;">'
                f'{badge(label_zh, badge_cls)}'
                f'<br><span style="font-size:0.7rem;color:var(--muted);font-family:JetBrains Mono,monospace;">'
                f'{status.value}</span>'
                f"</div>",
                unsafe_allow_html=True,
            )

        # Quantifier warning
        if bundle.claim.quantifier:
            q = bundle.claim.quantifier
            q_ok = bundle.quantifier_assessment and bundle.quantifier_assessment.supported
            q_badge = badge("数量词已验证", "badge-ok") if q_ok else badge("数量词存疑", "badge-risk")
            st.markdown(
                f'<div style="margin-bottom:0.6rem;">'
                f'识别到数量词 <code>{q}</code> &nbsp;{q_badge}'
                f"</div>",
                unsafe_allow_html=True,
            )
            if bundle.quantifier_assessment:
                qa = bundle.quantifier_assessment
                st.caption(
                    f"支持：{qa.supporting_participant_count} 人 / "
                    f"反对：{qa.opposing_participant_count} 人 / "
                    f"总计：{qa.total_participant_count} 人 · "
                    f"比例 {qa.observed_ratio:.0%} · {qa.explanation}"
                )

        # Evidence matches
        if bundle.candidate_matches:
            st.markdown(
                '<div class="mandate-label" style="margin-top:0.8rem;">来源证据</div>',
                unsafe_allow_html=True,
            )
            for m in bundle.candidate_matches[:4]:
                s_badge = badge(SUPPORT_LABEL[m.support_status], SUPPORT_BADGE[m.support_status])
                cond_note = ""
                if m.condition_preserved is False:
                    cond_note = " &nbsp;" + badge("条件已删除", "badge-risk")
                st.markdown(
                    f'<div class="claim-evidence-item">'
                    f'<span class="claim-source-id">{m.source_id}</span>'
                    f'&nbsp;&nbsp;{s_badge}{cond_note}'
                    f'<div style="margin-top:0.4rem;color:var(--cream);font-size:0.88rem;">{m.source_text}</div>'
                    f'<div style="margin-top:0.3rem;color:var(--muted);font-size:0.78rem;">{m.explanation}</div>'
                    f"</div>",
                    unsafe_allow_html=True,
                )

        if bundle.contradicting_matches:
            st.markdown(
                '<div class="mandate-label" style="margin-top:0.8rem;color:var(--risk-lt);">反对意见</div>',
                unsafe_allow_html=True,
            )
            for m in bundle.contradicting_matches[:2]:
                st.markdown(
                    f'<div class="mandate-quote">{m.source_text}</div>',
                    unsafe_allow_html=True,
                )

        if bundle.warnings:
            for w in bundle.warnings:
                st.warning(w)


def render_source_section(bundles: list[ClaimEvidenceBundle]) -> None:
    section_header("SOURCE VERIFICATION", "来源验证")

    total = len(bundles)
    supported = sum(
        1
        for b in bundles
        if b.final_support_status
        in {SupportStatus.DIRECTLY_SUPPORTED, SupportStatus.PARTIALLY_SUPPORTED}
    )
    unsupported = sum(
        1 for b in bundles if b.final_support_status == SupportStatus.UNSUPPORTED
    )
    quantifier_risks = sum(
        1
        for b in bundles
        if b.quantifier_assessment and not b.quantifier_assessment.supported
    )

    st.markdown(
        f"""<div class="stats-row">
            <div class="stat-block">
                <div class="stat-block-label">可追溯主张</div>
                <div class="stat-block-value">{supported}<span style="font-size:1rem;color:var(--muted);">/{total}</span></div>
                <div class="stat-block-sub">有原始材料支持</div>
            </div>
            <div class="stat-block">
                <div class="stat-block-label">无来源主张</div>
                <div class="stat-block-value" style="color:{'var(--risk-lt)' if unsupported else 'var(--ok-lt)'};">{unsupported}</div>
                <div class="stat-block-sub">缺乏原始依据</div>
            </div>
            <div class="stat-block">
                <div class="stat-block-label">数量词风险</div>
                <div class="stat-block-value" style="color:{'var(--warn-lt)' if quantifier_risks else 'var(--ok-lt)'};">{quantifier_risks}</div>
                <div class="stat-block-sub">数量词未获支持</div>
            </div>
        </div>""",
        unsafe_allow_html=True,
    )

    for i, bundle in enumerate(bundles):
        render_claim_card(bundle, i)

    st.markdown(
        '<div class="method-note">来源追踪基于TF-IDF语义相似度匹配与规则分类。'
        "相似度分数仅作参考，最终支持状态由规则引擎决定。</div>",
        unsafe_allow_html=True,
    )
