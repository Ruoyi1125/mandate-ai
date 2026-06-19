"""Input panel — three-part audit input form."""
from __future__ import annotations

from pathlib import Path

import streamlit as st

from mandate.input_loader import source_records_from_csv, source_records_from_lines
from mandate.schemas import (
    AuthorizationContext,
    AuthorizationProfile,
    AuthorityBasis,
    SourceRecord,
)
from ui.helpers import section_header


def _load_demo_sources() -> list[SourceRecord]:
    csv_path = Path("data/demo/school_ai_warning_sources.csv")
    if csv_path.exists():
        return source_records_from_csv(csv_path.read_text(encoding="utf-8-sig"))
    return []


def _load_demo_summary() -> str:
    txt_path = Path("data/demo/problematic_summary.txt")
    if txt_path.exists():
        return txt_path.read_text(encoding="utf-8").strip()
    return "学生普遍支持学校使用AI进行学业预警，主要担忧集中在隐私保护，但整体认为该系统利大于弊。"


def render_input_panel(demo_mode: bool = False) -> dict | None:
    """Render the three-part input form.

    Returns a dict with keys: source_records, summary, profile, context, project_name
    when the run button is clicked, otherwise None.
    """

    # ── Part 1: Source material ──────────────────────────────────────────────
    section_header("PART 01  SOURCES", "原始声音")

    st.markdown(
        '<p style="color:var(--muted);font-size:0.88rem;margin-bottom:1rem;">'
        "上传或粘贴需要被审计的原始群体意见——这些是AI总结所依据的真实声音。"
        "</p>",
        unsafe_allow_html=True,
    )

    input_method = st.radio(
        "输入方式",
        ["逐条粘贴", "上传 CSV"],
        horizontal=True,
        label_visibility="collapsed",
    )

    source_records: list[SourceRecord] = []

    if demo_mode:
        source_records = _load_demo_sources()
        st.info(f"已载入演示数据：{len(source_records)} 条意见，来自 {len(source_records)} 位参与者。")
    elif input_method == "逐条粘贴":
        source_text = st.text_area(
            "原始群体意见（一行一条，支持中英文）",
            placeholder=(
                "我支持AI学业预警，但前提是学生可以申诉和退出。\n"
                "我反对学校使用AI预警，因为它可能给学生贴标签。\n"
                "部分学生担心隐私泄露和数据用途扩大。\n"
                "如果只用于辅导提醒，我可以接受AI预警。"
            ),
            height=160,
            label_visibility="collapsed",
        )
        if source_text.strip():
            source_records = source_records_from_lines(source_text)
            st.caption(f"已识别 {len(source_records)} 条意见。")
    else:
        uploaded = st.file_uploader(
            "上传 CSV（至少包含 source_id, text 列；可选 participant_id, consent_id）",
            type=["csv"],
            label_visibility="collapsed",
        )
        if uploaded is not None:
            try:
                source_records = source_records_from_csv(
                    uploaded.getvalue().decode("utf-8-sig")
                )
                participants = {r.participant_id for r in source_records if r.participant_id}
                missing_pid = sum(1 for r in source_records if not r.participant_id)
                st.markdown(
                    f'<div class="mandate-card">'
                    f"✓ 已载入 <b>{len(source_records)}</b> 条意见"
                    f"&nbsp;·&nbsp;{len(participants)} 位参与者"
                    + (f"&nbsp;·&nbsp;<span style='color:var(--warn-lt)'>{missing_pid} 条缺少 participant_id</span>" if missing_pid else "")
                    + "</div>",
                    unsafe_allow_html=True,
                )
            except ValueError as err:
                st.error(str(err))

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Part 2: AI summary ───────────────────────────────────────────────────
    section_header("PART 02  AI SUMMARY", "待审AI总结")

    st.markdown(
        '<p style="color:var(--muted);font-size:0.88rem;margin-bottom:1rem;">'
        "粘贴需要被审计的AI生成总结。这可以是问卷摘要、用户反馈汇总、会议意见整理或群体立场描述。"
        "</p>",
        unsafe_allow_html=True,
    )

    default_summary = _load_demo_summary() if demo_mode else ""
    summary = st.text_area(
        "AI生成总结",
        value=default_summary,
        placeholder="粘贴AI生成的总结文本……",
        height=120,
        label_visibility="collapsed",
    )

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Part 3: Authorization ────────────────────────────────────────────────
    section_header("PART 03  AUTHORIZATION", "使用与授权")

    st.markdown(
        '<p style="color:var(--muted);font-size:0.88rem;margin-bottom:1rem;">'
        "填写原始授权范围与当前实际用途。系统将逐项比对，识别越界项目。"
        "</p>",
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns(2)

    with col1:
        st.markdown(
            '<div class="mandate-label">原始授权范围</div>',
            unsafe_allow_html=True,
        )
        represented_subject = st.text_input(
            "代表对象",
            value="anonymous students" if demo_mode else "",
            placeholder="例：匿名学生",
        )
        allow_publication = st.checkbox(
            "允许公开发布",
            value=False,
        )
        allow_ai_processing = st.checkbox("允许 AI 处理", value=True)
        allow_inference = st.checkbox("允许 AI 推断新观点", value=False)
        allow_reuse = st.checkbox("允许后续复用", value=False)
        withdrawal_supported = st.checkbox("支持撤回权", value=True)

    with col2:
        st.markdown(
            '<div class="mandate-label">当前实际用途</div>',
            unsafe_allow_html=True,
        )
        intended_purpose = st.text_input(
            "使用目的",
            value="course_research" if demo_mode else "",
            placeholder="例：课程研究",
        )
        intended_audience = st.text_input(
            "受众",
            value="course_teacher" if demo_mode else "",
            placeholder="例：课程教师",
        )
        is_public = st.checkbox("公开使用", value=False)
        includes_identity = st.checkbox("包含身份信息", value=False)
        includes_inference = st.checkbox("包含 AI 推断", value=False)
        downstream_reuse = st.checkbox("计划后续复用", value=False)

    # Provide defaults before expander so they are always defined
    project_name = "AI学业风险预警来源审计" if demo_mode else "代言审计"
    permitted_purpose = "course_research" if demo_mode else "research"
    permitted_audience = "course_teacher" if demo_mode else "internal_team"

    with st.expander("高级授权设置"):
        project_name = st.text_input(
            "项目名称",
            value=project_name,
        )
        permitted_purpose = st.text_input(
            "允许目的（原授权）",
            value=permitted_purpose,
        )
        permitted_audience = st.text_input(
            "允许受众（原授权）",
            value=permitted_audience,
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Run button ───────────────────────────────────────────────────────────
    run_disabled = not source_records or not summary.strip()

    if run_disabled:
        st.caption("请先填写原始意见和AI总结，再运行审计。")

    run_clicked = st.button(
        "▶  验证这次代言",
        type="primary",
        disabled=run_disabled,
        use_container_width=True,
    )

    if not run_clicked:
        return None

    profile = AuthorizationProfile(
        authorization_id="streamlit-audit",
        represented_subject=represented_subject or "anonymous participants",
        authorizing_party="anonymous participants",
        authority_basis=AuthorityBasis.RESEARCH_CONSENT,
        source_type="submitted_opinion",
        permitted_operations=["summarize", "audit"],
        prohibited_operations=["public_release"],
        permitted_purposes=[permitted_purpose or "research"],
        prohibited_purposes=["advertising", "commercial"],
        permitted_audiences=[permitted_audience or "internal_team"],
        prohibited_audiences=["public"] if not allow_publication else [],
        permitted_data_types=["anonymous_quotes", "summary"],
        prohibited_data_types=["identity", "student_id"],
        allow_publication=allow_publication,
        allow_ai_processing=allow_ai_processing,
        allow_rewriting=True,
        allow_inference=allow_inference,
        allow_identity_disclosure=False,
        allow_reuse=allow_reuse,
        allow_model_training=False,
        duration="course project phase",
        duration_description="Participants may withdraw future use before project completion.",
        withdrawal_supported=withdrawal_supported,
        withdrawal_method="contact course project team",
        required_disclosures=[
            "AI-assisted summary",
            "Exploratory sample; not representative of all students",
        ],
        notes="Not authorized as formal opinion of all students.",
    ).model_copy(
        update={
            "permitted_purposes": [permitted_purpose or "research"],
            "permitted_audiences": [permitted_audience or "internal_team"],
        }
    )

    context = AuthorizationContext(
        intended_operation="summarize",
        intended_purpose=intended_purpose or "research",
        intended_audience=intended_audience or "internal_team",
        is_public=is_public,
        includes_identity=includes_identity,
        uses_ai=True,
        includes_inference=includes_inference,
        allows_human_review=True,
        downstream_reuse_planned=downstream_reuse,
    )

    return {
        "project_name": project_name,
        "source_records": source_records,
        "summary": summary.strip(),
        "profile": profile,
        "context": context,
        "intended_purpose": intended_purpose or "research",
        "intended_audience": intended_audience or "internal_team",
        "is_public": is_public,
    }
