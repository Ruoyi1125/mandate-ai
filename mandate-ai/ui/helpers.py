"""Shared rendering helpers for MANDATE UI (dark-glass theme)."""
from __future__ import annotations

import streamlit as st

from mandate.schemas import (
    AuthorizationStatus,
    CoverageStatus,
    FinalStatus,
    SupportStatus,
)

# ── Label maps ───────────────────────────────────────────────────────────────

SUPPORT_LABEL: dict[SupportStatus, str] = {
    SupportStatus.DIRECTLY_SUPPORTED: "直接支持",
    SupportStatus.PARTIALLY_SUPPORTED: "部分支持",
    SupportStatus.INFERRED: "推断",
    SupportStatus.UNSUPPORTED: "无来源",
    SupportStatus.CONTRADICTED: "矛盾",
}

SUPPORT_BADGE: dict[SupportStatus, str] = {
    SupportStatus.DIRECTLY_SUPPORTED: "b-ok",
    SupportStatus.PARTIALLY_SUPPORTED: "b-warn",
    SupportStatus.INFERRED: "b-accent",
    SupportStatus.UNSUPPORTED: "b-risk",
    SupportStatus.CONTRADICTED: "b-risk",
}

COVERAGE_LABEL: dict[CoverageStatus, str] = {
    CoverageStatus.COVERED: "忠实覆盖",
    CoverageStatus.WEAKENED: "被弱化",
    CoverageStatus.DISTORTED: "被扭曲",
    CoverageStatus.OMITTED: "被遗漏",
}

COVERAGE_BADGE: dict[CoverageStatus, str] = {
    CoverageStatus.COVERED: "b-ok",
    CoverageStatus.WEAKENED: "b-warn",
    CoverageStatus.DISTORTED: "b-risk",
    CoverageStatus.OMITTED: "b-risk",
}

COVERAGE_CARD: dict[CoverageStatus, str] = {
    CoverageStatus.COVERED: "m-card-ok",
    CoverageStatus.WEAKENED: "m-card-warn",
    CoverageStatus.DISTORTED: "m-card-risk",
    CoverageStatus.OMITTED: "m-card-risk",
}

FINAL_STATUS_META: dict[FinalStatus, tuple[str, str]] = {
    FinalStatus.ALLOWED:        ("ALLOWED",        "b-ok"),
    FinalStatus.CONDITIONAL:    ("CONDITIONAL",    "b-warn"),
    FinalStatus.REAUTHORIZE:    ("REAUTHORIZE",    "b-risk"),
    FinalStatus.INTERNAL_ONLY:  ("INTERNAL ONLY",  "b-accent"),
    FinalStatus.SYNTHETIC_ONLY: ("SYNTHETIC ONLY", "b-muted"),
    FinalStatus.PROHIBITED:     ("PROHIBITED",     "b-risk"),
}

FINAL_STATUS_ZH: dict[FinalStatus, str] = {
    FinalStatus.ALLOWED:        "审计通过",
    FinalStatus.CONDITIONAL:    "有条件通过",
    FinalStatus.REAUTHORIZE:    "需重新授权",
    FinalStatus.INTERNAL_ONLY:  "仅限内部使用",
    FinalStatus.SYNTHETIC_ONLY: "仅供示例参考",
    FinalStatus.PROHIBITED:     "已被明确禁止",
}

AUTH_STATUS_META: dict[AuthorizationStatus, tuple[str, str]] = {
    AuthorizationStatus.ALLOWED:              ("ALLOWED",              "b-ok"),
    AuthorizationStatus.PERMITTED:            ("PERMITTED",            "b-ok"),
    AuthorizationStatus.CONDITIONAL:          ("CONDITIONAL",          "b-warn"),
    AuthorizationStatus.INTERNAL_ONLY:        ("INTERNAL ONLY",        "b-accent"),
    AuthorizationStatus.REAUTHORIZE:          ("REAUTHORIZE",          "b-risk"),
    AuthorizationStatus.REAUTHORIZE_REQUIRED: ("REAUTHORIZE REQUIRED", "b-risk"),
    AuthorizationStatus.SYNTHETIC_ONLY:       ("SYNTHETIC ONLY",       "b-muted"),
    AuthorizationStatus.PROHIBITED:           ("PROHIBITED",           "b-risk"),
    AuthorizationStatus.UNKNOWN:              ("UNKNOWN",              "b-muted"),
}

AUTH_STATUS_ZH: dict[AuthorizationStatus, str] = {
    AuthorizationStatus.ALLOWED:              "已获授权",
    AuthorizationStatus.PERMITTED:            "已获许可",
    AuthorizationStatus.CONDITIONAL:          "有条件通过",
    AuthorizationStatus.INTERNAL_ONLY:        "仅限内部使用",
    AuthorizationStatus.REAUTHORIZE:          "需重新授权",
    AuthorizationStatus.REAUTHORIZE_REQUIRED: "需重新授权",
    AuthorizationStatus.SYNTHETIC_ONLY:       "仅供示例参考",
    AuthorizationStatus.PROHIBITED:           "已被明确禁止",
    AuthorizationStatus.UNKNOWN:              "状态未知",
}


def badge(text: str, cls: str = "b-muted") -> str:
    return f'<span class="m-badge {cls}">{text}</span>'


def step_header(num: str, zh: str, title: str, subtitle: str = "") -> None:
    """Render a full-width cinematic step heading."""
    sub_html = (
        f'<div style="font-family:Inter,sans-serif;font-size:.84rem;'
        f'font-weight:300;color:rgba(232,228,220,.52);margin-top:.6rem;'
        f'letter-spacing:.02em;line-height:1.7;max-width:560px;'
        f'margin-left:auto;margin-right:auto;">{subtitle}</div>'
        if subtitle else ""
    )
    st.markdown(
        f'<div style="text-align:center;padding:1.4rem 1rem 1.2rem;">'
        f'<div style="font-family:\'JetBrains Mono\',monospace;font-size:.58rem;'
        f'letter-spacing:.28em;color:rgba(232,228,220,.38);'
        f'text-transform:uppercase;margin-bottom:.7rem;">{num} / {zh}</div>'
        f'<div style="font-family:\'Cormorant Garamond\',serif;'
        f'font-size:clamp(1.8rem,4vw,2.6rem);font-weight:300;'
        f'color:rgba(232,228,220,.97);line-height:1.25;'
        f'text-shadow:0 0 80px rgba(140,180,240,.4);">{title}</div>'
        f'{sub_html}</div>',
        unsafe_allow_html=True,
    )


_VIOLATION_ZH: dict[str, str] = {
    "publication": "公开发布",
    "public_release": "公开发布",
    "public_distribution": "公开传播",
    "ai_inference": "AI 推断内容",
    "inference": "AI 推断",
    "identity": "身份信息",
    "identity_disclosure": "身份披露",
    "downstream_reuse": "后续复用",
    "reuse": "后续复用",
    "model_training": "模型训练",
    "commercial": "商业用途",
    "advertising": "广告用途",
    "external_sharing": "外部传播",
    "public_audience": "公开受众",
    "universal_representation": "未授权的普遍性代言",
    "ai_processing": "AI 处理",
}

_ACTION_ZH: dict[str, str] = {
    "Do not publish without new authorization.": "获得新授权前，请停止公开发布。",
    "Add required disclosures before use.": "使用前请补充必要的披露声明。",
    "Remove personal identifiers before sharing.": "分享前请删除所有个人身份信息。",
    "Obtain explicit consent for AI inference.": "请就 AI 推断内容获取明确的知情同意。",
    "Restrict access to internal team only.": "请将访问权限限制为仅限内部团队。",
    "Do not use for AI model training.": "请勿将此数据用于 AI 模型训练。",
    "Confirm audience restrictions are enforced.": "请确认受众限制措施已落实执行。",
    "Obtain proper authorization for public release.": "请就公开发布取得正式授权。",
    "Add required disclosures.": "请补充必要的披露声明。",
    "Reauthorize for public use.": "请重新取得公开使用授权。",
}


def zh_violation(v: str) -> str:
    return _VIOLATION_ZH.get(v.strip(), v)


def zh_action(a: str) -> str:
    exact = _ACTION_ZH.get(a.strip())
    if exact:
        return exact
    for en, zh in _ACTION_ZH.items():
        if en.rstrip(".") in a or a.rstrip(".") in en:
            return zh
    # Generic fallback: handle "Obtain proper authorization for X." pattern
    if a.startswith("Obtain proper authorization for "):
        key = a[len("Obtain proper authorization for "):].rstrip(".")
        return "请就「" + zh_violation(key) + "」取得正式授权。"
    return a  # last resort: keep original


def suggest_revision(cluster_label: str, is_procedural: bool, is_salient: bool) -> str:
    if "申诉" in cluster_label:
        return '恢复"误判后的申诉机制"。'
    if "退出" in cluster_label:
        return '不要把"有条件支持"写成无条件支持，补回退出权。'
    if "门禁" in cluster_label:
        return "明确存在反对使用门禁数据的参与者。"
    if "标签" in cluster_label:
        return "补充标签化可能造成的严重后果。"
    if is_procedural:
        return "补入程序性诉求，并说明其不是普通偏好。"
    if is_salient:
        return "补入少数但重要的权利或风险观点。"
    return "在总结中补充该主题，或说明为何未覆盖。"


def final_status_sentence(status: FinalStatus) -> str:
    mapping = {
        FinalStatus.ALLOWED:
            "审计通过。这次代言符合授权范围，可按既定方式使用。",
        FinalStatus.CONDITIONAL:
            "有条件通过。这份总结可用于内部分析，但公开前需恢复被遗漏意见并重新确认授权。",
        FinalStatus.REAUTHORIZE:
            "当前使用方式已超出原始授权边界，必须在继续使用前重新取得授权。",
        FinalStatus.INTERNAL_ONLY:
            "该材料仅限内部使用，未经重新授权不得公开或外传。",
        FinalStatus.SYNTHETIC_ONLY:
            "该输出仅可作为合成示例，不得作为真实群体意见引用。",
        FinalStatus.PROHIBITED:
            "当前使用方式已被明确禁止，请停止使用并联系授权方。",
    }
    return mapping.get(status, "审计已完成，请查看详细结果。")
