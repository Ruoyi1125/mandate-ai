"""Representation Passport credential component."""
from __future__ import annotations

import streamlit as st

from mandate.passport_generator import PassportExporter
from mandate.schemas import AuditPassport, FinalStatus
from ui.helpers import (
    AUTH_STATUS_LABEL,
    FINAL_STATUS_LABEL,
    badge,
    section_header,
)


def _passport_status_style(status: FinalStatus) -> tuple[str, str]:
    """Return (background gradient stop, text color) for a status."""
    mapping = {
        FinalStatus.ALLOWED:        ("#3a7a5a", "var(--ok-lt)"),
        FinalStatus.CONDITIONAL:    ("#8a6020", "var(--warn-lt)"),
        FinalStatus.REAUTHORIZE:    ("#9b3a3a", "var(--risk-lt)"),
        FinalStatus.INTERNAL_ONLY:  ("#2a5070", "var(--accent-lt)"),
        FinalStatus.SYNTHETIC_ONLY: ("#3d4354", "var(--muted)"),
        FinalStatus.PROHIBITED:     ("#9b3a3a", "var(--risk-lt)"),
    }
    return mapping.get(status, ("#3d4354", "var(--muted)"))


def render_passport(passport: AuditPassport) -> None:
    section_header("REPRESENTATION PASSPORT", "代言凭证")

    final_label, final_badge_cls = FINAL_STATUS_LABEL.get(
        passport.final_status, ("UNKNOWN", "badge-neutral")
    )
    auth_label, auth_badge_cls = AUTH_STATUS_LABEL.get(
        passport.authorization_status, ("UNKNOWN", "badge-neutral")
    )
    _, status_color = _passport_status_style(passport.final_status)

    # ── Passport credential block ──────────────────────────────────────────
    omission = passport.omission_result
    proc_total = omission.procedural_issue_retention_denominator if omission else 0
    proc_retained = omission.procedural_issue_retention_numerator if omission else 0
    covered_count = len(passport.covered_clusters)
    cluster_total = passport.cluster_count

    st.markdown(
        f"""
        <div class="mandate-passport">
            <div class="mandate-passport-header">
                <div>
                    <div class="mandate-passport-wordmark">MANDATE</div>
                    <div class="mandate-passport-title">REPRESENTATION PASSPORT · 代言凭证</div>
                </div>
                <div class="mandate-passport-status" style="color:{status_color};
                     border:1px solid {status_color};background:rgba(0,0,0,0.3);">
                    USE STATUS · {final_label}
                </div>
            </div>

            <div class="mandate-passport-grid">
                <div class="mandate-passport-block">
                    <div class="mandate-passport-block-label">SOURCE · 来源状态</div>
                    <div class="mandate-passport-stat">
                        {passport.traceable_claim_count}<span style="font-size:1rem;color:var(--muted);">/{passport.claim_count}</span>
                    </div>
                    <div class="mandate-passport-stat-desc">主张可追溯</div>
                    <div style="margin-top:0.5rem;font-size:0.78rem;color:{'var(--risk-lt)' if passport.unsupported_claim_ids else 'var(--ok-lt)'};">
                        {len(passport.unsupported_claim_ids)} 个无来源主张
                    </div>
                    <div style="font-size:0.78rem;color:{'var(--warn-lt)' if passport.quantifier_warnings else 'var(--ok-lt)'};">
                        {len(passport.quantifier_warnings)} 个数量词风险
                    </div>
                </div>

                <div class="mandate-passport-block">
                    <div class="mandate-passport-block-label">VOICE · 代表性状态</div>
                    <div class="mandate-passport-stat">
                        {covered_count}<span style="font-size:1rem;color:var(--muted);">/{cluster_total}</span>
                    </div>
                    <div class="mandate-passport-stat-desc">主题忠实覆盖</div>
                    <div style="margin-top:0.5rem;font-size:0.78rem;color:{'var(--risk-lt)' if passport.omitted_clusters else 'var(--ok-lt)'};">
                        {len(passport.omitted_clusters)} 个主题被遗漏
                    </div>
                    <div style="font-size:0.78rem;color:{'var(--warn-lt)' if passport.weakened_clusters else 'var(--ok-lt)'};">
                        {len(passport.weakened_clusters)} 个主题被弱化
                    </div>
                    <div style="font-size:0.78rem;color:var(--muted);">
                        程序性诉求保留 {proc_retained}/{proc_total}
                    </div>
                </div>

                <div class="mandate-passport-block">
                    <div class="mandate-passport-block-label">AUTHORIZATION · 授权状态</div>
                    <div class="mandate-passport-stat" style="font-size:1.1rem;">
                        {auth_label}
                    </div>
                    <div class="mandate-passport-stat-desc">当前用途授权</div>
                    <div style="margin-top:0.5rem;font-size:0.78rem;color:{'var(--risk-lt)' if not passport.permitted_use else 'var(--ok-lt)'};">
                        {'✓ 已获授权' if passport.permitted_use else '✗ 未获授权'}
                    </div>
                    <div style="font-size:0.78rem;color:var(--muted);">
                        {len(passport.missing_authorization_information)} 项信息待确认
                    </div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── Required actions ───────────────────────────────────────────────────
    if passport.required_actions:
        st.markdown(
            '<div class="mandate-card-warn" style="margin-top:1rem;">'
            '<div class="mandate-label" style="color:var(--warn-lt);margin-bottom:0.6rem;">必须完成的行动</div>'
            + "".join(
                f"<div style='display:flex;gap:0.5rem;margin-bottom:0.4rem;font-size:0.88rem;'>"
                f"<span style='color:var(--warn-lt);font-weight:600;'>{i + 1}.</span>"
                f"<span>{action}</span></div>"
                for i, action in enumerate(passport.required_actions)
            )
            + "</div>",
            unsafe_allow_html=True,
        )

    if passport.required_disclosures:
        st.markdown(
            '<div class="mandate-card-accent" style="margin-top:0.8rem;">'
            '<div class="mandate-label" style="color:var(--accent-lt);margin-bottom:0.5rem;">必须增加的披露说明</div>'
            + "".join(
                f"<div style='margin-bottom:0.3rem;font-size:0.88rem;'>· {d}</div>"
                for d in passport.required_disclosures
            )
            + "</div>",
            unsafe_allow_html=True,
        )

    # ── Download buttons ───────────────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(
        '<div class="mandate-label">导出代言凭证</div>',
        unsafe_allow_html=True,
    )
    exporter = PassportExporter()
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.download_button(
            "⬇  JSON",
            exporter.to_json(passport),
            file_name="mandate_passport.json",
            mime="application/json",
            use_container_width=True,
        )
    with col2:
        st.download_button(
            "⬇  Markdown",
            exporter.to_markdown(passport),
            file_name="mandate_passport.md",
            mime="text/markdown",
            use_container_width=True,
        )
    with col3:
        st.download_button(
            "⬇  HTML",
            exporter.to_html(passport),
            file_name="mandate_passport.html",
            mime="text/html",
            use_container_width=True,
        )
    with col4:
        with st.expander("查看原始 JSON"):
            st.json(passport.model_dump(mode="json"))
