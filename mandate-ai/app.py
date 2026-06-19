"""
MANDATE — AI代理表达的来源、代表性与授权审计系统

Architecture:
  mode = 'hero'  → full-screen animated landing page
  mode = 'app'   → step-based immersive workflow (step 1-11)

Every screen after the hero still has the live canvas background
thanks to atmosphere.inject_atmosphere() using the same-origin
iframe trick to paint into window.parent.document.
"""
from __future__ import annotations

from pathlib import Path

import streamlit as st
from pydantic import ValidationError

from mandate.input_loader import source_records_from_csv, source_records_from_lines
from mandate.passport_generator import PassportExporter
from mandate.pipeline import AuditPipeline
from mandate.providers import MockProvider
from mandate.schemas import (
    AuditRequest,
    AuthorizationContext,
    AuthorizationProfile,
    AuthorityBasis,
    CoverageStatus,
    FinalStatus,
    RepresentationMode,
    SupportStatus,
)
from ui.atmosphere import inject_atmosphere
from ui.helpers import (
    AUTH_STATUS_META,
    AUTH_STATUS_ZH,
    COVERAGE_BADGE,
    COVERAGE_CARD,
    COVERAGE_LABEL,
    FINAL_STATUS_META,
    FINAL_STATUS_ZH,
    SUPPORT_BADGE,
    SUPPORT_LABEL,
    badge,
    final_status_sentence,
    step_header,
    suggest_revision,
    zh_action,
    zh_violation,
)
from ui.state import get_passport, has_results, init_state, mark_demo_loaded, set_passport
from components.hero import render_hero
import streamlit.components.v1 as _components

# ─── CSS for hero mode: hide ALL Streamlit chrome ──────────────────────────
_HERO_CHROME_HIDE = """<style>
header,footer,#MainMenu,[data-testid="stHeader"] { display:none !important; }
.block-container { padding:0 !important; max-width:100% !important; }
[data-testid="stAppViewContainer"],[data-testid="stMain"],
section[data-testid="stMain"]>div {
  background:transparent !important; background-color:transparent !important;
  padding:0 !important;
}
iframe { border:none !important; display:block; }
</style>"""


# ═══════════════════════════════════════════════════════════════════════════
# STEP PAGES
# ═══════════════════════════════════════════════════════════════════════════

def _nav(back_step: int | None, forward_label: str = "下一步 →",
         forward_disabled: bool = False, forward_primary: bool = False) -> bool:
    """Bottom navigation bar. Returns True when forward is clicked."""
    st.markdown("<div style='height:3rem;'></div>", unsafe_allow_html=True)
    cols = st.columns([1, 3, 1])
    with cols[0]:
        if back_step is not None:
            if st.button("← 返回", key=f"back_{back_step}"):
                st.session_state["step"] = back_step
                st.rerun()
        else:
            # First step — offer a way back to the landing page
            if st.button("← 主页", key="back_to_hero"):
                for k in ["step", "mode", "demo_mode", "_src_records", "_src_text",
                          "_src_textarea", "_summary", "last_summary", "last_profile", "last_context"]:
                    st.session_state.pop(k, None)
                st.session_state.pop("passport", None)
                st.session_state["mode"] = "hero"
                st.rerun()
    with cols[2]:
        clicked = st.button(
            forward_label,
            key=f"fwd_{st.session_state.get('step', 0)}",
            type="primary" if forward_primary else "secondary",
            disabled=forward_disabled,
        )
    return clicked


def _progress_bar(step: int, total: int = 11) -> None:
    pct = round((step - 1) / (total - 1) * 100, 1)
    st.markdown(
        f'<div style="position:fixed;top:0;left:0;right:0;height:2px;'
        f'background:rgba(232,228,220,.07);z-index:9999;">'
        f'<div style="width:{pct}%;height:100%;'
        f'background:linear-gradient(90deg,rgba(140,180,240,.7),rgba(184,150,60,.5));'
        f'transition:width .6s ease;"></div></div>',
        unsafe_allow_html=True,
    )


def _wordmark() -> None:
    st.markdown(
        '<div style="font-family:\'JetBrains Mono\',monospace;font-size:.62rem;'
        'letter-spacing:.22em;color:rgba(232,228,220,.45);margin-bottom:.4rem;">'
        "MANDATE · 代言权</div>",
        unsafe_allow_html=True,
    )


_DEMO_GUIDES: dict[int, str] = {
    1: "已为你载入样本：某学校AI学业预警系统的真实学生意见，共24条。",
    2: "这是AI对上述学生意见的一句话总结——注意它如何将复杂声音简化。",
    3: "这份问卷的采集协议：匿名学生意见，仅供课程研究，不允许公开发布。",
    4: "MANDATE 正在逐条拆解AI总结，与原始24条意见逐一比对。",
    5: "审计完成。这里是来源可追溯性、代表性覆盖和授权三个维度的综合结论。",
    6: "AI总结中的每项主张是否有原始学生意见支撑？展开查看证据。",
    7: "原始意见涉及哪些主题？AI总结覆盖了哪些，遗漏了哪些？",
    8: "这些学生声音在AI总结中完全消失——没有任何形式的提及。",
    9: "核查：AI总结的当前使用方式，是否超出了匿名采集时获得的授权边界？",
    10: "这是本次审计的完整代言凭证，包含可下载的结构化数据。",
    11: "如果AI总结要如实反映全部学生声音，MANDATE 建议这样改写。",
}


def _demo_guide(step: int) -> None:
    """Floating demo context card — only shown in demo mode."""
    if not st.session_state.get("demo_mode"):
        return
    text = _DEMO_GUIDES.get(step, "")
    if not text:
        return
    st.markdown(
        f'<div style="position:fixed;bottom:6.5rem;left:1.5rem;z-index:200;max-width:230px;'
        f'opacity:0;animation:pageIn .7s ease .5s forwards;pointer-events:none;">'
        f'<div style="background:rgba(10,15,32,.9);border:1px solid rgba(140,180,240,.14);'
        f'border-radius:6px;padding:.7rem .95rem;backdrop-filter:blur(12px);">'
        f'<div style="font-family:\'JetBrains Mono\',monospace;font-size:.46rem;'
        f'letter-spacing:.2em;color:rgba(140,180,240,.5);margin-bottom:.35rem;">演 示 说 明</div>'
        f'<div style="font-family:Inter,sans-serif;font-size:.7rem;font-weight:300;'
        f'color:rgba(232,228,220,.55);line-height:1.6;">{text}</div>'
        f'</div></div>',
        unsafe_allow_html=True,
    )


def _animate_expanders() -> None:
    """Stagger-fade expanders in after Streamlit renders them."""
    _components.html("""<script>
(function() {
  function go() {
    var exps = window.parent.document.querySelectorAll('[data-testid="stExpander"]');
    exps.forEach(function(el, i) {
      if (el.dataset.anim) return;
      el.dataset.anim = '1';
      el.style.opacity = '0';
      el.style.transform = 'translateY(6px)';
      el.style.transition = 'opacity .45s ease, transform .45s ease';
      setTimeout(function() {
        el.style.opacity = '1';
        el.style.transform = 'translateY(0)';
      }, i * 70 + 100);
    });
  }
  setTimeout(go, 120);
  setTimeout(go, 500);
})();
</script>""", height=0)


# ── Step 1: Source upload ────────────────────────────────────────────────────
def page_source() -> None:
    _progress_bar(1)
    _wordmark()
    _demo_guide(1)
    step_header(
        "01", "原 声",
        "先听见<br>真实的人。",
        "上传 AI 试图总结的原始声音——它们将成为整个审计的基础。",
    )

    col_l, col_r = st.columns([3, 2], gap="large")

    with col_l:
        method = st.radio(
            "输入方式",
            ["逐条粘贴", "上传 CSV"],
            horizontal=True,
            label_visibility="collapsed",
        )

        source_records = []

        if method == "逐条粘贴":
            # Apply staged content BEFORE widget renders (Streamlit constraint)
            if "_src_staged" in st.session_state:
                st.session_state["_src_textarea"] = st.session_state.pop("_src_staged")
            elif "_src_textarea" not in st.session_state:
                st.session_state["_src_textarea"] = ""
            text = st.text_area(
                "原始意见（一行一条）",
                key="_src_textarea",
                placeholder=(
                    "我支持AI预警，但学生应该能够申诉。\n"
                    "我反对——它会给学生贴标签。\n"
                    "只要不用于处分，我可以接受。\n"
                    "门禁、消费记录不应被纳入系统。"
                ),
                height=220,
                label_visibility="collapsed",
            )
            text = st.session_state.get("_src_textarea", "")
            if text.strip():
                source_records = source_records_from_lines(text)
                st.markdown(
                    f'<div style="font-size:.73rem;color:rgba(80,160,120,.75);'
                    f'margin-top:.4rem;font-family:\'JetBrains Mono\',monospace;">'
                    f'✓ 已识别 {len(source_records)} 条意见</div>',
                    unsafe_allow_html=True,
                )
        else:
            uploaded = st.file_uploader(
                "上传 CSV（需含 source_id, text 列）",
                type=["csv"],
                label_visibility="collapsed",
            )
            if uploaded:
                try:
                    source_records = source_records_from_csv(
                        uploaded.getvalue().decode("utf-8-sig")
                    )
                    participants = {r.participant_id for r in source_records if r.participant_id}
                    st.markdown(
                        f'<div style="font-size:.73rem;color:rgba(80,160,120,.75);'
                        f'margin-top:.4rem;">✓ {len(source_records)} 条意见 · '
                        f'{len(participants)} 位参与者</div>',
                        unsafe_allow_html=True,
                    )
                except ValueError as e:
                    st.error(str(e))

        # Demo link — only show when not already in demo mode
        if not st.session_state.get("demo_mode"):
            st.markdown(
                '<div style="margin-top:1.2rem;font-size:.72rem;'
                'color:rgba(232,228,220,.55);font-family:Inter,sans-serif;">'
                '自动填入学校 AI 预警系统的真实学生意见样本</div>',
                unsafe_allow_html=True,
            )
            if st.button("⊙ 载入演示案例", key="load_demo_step1"):
                from ui.state import mark_demo_loaded
                _handle_demo_prefill()
                st.session_state["demo_mode"] = True
                mark_demo_loaded()
                st.rerun()

    with col_r:
        st.markdown(
            '<div style="padding-top:3rem;">'
            '<div style="font-family:\'Cormorant Garamond\',serif;font-size:1.15rem;'
            'font-weight:300;color:rgba(232,228,220,.58);line-height:2.8;font-style:italic;">'
            '"我支持，但前提是我能申诉。"<br>'
            '"如果被误判了呢？"<br>'
            '"我想知道谁能看到这些数据。"<br>'
            '"取决于算法是否公开。"</div>'
            '<div style="margin-top:1.6rem;font-size:.85rem;color:rgba(232,228,220,.52);'
            'letter-spacing:.05em;line-height:1.8;font-family:\'Cormorant Garamond\',serif;">'
            "— 这些声音，<br>AI的总结看见了吗？</div>"
            "</div>",
            unsafe_allow_html=True,
        )

    st.session_state["_src_records"] = source_records
    if _nav(back_step=None, forward_label="下一步 →", forward_disabled=not source_records):
        st.session_state["step"] = 2
        st.rerun()


# ── Step 2: AI summary ───────────────────────────────────────────────────────
def page_summary() -> None:
    _progress_bar(2)
    _wordmark()

    _demo_guide(2)

    # Single focal point: one big question, one input, whisper hints
    st.markdown(
        '<div style="text-align:center;padding:4rem 2rem 2.2rem;">'
        '<div style="font-family:\'JetBrains Mono\',monospace;font-size:.55rem;'
        'letter-spacing:.28em;color:rgba(232,228,220,.32);margin-bottom:1.4rem;">02 / AI 说了什么</div>'
        '<div style="font-family:\'Cormorant Garamond\',serif;'
        'font-size:clamp(2rem,4.5vw,3rem);font-weight:300;'
        'color:rgba(232,228,220,.94);line-height:1.55;'
        'text-shadow:0 0 60px rgba(140,180,240,.3);">'
        '它如何总结<br>这些声音？</div>'
        '<div style="font-family:Inter,sans-serif;font-size:.78rem;font-weight:300;'
        'color:rgba(232,228,220,.48);margin-top:1.5rem;letter-spacing:.14em;'
        'animation:pageIn 1.2s ease .5s both;">'
        '问卷摘要 &nbsp;·&nbsp; 会议纪要 &nbsp;·&nbsp; AI 群体意见汇总'
        '</div></div>',
        unsafe_allow_html=True,
    )

    _, col, _ = st.columns([1, 6, 1])
    with col:
        summary = st.text_area(
            "",
            value=st.session_state.get("_summary", ""),
            placeholder="将 AI 生成的文本粘贴于此……",
            height=260,
            label_visibility="collapsed",
        )
        st.session_state["_summary"] = summary

    st.markdown(
        '<div style="text-align:center;margin-top:.5rem;'
        'font-family:\'Cormorant Garamond\',serif;font-size:.76rem;font-style:italic;'
        'color:rgba(232,228,220,.14);letter-spacing:.05em;">'
        '这段文字将接受来源、代表性与授权的全面审计'
        '</div>',
        unsafe_allow_html=True,
    )

    if _nav(back_step=1, forward_disabled=not summary.strip()):
        st.session_state["step"] = 3
        st.rerun()


# ── Step 3: Authorization ────────────────────────────────────────────────────
def page_auth() -> None:
    _progress_bar(3)
    _wordmark()
    step_header(
        "03", "以什么名义",
        "它获得了<br>什么授权？",
        "关于原始声音的采集协议，以及当前的实际用途。",
    )

    _demo_guide(3)

    # Left: original consent | Right: current use — more editorial layout
    col1, gap_col, col2 = st.columns([5, 1, 5], gap="small")

    with col1:
        st.markdown(
            '<div style="font-family:\'Cormorant Garamond\',serif;font-size:1rem;'
            'color:rgba(232,228,220,.38);letter-spacing:.1em;margin-bottom:1.2rem;'
            'font-style:italic;">原始授权范围</div>',
            unsafe_allow_html=True,
        )
        represented = st.text_input(
            "这份材料代表谁？",
            value=st.session_state.get("_represented", "匿名参与者"),
            placeholder="例：匿名学生、社区居民……",
        )
        st.markdown('<div style="height:.4rem;"></div>', unsafe_allow_html=True)
        allow_ai = st.checkbox("允许 AI 处理和总结",
                               value=st.session_state.get("_allow_ai", True))
        allow_pub = st.checkbox("允许公开发布",
                                value=st.session_state.get("_allow_pub", False))
        allow_infer = st.checkbox("允许 AI 推断未明确表达的观点",
                                  value=st.session_state.get("_allow_infer", False))
        allow_reuse = st.checkbox("允许后续场景复用",
                                  value=st.session_state.get("_allow_reuse", False))
        withdrawal = st.checkbox("参与者持有撤回权",
                                 value=st.session_state.get("_withdrawal", True))

    with gap_col:
        st.markdown(
            '<div style="border-left:1px solid rgba(232,228,220,.07);'
            'height:320px;margin:1.5rem auto;width:1px;"></div>',
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            '<div style="font-family:\'Cormorant Garamond\',serif;font-size:1rem;'
            'color:rgba(232,228,220,.38);letter-spacing:.1em;margin-bottom:1.2rem;'
            'font-style:italic;">当前实际用途</div>',
            unsafe_allow_html=True,
        )
        purpose = st.text_input(
            "使用目的是什么？",
            value=st.session_state.get("_purpose", "课程研究"),
            placeholder="例：课程研究、政策汇报、产品决策……",
        )
        audience = st.text_input(
            "谁会看到这份总结？",
            value=st.session_state.get("_audience", "课程教师"),
            placeholder="例：课程教师、公众、决策层……",
        )
        st.markdown('<div style="height:.4rem;"></div>', unsafe_allow_html=True)
        is_public = st.checkbox("这次使用面向公众",
                                value=st.session_state.get("_is_public", False))
        incl_id = st.checkbox("总结包含身份信息",
                              value=st.session_state.get("_incl_id", False))
        incl_infer = st.checkbox("总结包含 AI 推断内容",
                                 value=st.session_state.get("_incl_infer", False))
        downstream = st.checkbox("此后计划二次使用",
                                 value=st.session_state.get("_downstream", False))

    for k, v in [
        ("_represented", represented), ("_allow_pub", allow_pub),
        ("_allow_ai", allow_ai), ("_allow_infer", allow_infer),
        ("_allow_reuse", allow_reuse), ("_withdrawal", withdrawal),
        ("_purpose", purpose), ("_audience", audience),
        ("_is_public", is_public), ("_incl_id", incl_id),
        ("_incl_infer", incl_infer), ("_downstream", downstream),
    ]:
        st.session_state[k] = v

    if _nav(back_step=2, forward_label="开始审计 ▶", forward_primary=True):
        st.session_state["step"] = 4
        st.rerun()


# ── Step 4: Processing ───────────────────────────────────────────────────────
def page_processing() -> None:
    _progress_bar(4)
    _wordmark()
    step_header(
        "04", "核 查 中",
        "MANDATE 正在<br>审阅这次代言。",
    )

    _demo_guide(4)

    if has_results():
        st.session_state["step"] = 5
        st.rerun()
        return

    # Build pipeline inputs
    src = st.session_state.get("_src_records", [])
    summary = st.session_state.get("_summary", "")

    if not src or not summary.strip():
        st.error("缺少原始意见或 AI 总结，请返回重新填写。")
        if st.button("← 返回"):
            st.session_state["step"] = 1
            st.rerun()
        return

    profile = AuthorizationProfile(
        authorization_id="mandate-audit",
        represented_subject=st.session_state.get("_represented", "anonymous participants"),
        authorizing_party="anonymous participants",
        authority_basis=AuthorityBasis.RESEARCH_CONSENT,
        source_type="submitted_opinion",
        permitted_operations=["summarize", "audit"],
        prohibited_operations=["public_release"],
        permitted_purposes=[st.session_state.get("_purpose", "research")],
        prohibited_purposes=["advertising", "commercial"],
        permitted_audiences=[st.session_state.get("_audience", "internal_team")],
        prohibited_audiences=["public"] if not st.session_state.get("_allow_pub") else [],
        permitted_data_types=["anonymous_quotes", "summary"],
        prohibited_data_types=["identity", "student_id"],
        allow_publication=st.session_state.get("_allow_pub", False),
        allow_ai_processing=st.session_state.get("_allow_ai", True),
        allow_rewriting=True,
        allow_inference=st.session_state.get("_allow_infer", False),
        allow_identity_disclosure=False,
        allow_reuse=st.session_state.get("_allow_reuse", False),
        allow_model_training=False,
        duration="project phase",
        duration_description="Participants may withdraw before project completion.",
        withdrawal_supported=st.session_state.get("_withdrawal", True),
        withdrawal_method="contact project team",
        required_disclosures=["本总结由 AI 辅助生成",
                               "探索性样本，不代表全体参与者立场"],
        notes="未经正式授权，不得作为全体参与者的代表性意见引用。",
    )

    context = AuthorizationContext(
        intended_operation="summarize",
        intended_purpose=st.session_state.get("_purpose", "research"),
        intended_audience=st.session_state.get("_audience", "internal_team"),
        is_public=st.session_state.get("_is_public", False),
        includes_identity=st.session_state.get("_incl_id", False),
        uses_ai=True,
        includes_inference=st.session_state.get("_incl_infer", False),
        allows_human_review=True,
        downstream_reuse_planned=st.session_state.get("_downstream", False),
    )

    try:
        request = AuditRequest(
            project_name="MANDATE 代言审计",
            representation_mode=RepresentationMode.REAL_GROUP,
            source_records=src,
            ai_generated_summary=summary,
            authorization_profile=profile,
            authorization_context=context,
            intended_purpose=context.intended_purpose,
            intended_audience=context.intended_audience,
            is_public=context.is_public,
        )
    except (ValidationError, ValueError) as e:
        st.error(f"输入验证失败：{e}")
        return

    steps = [
        "拆解 AI 总结中的每一项主张……",
        "为每项主张寻找原始依据……",
        "重建真实意见的完整地图……",
        "寻找在总结中消失的声音……",
        "核查授权范围……",
        "生成代言凭证……",
    ]

    with st.status("", expanded=True) as status_w:
        for s in steps:
            st.markdown(
                f'<div style="font-family:\'Cormorant Garamond\',serif;'
                f'font-size:1rem;font-weight:300;color:rgba(232,228,220,.7);">{s}</div>',
                unsafe_allow_html=True,
            )
        try:
            passport = AuditPipeline(
                provider=MockProvider(),
                rules_path=Path(__file__).parent / "rules/authorization_rules.yaml",
            ).run(request)
        except Exception as e:  # noqa: BLE001
            st.error(f"审计失败：{e}")
            status_w.update(label="失败", state="error")
            return

        st.session_state["last_summary"] = summary
        st.session_state["last_profile"] = profile
        st.session_state["last_context"] = context
        set_passport(passport)
        status_w.update(label="完成", state="complete")

    st.session_state["step"] = 5
    st.rerun()


# ── Step 5: Overview ─────────────────────────────────────────────────────────
def page_overview() -> None:
    passport = get_passport()
    if not passport:
        st.session_state["step"] = 1; st.rerun(); return

    _progress_bar(5)
    _wordmark()

    _demo_guide(5)
    _, badge_cls = FINAL_STATUS_META.get(passport.final_status, ("UNKNOWN", "b-muted"))
    label_zh = FINAL_STATUS_ZH.get(passport.final_status, "未知")
    sentence = final_status_sentence(passport.final_status)

    # Dramatic verdict — centered, breathing
    st.markdown(
        '<div style="text-align:center;padding:2.5rem 1rem 1rem;">'
        '<div style="font-family:\'JetBrains Mono\',monospace;font-size:.55rem;'
        'letter-spacing:.28em;color:rgba(232,228,220,.35);margin-bottom:1.2rem;">05 / 结 论</div>'
        '<div style="margin-bottom:1.4rem;">' + badge(label_zh, badge_cls) + '</div>'
        '<div style="font-family:\'Cormorant Garamond\',serif;'
        'font-size:clamp(1.4rem,3.2vw,2rem);font-weight:300;'
        'color:rgba(232,228,220,.88);line-height:1.65;max-width:560px;margin:0 auto;">'
        + sentence + '</div></div>',
        unsafe_allow_html=True,
    )

    # Three key metrics — animated sequential reveal, no boxes
    omission = passport.omission_result
    proc_r = omission.procedural_issue_retention_numerator if omission else 0
    proc_t = omission.procedural_issue_retention_denominator if omission else 0

    unsup_n = len(passport.unsupported_claim_ids)
    omit_n = len(passport.omitted_clusters)
    auth_ok = passport.permitted_use

    metrics = [
        (
            str(passport.traceable_claim_count),
            f"/{passport.claim_count}",
            "项主张有原始来源",
            f"{unsup_n} 项无法追溯" if unsup_n else "全部可溯源",
            "rgba(80,160,120,.75)" if not unsup_n else "rgba(176,126,48,.75)",
        ),
        (
            str(len(passport.covered_clusters)),
            f"/{passport.cluster_count}",
            "个意见主题忠实覆盖",
            f"{omit_n} 个主题完全消失" if omit_n else "无遗漏主题",
            "rgba(80,160,120,.75)" if not omit_n else "rgba(192,80,80,.75)",
        ),
        (
            "✓" if auth_ok else "✗",
            "",
            "已获授权" if auth_ok else "未获授权",
            f"{len(passport.required_actions)} 项待完成事项" if passport.required_actions else "无待完成事项",
            "rgba(80,160,120,.8)" if auth_ok else "rgba(192,80,80,.8)",
        ),
    ]

    items_html = ""
    for i, (num, denom, label, sub, color) in enumerate(metrics):
        delay = 0.18 + i * 0.2
        items_html += (
            f'<div style="display:flex;align-items:baseline;gap:1.2rem;'
            f'padding:1.4rem 0;border-bottom:1px solid rgba(232,228,220,.05);'
            f'opacity:0;animation:revealItem .65s cubic-bezier(.22,1,.36,1) {delay:.2f}s forwards;">'
            f'<div style="font-family:\'JetBrains Mono\',monospace;font-size:2.6rem;'
            f'color:{color};line-height:1;min-width:3.5rem;">{num}'
            f'<span style="font-size:1rem;color:rgba(232,228,220,.22);">{denom}</span></div>'
            f'<div style="padding-bottom:.1rem;">'
            f'<div style="font-family:Inter,sans-serif;font-size:.88rem;font-weight:300;'
            f'color:rgba(232,228,220,.62);">{label}</div>'
            f'<div style="font-size:.72rem;color:{color};margin-top:.3rem;'
            f'font-family:\'JetBrains Mono\',monospace;">{sub}</div>'
            f'</div></div>'
        )

    st.markdown(
        f'<div style="max-width:500px;margin:1.5rem auto 0;padding:0 1.5rem;">'
        f'{items_html}</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div style="text-align:center;font-family:\'Cormorant Garamond\',serif;'
        'font-size:.82rem;color:rgba(232,228,220,.50);letter-spacing:.06em;'
        'font-style:italic;margin:1.8rem 0 .5rem;'
        'opacity:0;animation:revealItem .6s ease .78s forwards;">'
        '展开各维度审计细节 →</div>',
        unsafe_allow_html=True,
    )

    if _nav(back_step=None, forward_label="来源验证 →"):
        st.session_state["step"] = 6
        st.rerun()

    if st.button("← 重新开始", key="restart_5"):
        for k in ["step", "mode", "demo_mode", "_src_records", "_src_text",
                  "_src_textarea", "_summary", "last_summary", "last_profile", "last_context"]:
            st.session_state.pop(k, None)
        st.session_state.pop("passport", None)
        st.session_state["mode"] = "hero"
        st.rerun()


# ── Step 6: Source verification ──────────────────────────────────────────────
def page_source_detail() -> None:
    passport = get_passport()
    if not passport:
        st.session_state["step"] = 5; st.rerun(); return

    _progress_bar(6)
    _wordmark()
    step_header(
        "06", "来 源 验 证",
        "每项主张，<br>有据可查吗？",
        "将 AI 总结拆解为原子主张，逐一对照原始材料。",
    )

    _animate_expanders()
    _demo_guide(6)

    trace = passport.source_trace_result
    if not trace:
        st.info("来源追踪结果不可用。"); _nav(6, "→ 声音地图"); return

    total = len(trace.evidence_bundles)
    supported_n = sum(1 for b in trace.evidence_bundles
                      if b.final_support_status in
                      {SupportStatus.DIRECTLY_SUPPORTED, SupportStatus.PARTIALLY_SUPPORTED})
    unsup_n = sum(1 for b in trace.evidence_bundles
                  if b.final_support_status == SupportStatus.UNSUPPORTED)
    q_risk_n = sum(1 for b in trace.evidence_bundles
                   if b.quantifier_assessment and not b.quantifier_assessment.supported)

    st.markdown(
        f'<div style="display:flex;gap:2.5rem;max-width:640px;margin:0 auto 1.8rem;'
        f'padding:0 .5rem;opacity:0;animation:revealItem .6s ease .1s forwards;">'
        f'<div><div style="font-size:.72rem;letter-spacing:.14em;color:rgba(232,228,220,.55);">可追溯</div>'
        f'<div style="font-family:\'JetBrains Mono\',monospace;font-size:2rem;'
        f'color:rgba(232,228,220,.88);">{supported_n}'
        f'<span style="font-size:.9rem;color:rgba(232,228,220,.38);">/{total}</span></div></div>'
        f'<div><div style="font-size:.72rem;letter-spacing:.14em;color:rgba(232,228,220,.55);">无来源</div>'
        f'<div style="font-family:\'JetBrains Mono\',monospace;font-size:2rem;'
        f'color:{("rgba(192,80,80,.9)" if unsup_n else "rgba(80,160,120,.9)")};">{unsup_n}</div></div>'
        f'<div><div style="font-size:.72rem;letter-spacing:.14em;color:rgba(232,228,220,.55);">数量词风险</div>'
        f'<div style="font-family:\'JetBrains Mono\',monospace;font-size:2rem;'
        f'color:{("rgba(176,126,48,.9)" if q_risk_n else "rgba(80,160,120,.9)")};">{q_risk_n}</div></div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    for i, bundle in enumerate(trace.evidence_bundles):
        status = bundle.final_support_status
        lbl = SUPPORT_LABEL[status]
        bcls = SUPPORT_BADGE[status]
        card_map = {
            SupportStatus.DIRECTLY_SUPPORTED: "m-card-ok",
            SupportStatus.PARTIALLY_SUPPORTED: "m-card-warn",
            SupportStatus.INFERRED: "m-card-accent",
            SupportStatus.UNSUPPORTED: "m-card-risk",
            SupportStatus.CONTRADICTED: "m-card-risk",
        }
        card_cls = card_map.get(status, "m-card")

        with st.expander(
            f"主张 {i+1}  ·  {bundle.claim.text[:55]}{'…' if len(bundle.claim.text)>55 else ''}",
            expanded=(status in {SupportStatus.UNSUPPORTED, SupportStatus.CONTRADICTED}),
        ):
            st.markdown(
                f'<div class="{card_cls}">'
                f'<div style="display:flex;justify-content:space-between;align-items:flex-start;">'
                f'<div style="font-size:.95rem;font-weight:400;color:rgba(232,228,220,.9);'
                f'max-width:75%;line-height:1.55;">{bundle.claim.text}</div>'
                f'<div style="text-align:right;">{badge(lbl, bcls)}'
                f'<div style="font-family:\'JetBrains Mono\',monospace;font-size:.68rem;'
                f'color:rgba(232,228,220,.45);margin-top:.3rem;">{status.value}</div></div>'
                f"</div>",
                unsafe_allow_html=True,
            )
            if bundle.claim.quantifier:
                q_ok = bundle.quantifier_assessment and bundle.quantifier_assessment.supported
                st.markdown(
                    f'<div style="margin-top:.6rem;font-size:.8rem;color:rgba(232,228,220,.45);">'
                    f'数量词 <code>{bundle.claim.quantifier}</code> &nbsp;'
                    + badge("已验证", "b-ok" if q_ok else "b-risk")
                    + ("" if not bundle.quantifier_assessment else
                       f'<span style="margin-left:.6rem;color:rgba(232,228,220,.58);font-size:.78rem;">'
                       f'{bundle.quantifier_assessment.explanation}</span>')
                    + "</div>",
                    unsafe_allow_html=True,
                )
            for m in bundle.candidate_matches[:3]:
                cond_note = ""
                if m.condition_preserved is False:
                    cond_note = " &nbsp;" + badge("条件已删除", "b-risk")
                st.markdown(
                    f'<div style="background:rgba(0,0,0,.18);border:1px solid rgba(232,228,220,.09);'
                    f'border-radius:4px;padding:.6rem .8rem;margin-top:.4rem;">'
                    f'<span style="font-family:\'JetBrains Mono\',monospace;font-size:.65rem;'
                    f'color:rgba(110,170,210,.8);">{m.source_id}</span>'
                    f'&nbsp;&nbsp;{badge(SUPPORT_LABEL[m.support_status], SUPPORT_BADGE[m.support_status])}{cond_note}'
                    f'<div style="margin-top:.35rem;font-size:.84rem;color:rgba(232,228,220,.7);">{m.source_text}</div>'
                    f'<div style="margin-top:.25rem;font-size:.78rem;color:rgba(232,228,220,.58);">{m.explanation}</div>'
                    f"</div>",
                    unsafe_allow_html=True,
                )
            if bundle.warnings:
                for w in bundle.warnings:
                    st.warning(w)
            st.markdown("</div>", unsafe_allow_html=True)

    if _nav(back_step=5, forward_label="→ 声音地图"):
        st.session_state["step"] = 7
        st.rerun()


# ── Step 7: Voice map ────────────────────────────────────────────────────────
def page_voice_map() -> None:
    passport = get_passport()
    if not passport:
        st.session_state["step"] = 5; st.rerun(); return

    _progress_bar(7)
    _wordmark()
    step_header(
        "07", "声 音 地 图",
        "原始材料里<br>有哪些声音？",
        "从参与者意见中重建真实主题图，检查 AI 总结覆盖了哪些、忽视了哪些。",
    )

    _animate_expanders()
    _demo_guide(7)

    omission = passport.omission_result
    if not omission:
        st.info("声音地图不可用。"); return

    cluster_lookup = {c.cluster_id: c for c in omission.clusters}

    order = {CoverageStatus.OMITTED: 0, CoverageStatus.DISTORTED: 1,
             CoverageStatus.WEAKENED: 2, CoverageStatus.COVERED: 3}
    sorted_a = sorted(
        omission.coverage_assessments,
        key=lambda a: (order.get(a.status, 9), not a.is_normatively_salient),
    )

    for assessment in sorted_a:
        cluster = cluster_lookup.get(assessment.cluster_id)
        if not cluster:
            continue
        status = assessment.status
        card_cls = COVERAGE_CARD.get(status, "m-card")
        lbl = COVERAGE_LABEL[status]
        bcls = COVERAGE_BADGE[status]

        tags = []
        if cluster.is_normatively_salient:
            tags.append(badge("规范重要性", "b-gold"))
        if cluster.is_procedural:
            tags.append(badge("程序性诉求", "b-accent"))
        if cluster.is_minority:
            tags.append(badge("少数意见", "b-muted"))
        tags_html = " ".join(tags)

        stances = " / ".join(f"{k}:{v}" for k, v in cluster.stance_distribution.items()) or "—"

        with st.expander(
            f"{cluster.label}  ·  {lbl}",
            expanded=(status in {CoverageStatus.OMITTED, CoverageStatus.DISTORTED}),
        ):
            st.markdown(
                f'<div class="{card_cls}">'
                f'<div style="display:flex;justify-content:space-between;margin-bottom:.6rem;">'
                f'<span style="font-size:1rem;font-weight:500;color:rgba(232,228,220,.9);">{cluster.label}</span>'
                f'<div>{tags_html}</div></div>'
                f'<div style="font-size:.82rem;color:rgba(232,228,220,.60);margin-bottom:.5rem;">'
                f'涉及 <b style="color:rgba(232,228,220,.88);">{cluster.unique_participant_count}</b> 位参与者'
                f'&nbsp;·&nbsp;立场 {stances}&nbsp;·&nbsp;{badge(lbl, bcls)}</div>',
                unsafe_allow_html=True,
            )
            for src_id, quote in zip(cluster.source_ids[:2],
                                      cluster.representative_quotes[:2], strict=False):
                st.markdown(
                    f'<div class="m-quote">'
                    f'<span style="font-family:\'JetBrains Mono\',monospace;font-size:.68rem;'
                    f'color:rgba(110,170,210,.82);font-style:normal;">{src_id}</span> {quote}</div>',
                    unsafe_allow_html=True,
                )
            st.markdown(
                f'<div style="font-size:.78rem;color:rgba(232,228,220,.55);margin-top:.4rem;">'
                f'{assessment.explanation}</div></div>',
                unsafe_allow_html=True,
            )

    if _nav(back_step=6, forward_label="→ 消失的声音"):
        st.session_state["step"] = 8
        st.rerun()


# ── Step 8: Lost voices (MOST DRAMATIC) ─────────────────────────────────────
def page_lost_voices() -> None:
    passport = get_passport()
    if not passport:
        st.session_state["step"] = 5; st.rerun(); return

    _progress_bar(8)
    _wordmark()

    _demo_guide(8)

    omission = passport.omission_result
    if not omission:
        st.info("消失声音分析不可用。"); return

    cluster_lookup = {c.cluster_id: c for c in omission.clusters}
    lost = [a for a in omission.coverage_assessments
            if a.status == CoverageStatus.OMITTED]
    lost.sort(key=lambda a: (
        not a.is_normatively_salient,
        a.cluster_id not in omission.procedural_cluster_ids,
        -a.participant_count,
    ))

    # Dramatic header
    n_lost = len(lost)
    sub_text = f"这 {n_lost} 个真实主题在 AI 总结中完全消失。" if lost else "未发现完全消失的原始主题。"
    st.markdown(
        f'<div style="text-align:center;padding:3rem 1rem 2rem;">'
        f'<div style="font-family:\'JetBrains Mono\',monospace;font-size:.55rem;'
        f'letter-spacing:.28em;color:rgba(192,80,80,.45);margin-bottom:1.2rem;">08 / 消 失 的 声 音</div>'
        f'<div style="font-family:\'Cormorant Garamond\',serif;'
        f'font-size:clamp(2.4rem,5.5vw,3.8rem);font-weight:300;'
        f'color:rgba(192,80,80,.82);line-height:1.35;'
        f'text-shadow:0 0 80px rgba(192,80,80,.28);">'
        f'有些声音<br>从未被听见</div>'
        f'<div style="font-family:\'Cormorant Garamond\',serif;font-size:.95rem;font-style:italic;'
        f'color:rgba(232,228,220,.52);margin-top:1rem;letter-spacing:.04em;">'
        f'{sub_text}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    if not lost:
        st.markdown(
            '<div style="text-align:center;padding:4rem 1rem;">'
            '<div style="font-family:\'Cormorant Garamond\',serif;font-size:1.4rem;'
            'color:rgba(80,160,120,.7);font-weight:300;line-height:1.8;">'
            '所有重要的学生声音<br>都在 AI 总结中得到了体现。</div>'
            '<div style="font-size:.72rem;color:rgba(80,160,120,.38);margin-top:1rem;'
            'font-family:Inter,sans-serif;letter-spacing:.08em;">这是一个值得记录的好结果。</div>'
            '</div>',
            unsafe_allow_html=True,
        )
    else:
        items_html = '<div style="max-width:860px;margin:0 auto;">'
        for i, item in enumerate(lost):
            cluster = cluster_lookup.get(item.cluster_id)
            if not cluster:
                continue
            tags = []
            if cluster.is_normatively_salient:
                tags.append(badge("规范重要性", "b-gold"))
            if cluster.is_procedural:
                tags.append(badge("程序性诉求", "b-accent"))
            tags_html = " ".join(tags)
            hint = suggest_revision(
                cluster.label, cluster.is_procedural, cluster.is_normatively_salient
            )
            delay = 0.15 + i * 0.18

            quotes_html = ""
            for src_id, quote in zip(cluster.source_ids[:3],
                                      cluster.representative_quotes[:3], strict=False):
                quotes_html += (
                    f'<div class="m-quote">'
                    f'<span style="font-family:\'JetBrains Mono\',monospace;font-size:.68rem;'
                    f'color:rgba(110,170,210,.85);font-style:normal;">{src_id}</span> {quote}</div>'
                )

            salience_html = ""
            if cluster.salience_reasons:
                salience_html = (
                    f'<div style="font-size:.8rem;color:rgba(176,126,48,.82);margin:.5rem 0;">'
                    f'重要因为：{"、".join(cluster.salience_reasons)}</div>'
                )

            items_html += (
                f'<div style="padding:1.6rem 0;border-bottom:1px solid rgba(192,80,80,.1);'
                f'opacity:0;animation:revealItem .6s cubic-bezier(.22,1,.36,1) {delay:.2f}s forwards;">'
                f'<div style="display:flex;justify-content:space-between;align-items:flex-start;'
                f'margin-bottom:.5rem;">'
                f'<div style="font-family:\'Cormorant Garamond\',serif;font-size:1.15rem;'
                f'font-weight:300;color:rgba(192,80,80,.9);">{cluster.label}</div>'
                f'<div style="display:flex;gap:.4rem;flex-wrap:wrap;">{tags_html}</div></div>'
                f'<div style="font-size:.8rem;color:rgba(192,80,80,.65);margin-bottom:.6rem;">'
                f'涉及 <b style="color:rgba(192,80,80,.9);">{item.participant_count}</b> 位参与者'
                + (" · 少数意见" if item.is_minority else "") + "</div>"
                + salience_html
                + quotes_html
                + f'<div style="margin-top:.8rem;font-size:.82rem;'
                f'color:rgba(110,170,210,.80);font-style:italic;">'
                f'建议 → {hint}</div>'
                f'</div>'
            )

        items_html += '</div>'
        st.markdown(items_html, unsafe_allow_html=True)

    if _nav(back_step=7, forward_label="→ 授权边界"):
        st.session_state["step"] = 9
        st.rerun()


# ── Step 9: Authorization boundary ──────────────────────────────────────────
def page_auth_boundary() -> None:
    passport = get_passport()
    if not passport:
        st.session_state["step"] = 5; st.rerun(); return

    _progress_bar(9)
    _wordmark()
    step_header(
        "09", "授 权 边 界",
        "谁批准了<br>这次代言？",
        "逐项核查原始授权与当前用途，标注越界与缺失项。",
    )

    _demo_guide(9)

    auth = passport.authorization_assessment
    profile = st.session_state.get("last_profile")
    context = st.session_state.get("last_context")

    if auth:
        _, bcls = AUTH_STATUS_META.get(auth.authorization_status, ("UNKNOWN", "b-muted"))
        lbl_zh = AUTH_STATUS_ZH.get(auth.authorization_status, "状态未知")
        st.markdown(
            f'<div style="text-align:center;margin-bottom:1.5rem;">{badge(lbl_zh, bcls)}</div>',
            unsafe_allow_html=True,
        )

    if profile and context:
        pp = ", ".join(profile.permitted_purposes) or "未指定"
        ap = context.intended_purpose
        p_ok = any(p in ap or ap in p for p in profile.permitted_purposes) if profile.permitted_purposes else None

        pa = ", ".join(profile.permitted_audiences) or "未指定"
        aa = context.intended_audience
        a_ok = any(a in aa or aa in a for a in profile.permitted_audiences) if profile.permitted_audiences else None

        comparisons = [
            ("目的",   pp, ap,
             p_ok),
            ("受众",   pa, aa,
             a_ok),
            ("公开发布", "允许" if profile.allow_publication else "不允许",
             "是" if context.is_public else "否",
             None if profile.allow_publication is None else not (context.is_public and not profile.allow_publication)),
            ("AI 处理", "允许" if profile.allow_ai_processing else "不允许",
             "是" if context.uses_ai else "否",
             None if profile.allow_ai_processing is None else not (context.uses_ai and not profile.allow_ai_processing)),
            ("AI 推断", "允许" if profile.allow_inference else "不允许",
             "是" if context.includes_inference else "否",
             None if profile.allow_inference is None else not (context.includes_inference and not profile.allow_inference)),
            ("身份披露", "允许" if profile.allow_identity_disclosure else "不允许",
             "是" if context.includes_identity else "否",
             None if profile.allow_identity_disclosure is None else not (context.includes_identity and not profile.allow_identity_disclosure)),
            ("后续复用", "允许" if profile.allow_reuse else "不允许",
             "是" if context.downstream_reuse_planned else "否",
             None if profile.allow_reuse is None else not (context.downstream_reuse_planned and not profile.allow_reuse)),
            ("撤回权",  "支持" if profile.withdrawal_supported else "不支持",
             "已声明", True),
        ]

        # Column header
        header_html = (
            '<div style="display:flex;gap:.8rem;padding:.3rem 0;margin-bottom:.1rem;">'
            '<div style="width:5rem;"></div>'
            '<div style="flex:1;font-size:.64rem;letter-spacing:.14em;'
            'color:rgba(232,228,220,.42);font-family:\'JetBrains Mono\',monospace;">原始授权</div>'
            '<div style="width:2rem;"></div>'
            '<div style="flex:1;font-size:.64rem;letter-spacing:.14em;'
            'color:rgba(232,228,220,.42);font-family:\'JetBrains Mono\',monospace;">实际用途</div>'
            '</div>'
        )

        rows_html = ""
        for i, (label_str, permitted, actual, ok) in enumerate(comparisons):
            delay = 0.08 + i * 0.07
            if ok is None:
                icon, color = "·", "rgba(150,155,165,.55)"
            elif ok:
                icon, color = "✓", "rgba(80,160,120,.85)"
            else:
                icon, color = "✗", "rgba(192,80,80,.85)"
            rows_html += (
                f'<div style="display:flex;align-items:center;gap:.8rem;padding:.65rem 0;'
                f'border-bottom:1px solid rgba(232,228,220,.05);opacity:0;'
                f'animation:revealItem .5s cubic-bezier(.22,1,.36,1) {delay:.2f}s forwards;">'
                f'<div style="width:5rem;font-size:.66rem;letter-spacing:.1em;flex-shrink:0;'
                f'color:rgba(232,228,220,.50);font-family:\'JetBrains Mono\',monospace;">{label_str}</div>'
                f'<div style="flex:1;font-size:.86rem;color:rgba(232,228,220,.62);">{permitted}</div>'
                f'<div style="font-size:1.15rem;color:{color};width:2rem;text-align:center;'
                f'flex-shrink:0;">{icon}</div>'
                f'<div style="flex:1;font-size:.82rem;color:rgba(232,228,220,.82);">{actual}</div>'
                f'</div>'
            )

        st.markdown(
            f'<div style="max-width:680px;margin:0 auto 1rem;">'
            f'{header_html}{rows_html}</div>',
            unsafe_allow_html=True,
        )

    if auth and auth.violated_restrictions:
        rows_html = "".join(
            f"<div style='font-size:.88rem;margin-bottom:.3rem;color:rgba(232,228,220,.8);'>"
            f"· {zh_violation(v)}</div>"
            for v in auth.violated_restrictions
        )
        st.markdown(
            '<div class="m-card-risk" style="margin-top:.8rem;">'
            '<div class="m-label" style="color:rgba(192,80,80,.75);margin-bottom:.5rem;">越界项目</div>'
            + rows_html + "</div>",
            unsafe_allow_html=True,
        )

    if auth and auth.required_actions:
        rows_html = "".join(
            f"<div style='font-size:.88rem;margin-bottom:.35rem;color:rgba(232,228,220,.8);'>"
            f"{i+1}. {zh_action(a)}</div>"
            for i, a in enumerate(auth.required_actions)
        )
        st.markdown(
            '<div class="m-card-warn" style="margin-top:.6rem;">'
            '<div class="m-label" style="color:rgba(176,126,48,.75);margin-bottom:.5rem;">需要完成的事项</div>'
            + rows_html + "</div>",
            unsafe_allow_html=True,
        )

    st.markdown(
        '<div style="margin-top:1rem;font-size:.75rem;color:rgba(232,228,220,.50);'
        'font-family:Inter,sans-serif;letter-spacing:.03em;">本模块提供规则化授权边界核查，不构成正式法律意见。</div>',
        unsafe_allow_html=True,
    )

    if _nav(back_step=8, forward_label="→ 代言凭证"):
        st.session_state["step"] = 10
        st.rerun()


# ── Step 10: Passport ────────────────────────────────────────────────────────
def page_passport() -> None:
    passport = get_passport()
    if not passport:
        st.session_state["step"] = 5; st.rerun(); return

    _progress_bar(10)
    _wordmark()
    step_header(
        "10", "代 言 凭 证",
        "MANDATE<br>REPRESENTATION PASSPORT",
        "这是本次审计的结构化凭证。可下载留存或公开核查。",
    )

    _demo_guide(10)
    _, final_bcls = FINAL_STATUS_META.get(passport.final_status, ("UNKNOWN", "b-muted"))
    final_zh = FINAL_STATUS_ZH.get(passport.final_status, "未知")
    auth_lbl = AUTH_STATUS_ZH.get(passport.authorization_status, "状态未知")
    omission = passport.omission_result
    proc_r = omission.procedural_issue_retention_numerator if omission else 0
    proc_t = omission.procedural_issue_retention_denominator if omission else 0

    status_colors = {
        FinalStatus.ALLOWED: "rgba(80,160,120,.8)",
        FinalStatus.CONDITIONAL: "rgba(176,126,48,.8)",
        FinalStatus.REAUTHORIZE: "rgba(192,80,80,.8)",
        FinalStatus.INTERNAL_ONLY: "rgba(110,170,210,.8)",
        FinalStatus.PROHIBITED: "rgba(192,80,80,.8)",
        FinalStatus.SYNTHETIC_ONLY: "rgba(150,155,165,.8)",
    }
    sc = status_colors.get(passport.final_status, "rgba(150,155,165,.8)")
    auth_color = "rgba(80,160,120,.75)" if passport.permitted_use else "rgba(192,80,80,.75)"
    unsup_color = "rgba(192,80,80,.65)" if passport.unsupported_claim_ids else "rgba(80,160,120,.55)"
    omit_color = "rgba(192,80,80,.65)" if passport.omitted_clusters else "rgba(80,160,120,.55)"

    # Paper-textured passport card
    st.markdown(
        f'<div style="max-width:700px;margin:0 auto;">'
        f'<div class="m-paper-doc" style="border-top:2px solid {sc};">'
        # Header
        f'<div style="display:flex;justify-content:space-between;align-items:flex-start;'
        f'margin-bottom:1.4rem;padding-bottom:1rem;'
        f'border-bottom:1px solid rgba(205,185,140,.1);">'
        f'<div>'
        f'<div style="font-family:\'JetBrains Mono\',monospace;font-size:.72rem;'
        f'font-weight:500;letter-spacing:.16em;color:rgba(232,228,220,.82);">MANDATE</div>'
        f'<div style="font-size:.58rem;letter-spacing:.18em;'
        f'color:rgba(232,228,220,.52);margin-top:.18rem;">代 言 凭 证</div>'
        f'</div>'
        f'<div style="font-family:\'JetBrains Mono\',monospace;font-size:.66rem;'
        f'font-weight:500;letter-spacing:.1em;color:{sc};border:1px solid {sc};'
        f'background:rgba(0,0,0,.3);padding:.28em .8em;'
        f'border-radius:2px 5px 3px 2px / 4px 2px 5px 2px;">'
        f'审计状态 · {final_zh}</div>'
        f'</div>'
        # Three metric columns
        f'<div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:1.2rem;'
        f'margin-bottom:1.4rem;">'
        # Source
        f'<div>'
        f'<div style="font-size:.64rem;letter-spacing:.15em;text-transform:uppercase;'
        f'color:rgba(232,228,220,.45);margin-bottom:.4rem;">来 源</div>'
        f'<div style="font-family:\'JetBrains Mono\',monospace;font-size:1.6rem;'
        f'color:rgba(232,228,220,.88);">{passport.traceable_claim_count}'
        f'<span style="font-size:.9rem;color:rgba(232,228,220,.3);">/{passport.claim_count}</span></div>'
        f'<div style="font-size:.76rem;color:rgba(232,228,220,.48);margin-top:.3rem;">主张可追溯</div>'
        f'<div style="font-size:.72rem;color:{unsup_color};margin-top:.15rem;">'
        f'{len(passport.unsupported_claim_ids)} 个无来源主张</div>'
        f'</div>'
        # Voice
        f'<div>'
        f'<div style="font-size:.64rem;letter-spacing:.15em;text-transform:uppercase;'
        f'color:rgba(232,228,220,.45);margin-bottom:.4rem;">代 表 性</div>'
        f'<div style="font-family:\'JetBrains Mono\',monospace;font-size:1.6rem;'
        f'color:rgba(232,228,220,.88);">{len(passport.covered_clusters)}'
        f'<span style="font-size:.9rem;color:rgba(232,228,220,.3);">/{passport.cluster_count}</span></div>'
        f'<div style="font-size:.76rem;color:rgba(232,228,220,.48);margin-top:.3rem;">主题忠实覆盖</div>'
        f'<div style="font-size:.72rem;color:{omit_color};margin-top:.15rem;">'
        f'{len(passport.omitted_clusters)} 个主题被遗漏</div>'
        f'<div style="font-size:.68rem;color:rgba(232,228,220,.35);margin-top:.1rem;">'
        f'程序性诉求 {proc_r}/{proc_t}</div>'
        f'</div>'
        # Authorization
        f'<div>'
        f'<div style="font-size:.64rem;letter-spacing:.15em;text-transform:uppercase;'
        f'color:rgba(232,228,220,.45);margin-bottom:.4rem;">授 权</div>'
        f'<div style="font-size:1.1rem;font-family:\'Cormorant Garamond\',serif;'
        f'font-weight:300;color:{auth_color};margin-top:.1rem;">'
        f'{"已获授权" if passport.permitted_use else "未获授权"}</div>'
        f'<div style="font-size:.76rem;color:rgba(232,228,220,.48);margin-top:.4rem;">{auth_lbl}</div>'
        f'<div style="font-size:.72rem;color:rgba(232,228,220,.38);margin-top:.1rem;">'
        f'{len(passport.missing_authorization_information)} 项待确认</div>'
        f'</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    if passport.required_actions:
        st.markdown(
            '<div style="background:rgba(138,96,32,.08);border:1px solid rgba(138,96,32,.2);'
            'border-radius:2px 6px 4px 3px / 5px 2px 6px 2px;padding:.9rem 1.1rem;margin-bottom:.8rem;">'
            '<div style="font-size:.58rem;letter-spacing:.15em;text-transform:uppercase;'
            'color:rgba(176,126,48,.6);margin-bottom:.5rem;">必须完成</div>'
            + "".join(
                f"<div style='font-size:.84rem;margin-bottom:.3rem;color:rgba(232,228,220,.78);'>"
                f"{i+1}. {zh_action(a)}</div>"
                for i, a in enumerate(passport.required_actions)
            )
            + "</div>",
            unsafe_allow_html=True,
        )

    st.markdown("</div></div>", unsafe_allow_html=True)

    # Downloads
    st.markdown("<br>", unsafe_allow_html=True)
    exporter = PassportExporter()
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.download_button("↓ JSON", exporter.to_json(passport),
                           "mandate_passport.json", "application/json",
                           use_container_width=True)
    with c2:
        st.download_button("↓ Markdown", exporter.to_markdown(passport),
                           "mandate_passport.md", "text/markdown",
                           use_container_width=True)
    with c3:
        st.download_button("↓ HTML", exporter.to_html(passport),
                           "mandate_passport.html", "text/html",
                           use_container_width=True)
    with c4:
        with st.expander("查看 JSON"):
            st.json(passport.model_dump(mode="json"))

    if _nav(back_step=9, forward_label="→ 忠实修订"):
        st.session_state["step"] = 11
        st.rerun()


# ── Step 11: Revision diff ───────────────────────────────────────────────────
def page_revision() -> None:
    passport = get_passport()
    if not passport:
        st.session_state["step"] = 5; st.rerun(); return

    _progress_bar(11)
    _wordmark()
    step_header(
        "11", "忠 实 修 订",
        "如果要说得更诚实，<br>它应该这样写。",
        "MANDATE 根据审计结果生成了一份更忠实的版本。左边是 AI 原文，右边是修订版，下方列出了每一处改动及原因。",
    )

    _demo_guide(11)
    revision = passport.revision_result
    original = st.session_state.get("last_summary", "")

    # Build lookup maps: ID → human-readable text
    claim_map: dict[str, str] = {}
    if passport.source_trace_result:
        for bundle in passport.source_trace_result.evidence_bundles:
            claim_map[bundle.claim.claim_id] = bundle.claim.text

    cluster_map: dict[str, str] = {}
    if passport.omission_result:
        for c in passport.omission_result.clusters:
            cluster_map[c.cluster_id] = c.label

    # ── Original vs Revised side-by-side ──
    col_l, col_r = st.columns(2, gap="large")

    with col_l:
        st.markdown(
            '<div style="font-size:.65rem;letter-spacing:.18em;text-transform:uppercase;'
            'color:rgba(232,228,220,.42);margin-bottom:.8rem;">原始 AI 版本</div>',
            unsafe_allow_html=True,
        )
        import re as _re2
        _orig_parts = [s.strip() for s in _re2.split(r'(?<=[。！？])', original) if s.strip()]
        _orig_html = "".join(
            f'<div style="margin-bottom:.8rem;">{p}</div>'
            for p in (_orig_parts if _orig_parts else [original or "（未保存原始总结）"])
        )
        st.markdown(
            f'<div class="m-paper-doc" style="font-size:.95rem;line-height:1.85;'
            f'color:rgba(232,228,220,.55);font-family:\'Cormorant Garamond\',serif;'
            f'font-style:italic;">{_orig_html}</div>',
            unsafe_allow_html=True,
        )

    with col_r:
        st.markdown(
            '<div style="font-size:.65rem;letter-spacing:.18em;text-transform:uppercase;'
            'color:rgba(110,170,210,.65);margin-bottom:.8rem;">MANDATE 忠实修订版</div>',
            unsafe_allow_html=True,
        )

        # One clean disclosure line (no parsing, no duplication)
        _disc_html = (
            f'<div style="font-size:.72rem;color:rgba(232,228,220,.38);'
            f'border-bottom:1px solid rgba(232,228,220,.07);'
            f'padding-bottom:.6rem;margin-bottom:1.1rem;">'
            f'本修订版基于 {passport.source_count} 条匿名意见，由 MANDATE 审计，'
            f'为探索性样本，不代表全体参与者立场。</div>'
        )

        # Reconstruct content sentences from structured data (same logic as revision_generator.py)
        _rev_paras: list[str] = []
        if passport.omission_result:
            for _asmt in passport.omission_result.coverage_assessments:
                _cl = next(
                    (c for c in passport.omission_result.clusters
                     if c.cluster_id == _asmt.cluster_id), None
                )
                if not _cl:
                    continue
                _q = _cl.representative_quotes[0] if _cl.representative_quotes else ""
                _n = _cl.unique_participant_count
                if _asmt.status == CoverageStatus.COVERED:
                    _rev_paras.append(
                        f'当前材料中有{_n}名参与者表达了与"{_cl.label}"相关的意见。'
                    )
                elif _asmt.status in {CoverageStatus.WEAKENED, CoverageStatus.DISTORTED}:
                    _sent = f'关于"{_cl.label}"，应保留限定条件和原始强度'
                    _sent += f'，例如：{_q}' if _q else '。'
                    _rev_paras.append(_sent)
                elif (_asmt.status == CoverageStatus.OMITTED
                      and (_cl.is_normatively_salient or _cl.is_procedural)):
                    _sent = f'原始材料还包含"{_cl.label}"这一重要声音'
                    _sent += f'，例如：{_q}' if _q else '。'
                    _rev_paras.append(_sent)

        _body_html = "".join(
            f'<p style="margin-bottom:.85rem;line-height:1.85;">{p}</p>'
            for p in _rev_paras
        ) if _rev_paras else '<p style="color:rgba(232,228,220,.4);">未生成修订内容。</p>'

        st.markdown(
            f'<div class="m-paper-doc" style="border-top:2px solid rgba(110,170,210,.45);'
            f'padding:1.4rem 1.6rem;font-family:\'Cormorant Garamond\',serif;'
            f'font-size:.95rem;color:rgba(232,228,220,.9);">'
            f'{_disc_html}{_body_html}</div>',
            unsafe_allow_html=True,
        )

    # ── Change log — concise diff, disclosures consolidated into one entry ──
    if revision:
        has_changes = any([
            revision.removed_claims, revision.modified_claims,
            revision.restored_clusters, revision.added_disclosures,
        ])
        if has_changes:
            st.markdown(
                '<div style="height:2.2rem;"></div>'
                '<div style="font-size:.62rem;letter-spacing:.22em;text-transform:uppercase;'
                'color:rgba(232,228,220,.38);margin-bottom:1.2rem;text-align:center;">'
                'MANDATE 做了哪些修改</div>',
                unsafe_allow_html=True,
            )

            def _change_row(icon: str, ic: str, bg: str, border: str,
                            title: str, detail: str, reason: str) -> str:
                return (
                    f'<div style="display:flex;gap:1rem;padding:.9rem 1.1rem;'
                    f'background:{bg};border-left:2px solid {border};'
                    f'border-radius:0 5px 5px 0;margin-bottom:.55rem;">'
                    f'<div style="font-size:1.1rem;color:{ic};flex-shrink:0;width:1.5rem;'
                    f'text-align:center;line-height:1.5;">{icon}</div>'
                    f'<div style="flex:1;min-width:0;">'
                    f'<div style="font-size:.65rem;letter-spacing:.12em;text-transform:uppercase;'
                    f'color:{ic};font-family:\'JetBrains Mono\',monospace;margin-bottom:.4rem;">{title}</div>'
                    f'<div style="font-size:.92rem;color:rgba(232,228,220,.85);line-height:1.7;'
                    f'font-family:\'Cormorant Garamond\',serif;font-style:italic;">{detail}</div>'
                    f'<div style="font-size:.73rem;color:rgba(232,228,220,.48);margin-top:.3rem;'
                    f'font-family:Inter,sans-serif;line-height:1.5;">{reason}</div>'
                    f'</div></div>'
                )

            rows_html = ""
            for cid in revision.removed_claims:
                text = claim_map.get(cid, cid)
                rows_html += _change_row(
                    "✗", "rgba(192,80,80,.9)",
                    "rgba(192,80,80,.06)", "rgba(192,80,80,.35)",
                    "删除 · 无来源主张",
                    f"「{text}」",
                    "此主张在原始意见中找不到依据，已从修订版中删除。",
                )
            for cid in revision.modified_claims:
                text = claim_map.get(cid, cid)
                rows_html += _change_row(
                    "≈", "rgba(176,126,48,.9)",
                    "rgba(176,126,48,.06)", "rgba(176,126,48,.35)",
                    "修正 · 过度归纳",
                    f"「{text}」",
                    "原表述超出了来源证据的支持范围，已调整为更审慎的措辞。",
                )
            for cid in revision.restored_clusters:
                label = cluster_map.get(cid, cid)
                rows_html += _change_row(
                    "+", "rgba(110,170,210,.9)",
                    "rgba(110,170,210,.07)", "rgba(110,170,210,.3)",
                    "补入 · 被遗漏的主题",
                    label,
                    "此议题在参与者意见中有明确记录，但 AI 总结未予覆盖，现已补入修订版。",
                )
            # Consolidate all disclosures into ONE entry instead of listing each separately
            if revision.added_disclosures:
                n_disc = len(set(revision.added_disclosures))
                rows_html += _change_row(
                    "＋", "rgba(80,160,120,.9)",
                    "rgba(80,160,120,.06)", "rgba(80,160,120,.3)",
                    "新增 · 必要披露声明",
                    f"已在修订版顶部补充 {n_disc} 项授权声明",
                    "根据授权协议，使用前须附相关披露信息。",
                )

            st.markdown(
                f'<div style="max-width:780px;margin:0 auto;">{rows_html}</div>',
                unsafe_allow_html=True,
            )

        if revision.human_review_required:
            st.markdown(
                '<div style="font-size:.73rem;color:rgba(232,228,220,.38);margin-top:1.2rem;'
                'text-align:center;font-family:Inter,sans-serif;">'
                '修订版由规则引擎生成，需经人工审核后方可正式使用。</div>',
                unsafe_allow_html=True,
            )

    st.markdown("<div style='height:3rem;'></div>", unsafe_allow_html=True)
    cols = st.columns([1, 3, 1])
    with cols[0]:
        if st.button("← 返回", key="back_10_from_11"):
            st.session_state["step"] = 10
            st.rerun()
    with cols[2]:
        if st.button("返回首页", key="go_home_11", type="secondary"):
            for k in ["step", "mode", "demo_mode", "_src_records", "_src_text",
                      "_src_textarea", "_summary", "last_summary", "last_profile", "last_context"]:
                st.session_state.pop(k, None)
            st.session_state.pop("passport", None)
            st.session_state["mode"] = "hero"
            st.rerun()


# ═══════════════════════════════════════════════════════════════════════════
# ROUTING
# ═══════════════════════════════════════════════════════════════════════════

STEP_PAGES = {
    1: page_source,
    2: page_summary,
    3: page_auth,
    4: page_processing,
    5: page_overview,
    6: page_source_detail,
    7: page_voice_map,
    8: page_lost_voices,
    9: page_auth_boundary,
    10: page_passport,
    11: page_revision,
}


def _handle_demo_prefill() -> None:
    """Pre-fill session with demo data."""
    import csv as _csv
    import io as _io

    _here = Path(__file__).parent
    demo_csv = _here / "data/demo/school_ai_warning_sources.csv"
    demo_txt = _here / "data/demo/problematic_summary.txt"
    if demo_csv.exists():
        content = demo_csv.read_text("utf-8-sig")
        from mandate.input_loader import source_records_from_csv
        st.session_state["_src_records"] = source_records_from_csv(content)
        # Stage content — will be copied to _src_textarea BEFORE widget renders on next run
        reader = _csv.DictReader(_io.StringIO(content))
        lines = [r.get("text", "").strip() for r in reader if r.get("text", "").strip()]
        demo_text = "\n".join(lines)
        st.session_state["_src_staged"] = demo_text
        st.session_state["_src_text"] = demo_text
    if demo_txt.exists():
        st.session_state["_summary"] = demo_txt.read_text("utf-8").strip()
    # Demo auth defaults
    for k, v in [
        ("_represented", "anonymous students"),
        ("_allow_pub", False), ("_allow_ai", True), ("_allow_infer", False),
        ("_allow_reuse", False), ("_withdrawal", True),
        ("_purpose", "course_research"), ("_audience", "course_teacher"),
        ("_is_public", False), ("_incl_id", False),
        ("_incl_infer", False), ("_downstream", False),
    ]:
        st.session_state[k] = v


def main() -> None:
    st.set_page_config(
        page_title="MANDATE | 代言权",
        layout="wide",
        initial_sidebar_state="collapsed",
    )
    init_state()

    # Handle query-param navigation from hero buttons
    action = st.query_params.get("action", "")
    if action in ("start", "demo"):
        st.query_params.clear()
        st.session_state["mode"] = "app"
        st.session_state["step"] = 1
        if action == "demo":
            mark_demo_loaded()
            st.session_state["demo_mode"] = True
            _handle_demo_prefill()
        else:
            st.session_state["demo_mode"] = False
        st.rerun()

    mode = st.session_state.get("mode", "hero")

    if mode == "hero":
        st.markdown(_HERO_CHROME_HIDE, unsafe_allow_html=True)
        render_hero()
        return

    # App mode: inject persistent background + CSS on EVERY step
    inject_atmosphere()

    step = st.session_state.get("step", 1)
    page_fn = STEP_PAGES.get(step, page_source)
    page_fn()


if __name__ == "__main__":
    main()
