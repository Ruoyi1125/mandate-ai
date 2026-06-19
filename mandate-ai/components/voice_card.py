"""Voice map and lost voices components."""
from __future__ import annotations

import streamlit as st

from mandate.schemas import (
    ClusterCoverageAssessment,
    CoverageStatus,
    OmissionResult,
    OpinionCluster,
)
from ui.helpers import (
    COVERAGE_BADGE,
    COVERAGE_CARD_CLASS,
    COVERAGE_LABEL,
    badge,
    section_header,
    suggest_revision,
)


def render_voice_map(omission: OmissionResult) -> None:
    section_header("VOICE MAP", "声音地图")

    total_clusters = len(omission.clusters)
    covered = len(omission.covered_cluster_ids)
    omitted_count = len(omission.omitted_cluster_ids)
    weakened_count = len(omission.weakened_cluster_ids)
    distorted_count = len(omission.distorted_cluster_ids)

    st.markdown(
        f"""<div class="stats-row">
            <div class="stat-block">
                <div class="stat-block-label">意见主题总数</div>
                <div class="stat-block-value">{total_clusters}</div>
                <div class="stat-block-sub">来自原始材料</div>
            </div>
            <div class="stat-block">
                <div class="stat-block-label">忠实覆盖</div>
                <div class="stat-block-value" style="color:var(--ok-lt);">{covered}</div>
                <div class="stat-block-sub">在AI总结中保留</div>
            </div>
            <div class="stat-block">
                <div class="stat-block-label">被遗漏 / 弱化 / 扭曲</div>
                <div class="stat-block-value" style="color:var(--risk-lt);">{omitted_count} / {weakened_count} / {distorted_count}</div>
                <div class="stat-block-sub">需要关注</div>
            </div>
        </div>""",
        unsafe_allow_html=True,
    )

    cluster_lookup = {c.cluster_id: c for c in omission.clusters}

    # Sort: omitted first, then weakened/distorted, then covered
    order = {
        CoverageStatus.OMITTED: 0,
        CoverageStatus.DISTORTED: 1,
        CoverageStatus.WEAKENED: 2,
        CoverageStatus.COVERED: 3,
    }
    sorted_assessments = sorted(
        omission.coverage_assessments,
        key=lambda a: (order.get(a.status, 9), not a.is_normatively_salient),
    )

    for assessment in sorted_assessments:
        cluster = cluster_lookup.get(assessment.cluster_id)
        if cluster is None:
            continue
        _render_voice_cluster_card(cluster, assessment)


def _render_voice_cluster_card(
    cluster: OpinionCluster, assessment: ClusterCoverageAssessment
) -> None:
    status = assessment.status
    card_cls = COVERAGE_CARD_CLASS.get(status, "")
    status_label = COVERAGE_LABEL[status]
    status_badge_cls = COVERAGE_BADGE[status]

    tags: list[str] = []
    if cluster.is_minority:
        tags.append(badge("少数意见", "badge-neutral"))
    if cluster.is_normatively_salient:
        tags.append(badge("规范重要性", "badge-gold"))
    if cluster.is_procedural:
        tags.append(badge("程序性诉求", "badge-accent"))

    stances = " / ".join(
        f"{k}:{v}" for k, v in cluster.stance_distribution.items()
    ) or "未标注"

    quotes_html = "".join(
        f'<div class="mandate-quote"><span class="claim-source-id">'
        f'{src_id}</span> {quote}</div>'
        for src_id, quote in zip(
            cluster.source_ids[:2],
            cluster.representative_quotes[:2],
            strict=False,
        )
    )

    tags_html = "&nbsp;".join(tags)

    with st.expander(
        f"{cluster.label}  ·  {status_label}",
        expanded=(status in {CoverageStatus.OMITTED, CoverageStatus.DISTORTED}),
    ):
        st.markdown(
            f'<div class="voice-card {card_cls}">'
            f'<div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:0.6rem;">'
            f'  <div><span style="font-size:1.0rem;font-weight:600;color:var(--cream);">{cluster.label}</span>'
            f'  &nbsp;&nbsp;{tags_html}</div>'
            f'  <div>{badge(status_label, status_badge_cls)}</div>'
            f"</div>"
            f'<div style="font-size:0.82rem;color:var(--muted);margin-bottom:0.5rem;">'
            f"涉及 <b style='color:var(--cream);'>{cluster.unique_participant_count}</b> 位参与者"
            f"&nbsp;·&nbsp;立场分布：{stances}"
            f"</div>"
            f"{quotes_html}"
            f'<div style="font-size:0.8rem;color:var(--muted);margin-top:0.5rem;">'
            f"{assessment.explanation}"
            f"</div>"
            f"</div>",
            unsafe_allow_html=True,
        )
        if cluster.salience_reasons:
            st.caption("规范重要性原因：" + "、".join(cluster.salience_reasons))


def render_lost_voices(omission: OmissionResult) -> None:
    """Render the VOICES LOST IN SUMMARY section."""
    cluster_lookup = {c.cluster_id: c for c in omission.clusters}

    lost = [
        item
        for item in omission.coverage_assessments
        if item.status == CoverageStatus.OMITTED
    ]
    lost.sort(
        key=lambda item: (
            not item.is_normatively_salient,
            item.cluster_id not in omission.procedural_cluster_ids,
            -item.participant_count,
        )
    )

    # Header
    st.markdown(
        """<div class="lost-voices-header">
            <div class="lost-voices-title">VOICES LOST IN SUMMARY</div>
            <div class="lost-voices-subtitle">消失的声音 · 在AI总结中完全缺失的原始主题</div>
        </div>""",
        unsafe_allow_html=True,
    )

    if not lost:
        st.markdown(
            '<div class="mandate-card-ok" style="text-align:center;padding:2rem;">'
            "<b>未发现完全消失的原始主题。</b><br>"
            '<span style="color:var(--muted);font-size:0.85rem;">所有主要意见主题均在AI总结中有所体现。</span>'
            "</div>",
            unsafe_allow_html=True,
        )
        return

    st.markdown(
        f'<p style="color:var(--muted);font-size:0.88rem;margin-bottom:1.2rem;">'
        f"以下 <b style='color:var(--risk-lt);'>{len(lost)}</b> 个原始意见主题在AI总结中完全缺失。"
        f"这些不是边缘意见，而是来自真实参与者的真实声音。"
        f"</p>",
        unsafe_allow_html=True,
    )

    for item in lost:
        cluster = cluster_lookup.get(item.cluster_id)
        if cluster is None:
            continue
        _render_lost_voice_card(cluster, item, omission)


def _render_lost_voice_card(
    cluster: OpinionCluster,
    assessment: ClusterCoverageAssessment,
    omission: OmissionResult,
) -> None:
    tags: list[str] = []
    if cluster.is_normatively_salient:
        tags.append(badge("规范重要性", "badge-gold"))
    if cluster.is_procedural:
        tags.append(badge("程序性诉求", "badge-accent"))
    if cluster.is_minority:
        tags.append(badge("少数意见", "badge-neutral"))

    tags_html = " ".join(tags)
    revision_hint = suggest_revision(
        cluster.label, cluster.is_procedural, cluster.is_normatively_salient
    )

    with st.expander(
        f"🚫  {cluster.label}  ·  涉及 {assessment.participant_count} 位参与者",
        expanded=True,
    ):
        st.markdown(
            f'<div class="mandate-card-risk">'
            f'<div style="display:flex;justify-content:space-between;margin-bottom:0.8rem;">'
            f'  <div style="font-size:1.05rem;font-weight:600;color:var(--cream);">{cluster.label}</div>'
            f"  <div>{tags_html}</div>"
            f"</div>"
            f'<div style="font-size:0.82rem;color:var(--muted);margin-bottom:0.8rem;">'
            f"涉及 <b style='color:var(--cream);'>{assessment.participant_count}</b> 位参与者"
            f"</div>",
            unsafe_allow_html=True,
        )

        if cluster.salience_reasons:
            st.markdown(
                '<div style="font-size:0.83rem;color:var(--warn-lt);margin-bottom:0.6rem;">'
                "为什么重要：" + "、".join(cluster.salience_reasons)
                + "</div>",
                unsafe_allow_html=True,
            )

        for src_id, quote in zip(
            cluster.source_ids[:3],
            cluster.representative_quotes[:3],
            strict=False,
        ):
            st.markdown(
                f'<div class="mandate-quote">'
                f'<span class="claim-source-id">{src_id}</span> {quote}'
                f"</div>",
                unsafe_allow_html=True,
            )

        st.markdown(
            f'<div style="margin-top:0.8rem;padding:0.6rem 0.9rem;background:rgba(0,0,0,0.2);'
            f'border-radius:4px;font-size:0.83rem;color:var(--accent-lt);">'
            f"建议修订：{revision_hint}"
            f"</div></div>",
            unsafe_allow_html=True,
        )

    # Weakened and distorted summary at bottom
    weakened_or_distorted = [
        item
        for item in omission.coverage_assessments
        if item.status in {CoverageStatus.WEAKENED, CoverageStatus.DISTORTED}
    ]
    if weakened_or_distorted:
        cluster_lookup = {c.cluster_id: c for c in omission.clusters}
        st.markdown(
            '<div class="mandate-label" style="margin-top:1.2rem;">被弱化或扭曲的主题</div>',
            unsafe_allow_html=True,
        )
        for item in weakened_or_distorted:
            c = cluster_lookup.get(item.cluster_id)
            if c:
                status_lbl = COVERAGE_LABEL[item.status]
                badge_cls = COVERAGE_BADGE[item.status]
                st.markdown(
                    f'<div style="display:flex;gap:0.6rem;align-items:center;'
                    f'padding:0.4rem 0;border-bottom:1px solid var(--stone);font-size:0.88rem;">'
                    f'<span style="color:var(--cream);">{c.label}</span>'
                    f'<span>{badge(status_lbl, badge_cls)}</span>'
                    f'<span style="color:var(--muted);font-size:0.8rem;">{item.explanation}</span>'
                    f"</div>",
                    unsafe_allow_html=True,
                )
