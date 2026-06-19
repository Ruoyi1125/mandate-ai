"""Authorization boundary comparison component."""
from __future__ import annotations

import streamlit as st

from mandate.schemas import AuthorizationAssessment, AuthorizationProfile, AuthorizationContext
from ui.helpers import AUTH_STATUS_LABEL, badge, section_header


def _bool_display(val: bool | None, true_label: str = "是", false_label: str = "否") -> str:
    if val is True:
        return f'<span style="color:var(--ok-lt);">{true_label}</span>'
    if val is False:
        return f'<span style="color:var(--risk-lt);">{false_label}</span>'
    return '<span style="color:var(--muted);">未知</span>'


def _comparison_row(
    key: str,
    permitted_val: str,
    actual_val: str,
    out_of_scope: bool = False,
    unknown: bool = False,
) -> str:
    if out_of_scope:
        indicator = (
            '<span class="auth-out-of-scope">OUT OF SCOPE · 超出授权</span>'
        )
    elif unknown:
        indicator = (
            '<span style="color:var(--warn-lt);font-family:JetBrains Mono,monospace;'
            'font-size:0.65rem;letter-spacing:0.1em;text-transform:uppercase;">'
            "UNKNOWN · 需要确认</span>"
        )
    else:
        indicator = '<span class="auth-ok">✓ IN SCOPE</span>'

    return (
        f'<div class="auth-comparison-row">'
        f'  <div class="auth-comparison-key">{key}</div>'
        f'  <div style="text-align:center;padding-top:0.1rem;">{indicator}</div>'
        f'  <div class="auth-comparison-val">{actual_val}</div>'
        f"</div>"
    )


def render_authorization_comparison(
    profile: AuthorizationProfile,
    context: AuthorizationContext,
    assessment: AuthorizationAssessment,
) -> None:
    section_header("AUTHORIZATION BOUNDARY", "授权边界")

    auth_label, auth_badge_cls = AUTH_STATUS_LABEL.get(
        assessment.authorization_status, ("UNKNOWN", "badge-neutral")
    )

    st.markdown(
        f'<div style="display:flex;align-items:center;gap:1rem;margin-bottom:1.2rem;">'
        f'<div style="font-size:0.8rem;color:var(--muted);">授权状态</div>'
        f'<div style="font-family:JetBrains Mono,monospace;font-size:1.1rem;font-weight:600;">'
        f'{badge(auth_label, auth_badge_cls)}</div>'
        f"</div>",
        unsafe_allow_html=True,
    )

    # Column headers
    col1, col_mid, col2 = st.columns([5, 3, 5])
    with col1:
        st.markdown(
            '<div class="mandate-label" style="padding:0.4rem 0;">原始授权允许</div>',
            unsafe_allow_html=True,
        )
    with col_mid:
        st.markdown(
            '<div class="mandate-label" style="padding:0.4rem 0;text-align:center;">状态</div>',
            unsafe_allow_html=True,
        )
    with col2:
        st.markdown(
            '<div class="mandate-label" style="padding:0.4rem 0;">当前实际用途</div>',
            unsafe_allow_html=True,
        )

    # Build comparison rows
    rows: list[tuple[str, str, str, bool, bool]] = []

    # Purpose
    permitted_purposes = ", ".join(profile.permitted_purposes) or "未指定"
    actual_purpose = context.intended_purpose
    purpose_ok = any(p in actual_purpose or actual_purpose in p for p in profile.permitted_purposes)
    rows.append(("使用目的", permitted_purposes, actual_purpose, not purpose_ok, not profile.permitted_purposes))

    # Audience
    permitted_audiences = ", ".join(profile.permitted_audiences) or "未指定"
    actual_audience = context.intended_audience
    audience_ok = any(a in actual_audience or actual_audience in a for a in profile.permitted_audiences)
    rows.append(("受众范围", permitted_audiences, actual_audience, not audience_ok, not profile.permitted_audiences))

    # Publication
    permit_pub = "允许" if profile.allow_publication else "不允许"
    actual_pub = "是" if context.is_public else "否"
    pub_scope = context.is_public and not profile.allow_publication
    rows.append(("公开发布", permit_pub, actual_pub, pub_scope, profile.allow_publication is None))

    # AI processing
    permit_ai = "允许" if profile.allow_ai_processing else "不允许"
    actual_ai = "是" if context.uses_ai else "否"
    ai_scope = context.uses_ai and not profile.allow_ai_processing
    rows.append(("AI 处理", permit_ai, actual_ai, ai_scope, profile.allow_ai_processing is None))

    # Inference
    permit_inf = "允许" if profile.allow_inference else "不允许"
    actual_inf = "是" if context.includes_inference else "否"
    inf_scope = context.includes_inference and not profile.allow_inference
    rows.append(("AI 推断", permit_inf, actual_inf, inf_scope, profile.allow_inference is None))

    # Identity
    permit_id = "允许" if profile.allow_identity_disclosure else "不允许"
    actual_id = "是" if context.includes_identity else "否"
    id_scope = context.includes_identity and not profile.allow_identity_disclosure
    rows.append(("身份披露", permit_id, actual_id, id_scope, profile.allow_identity_disclosure is None))

    # Reuse
    permit_reuse = "允许" if profile.allow_reuse else "不允许"
    actual_reuse = "是" if context.downstream_reuse_planned else "否"
    reuse_scope = context.downstream_reuse_planned and not profile.allow_reuse
    rows.append(("后续复用", permit_reuse, actual_reuse, reuse_scope, profile.allow_reuse is None))

    # Model training
    permit_train = "允许" if profile.allow_model_training else "不允许"
    rows.append(("模型训练", permit_train, "未计划", False, profile.allow_model_training is None))

    # Withdrawal
    permit_wd = "支持" if profile.withdrawal_supported else "不支持"
    rows.append(("撤回权", permit_wd, "已声明支持", False, False))

    rows_html = "".join(
        _comparison_row(key, perm, actual, out, unk)
        for key, perm, actual, out, unk in rows
    )

    st.markdown(
        f'<div class="mandate-card" style="padding:0;">'
        f'<div style="padding:0.6rem 1.2rem;background:var(--stone);border-radius:10px 10px 0 0;">'
        f'<div style="display:grid;grid-template-columns:2fr 1fr 2fr;gap:0.5rem;">'
        f'  <div style="font-size:0.65rem;letter-spacing:0.12em;text-transform:uppercase;color:var(--muted);">授权条款</div>'
        f'  <div style="font-size:0.65rem;letter-spacing:0.12em;text-transform:uppercase;color:var(--muted);text-align:center;">核查</div>'
        f'  <div style="font-size:0.65rem;letter-spacing:0.12em;text-transform:uppercase;color:var(--muted);">当前用途</div>'
        f"</div></div>"
        f'<div style="padding:0.2rem 1.2rem;">{rows_html}</div>'
        f"</div>",
        unsafe_allow_html=True,
    )

    # Violations and required actions
    if assessment.violated_restrictions:
        st.markdown(
            '<div class="mandate-card-risk" style="margin-top:1rem;">'
            '<div class="mandate-label" style="color:var(--risk-lt);margin-bottom:0.5rem;">越界项目</div>'
            + "".join(f"<div style='margin-bottom:0.3rem;font-size:0.88rem;'>· {v}</div>" for v in assessment.violated_restrictions)
            + "</div>",
            unsafe_allow_html=True,
        )

    if assessment.required_actions:
        st.markdown(
            '<div class="mandate-card-warn" style="margin-top:0.8rem;">'
            '<div class="mandate-label" style="color:var(--warn-lt);margin-bottom:0.5rem;">必须完成的行动</div>'
            + "".join(f"<div style='margin-bottom:0.3rem;font-size:0.88rem;'>· {a}</div>" for a in assessment.required_actions)
            + "</div>",
            unsafe_allow_html=True,
        )

    if assessment.required_disclosures:
        st.markdown(
            '<div class="mandate-card-accent" style="margin-top:0.8rem;">'
            '<div class="mandate-label" style="color:var(--accent-lt);margin-bottom:0.5rem;">必须增加的披露</div>'
            + "".join(f"<div style='margin-bottom:0.3rem;font-size:0.88rem;'>· {d}</div>" for d in assessment.required_disclosures)
            + "</div>",
            unsafe_allow_html=True,
        )

    if assessment.permitted_use_description:
        st.markdown(
            f'<div style="margin-top:1rem;font-size:0.85rem;">'
            f'<span style="color:var(--muted);">允许用途：</span>'
            f'<span style="color:var(--cream);">{assessment.permitted_use_description}</span>'
            f"</div>",
            unsafe_allow_html=True,
        )

    if assessment.prohibited_use_description:
        st.markdown(
            f'<div style="margin-top:0.4rem;font-size:0.85rem;">'
            f'<span style="color:var(--muted);">禁止用途：</span>'
            f'<span style="color:var(--risk-lt);">{assessment.prohibited_use_description}</span>'
            f"</div>",
            unsafe_allow_html=True,
        )

    st.markdown(
        '<div class="method-note" style="margin-top:1.2rem;">本模块提供规则化授权边界检查，不构成正式法律意见。'
        "授权边界认定基于用户填写的授权信息，不能替代真实法律文件审查。</div>",
        unsafe_allow_html=True,
    )
