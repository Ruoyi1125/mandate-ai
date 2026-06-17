"""Streamlit entry point for the MANDATE source tracing prototype."""

from __future__ import annotations

from pathlib import Path
from typing import Any

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
    ClaimEvidenceBundle,
    CoverageStatus,
    RepresentationMode,
    SupportStatus,
)

STATUS_LABELS = {
    SupportStatus.DIRECTLY_SUPPORTED: "直接支持",
    SupportStatus.PARTIALLY_SUPPORTED: "部分支持",
    SupportStatus.INFERRED: "推断",
    SupportStatus.UNSUPPORTED: "无来源",
    SupportStatus.CONTRADICTED: "矛盾",
}

COVERAGE_LABELS = {
    CoverageStatus.COVERED: "忠实覆盖",
    CoverageStatus.WEAKENED: "被弱化",
    CoverageStatus.DISTORTED: "被扭曲",
    CoverageStatus.OMITTED: "被遗漏",
}


def _default_profile(
    represented_subject: str,
    withdrawal_supported: bool,
    allow_publication: bool,
    allow_ai_processing: bool,
    allow_inference: bool,
    allow_reuse: bool,
) -> AuthorizationProfile:
    return AuthorizationProfile(
        authorization_id="streamlit-demo-authorization",
        represented_subject=represented_subject,
        authorizing_party="anonymous participants",
        authority_basis=AuthorityBasis.RESEARCH_CONSENT,
        source_type="submitted_opinion",
        permitted_operations=["summarize", "audit"],
        prohibited_operations=["public_release"],
        permitted_purposes=["research", "governance_review"],
        prohibited_purposes=["advertising", "commercial"],
        permitted_audiences=["internal_team", "course_reviewers"],
        prohibited_audiences=["public"],
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
    )


def _render_bundle(bundle: ClaimEvidenceBundle) -> None:
    status = STATUS_LABELS[bundle.final_support_status]
    st.markdown(f"#### {bundle.claim.claim_id}: {bundle.claim.text}")
    st.write(f"支持状态：**{status}**")
    if bundle.claim.quantifier:
        st.write(f"识别到数量/程度词：`{bundle.claim.quantifier}`")
    if bundle.quantifier_assessment:
        st.caption(bundle.quantifier_assessment.explanation)

    st.write("来源证据")
    for match in bundle.candidate_matches:
        st.markdown(
            f"- #{match.rank} `{match.source_id}` "
            f"相关度 {match.similarity_score:.3f} / "
            f"{STATUS_LABELS[match.support_status]}：{match.source_text}"
        )
        st.caption(match.explanation)

    if bundle.warnings:
        st.warning("\n".join(f"- {warning}" for warning in bundle.warnings))


def _passport_json(passport: Any) -> dict[str, Any]:
    return passport.model_dump(mode="json")


def _suggest_revision(label: str, is_procedural: bool, is_salient: bool) -> str:
    if "申诉" in label:
        return "恢复“误判后的申诉机制”。"
    if "退出" in label:
        return "不要把“有条件支持”写成无条件支持，补回退出权。"
    if "门禁" in label:
        return "明确存在反对使用门禁数据的参与者。"
    if "标签" in label:
        return "补充标签化可能造成的严重后果。"
    if is_procedural:
        return "补入程序性诉求，并说明其不是普通偏好。"
    if is_salient:
        return "补入少数但重要的权利或风险观点。"
    return "在总结中补充该主题，或说明为何未覆盖。"


def main() -> None:
    st.set_page_config(page_title="MANDATE | 代言权", layout="wide")
    st.title("MANDATE | 代言权")
    st.caption("AI代理表达的来源、代表性与授权审计系统")

    mode = st.selectbox(
        "Representation mode",
        options=[mode.value for mode in RepresentationMode],
        index=1,
    )

    if mode != RepresentationMode.REAL_GROUP.value:
        st.info("本轮仅实现 REAL_GROUP 来源追踪审计。")
        return

    project_name = st.text_input("Project name", value="AI学业风险预警来源审计")
    input_method = st.radio("原始意见输入方式", ["逐行输入", "上传CSV"], horizontal=True)
    source_records = []
    if input_method == "逐行输入":
        source_text = st.text_area(
            "原始群体意见（一行一条）",
            value=(
                "我支持AI学业预警，但前提是学生可以申诉和退出。\n"
                "我反对学校使用AI预警，因为它可能给学生贴标签。\n"
                "部分学生担心隐私泄露和数据用途扩大。\n"
                "如果只用于辅导提醒，我可以接受AI预警。"
            ),
            height=180,
        )
        source_records = source_records_from_lines(source_text)
    else:
        uploaded = st.file_uploader(
            "上传CSV，至少包含 source_id,text，可选 participant_id,consent_id",
            type=["csv"],
        )
        if uploaded is not None:
            try:
                source_records = source_records_from_csv(uploaded.getvalue().decode("utf-8-sig"))
            except ValueError as error:
                st.error(str(error))

    summary = st.text_area(
        "AI生成总结",
        value="学生普遍支持学校使用AI进行学业预警，主要担忧集中在隐私保护，但整体认为该系统利大于弊。",
        height=120,
    )

    st.subheader("简单授权信息")
    represented_subject = st.text_input("Represented subject", value="anonymous students")
    permitted_purpose = st.text_input("允许目的", value="research")
    permitted_audience = st.text_input("允许受众", value="internal_team")
    allow_publication = st.checkbox("允许公开发布", value=False)
    allow_ai_processing = st.checkbox("允许AI处理", value=True)
    allow_inference = st.checkbox("允许AI推断新态度", value=False)
    allow_reuse = st.checkbox("允许后续复用", value=False)
    withdrawal_supported = st.checkbox("Withdrawal supported", value=True)
    st.subheader("当前实际用途")
    intended_purpose = st.text_input("Intended purpose", value="research")
    intended_audience = st.text_input("Intended audience", value="internal_team")
    is_public = st.checkbox("Public use", value=False)
    includes_identity = st.checkbox("包含身份信息", value=False)
    includes_inference = st.checkbox("包含AI推断", value=False)
    downstream_reuse = st.checkbox("计划后续复用", value=False)

    if st.button("验证代言依据", type="primary"):
        try:
            request = AuditRequest(
                project_name=project_name,
                representation_mode=RepresentationMode.REAL_GROUP,
                source_records=source_records,
                ai_generated_summary=summary,
                authorization_profile=_default_profile(
                    represented_subject=represented_subject,
                    withdrawal_supported=withdrawal_supported,
                    allow_publication=allow_publication,
                    allow_ai_processing=allow_ai_processing,
                    allow_inference=allow_inference,
                    allow_reuse=allow_reuse,
                ).model_copy(
                    update={
                        "permitted_purposes": [permitted_purpose],
                        "permitted_audiences": [permitted_audience],
                    }
                ),
                authorization_context=AuthorizationContext(
                    intended_operation="summarize",
                    intended_purpose=intended_purpose,
                    intended_audience=intended_audience,
                    is_public=is_public,
                    includes_identity=includes_identity,
                    uses_ai=True,
                    includes_inference=includes_inference,
                    allows_human_review=True,
                    downstream_reuse_planned=downstream_reuse,
                ),
                intended_purpose=intended_purpose,
                intended_audience=intended_audience,
                is_public=is_public,
            )
            passport = AuditPipeline(
                provider=MockProvider(),
                rules_path=Path("rules/authorization_rules.yaml"),
            ).run(request)
        except (ValidationError, ValueError, TypeError) as error:
            st.error(f"审计无法运行：{error}")
            return

        st.success("来源追踪完成")
        trace = passport.source_trace_result
        if trace is None:
            st.error("未生成来源追踪结果。")
            return

        if trace.warnings:
            st.info("\n".join(f"- {warning}" for warning in trace.warnings))

        st.subheader("授权边界")
        auth = passport.authorization_assessment
        if auth is not None:
            st.write(f"授权状态：**{auth.authorization_status.value}**")
            st.write("已允许范围：" + (", ".join(auth.matched_permissions) or "未确认"))
            st.write("当前越界项：" + (", ".join(auth.violated_restrictions) or "无"))
            st.write("缺失信息：" + (", ".join(auth.missing_information) or "无"))
            st.write("必要披露：" + (", ".join(auth.required_disclosures) or "无"))

        st.subheader("A. 总结主张 / B. 支持状态 / C. 来源证据 / D. 风险提示")
        for bundle in trace.evidence_bundles:
            _render_bundle(bundle)

        unsupported = [
            bundle
            for bundle in trace.evidence_bundles
            if bundle.final_support_status == SupportStatus.UNSUPPORTED
        ]
        if unsupported:
            st.subheader("E. 无来源主张")
            for bundle in unsupported:
                st.error(f"{bundle.claim.claim_id}: {bundle.claim.text}")

        omission = passport.omission_result
        if omission is not None:
            if omission.warnings:
                st.info("\n".join(f"- {warning}" for warning in omission.warnings))

            st.subheader("A. 原始声音地图")
            for cluster in omission.clusters:
                stance = ", ".join(
                    f"{key}:{value}" for key, value in cluster.stance_distribution.items()
                )
                st.markdown(
                    f"**{cluster.label}** · 人数 {cluster.unique_participant_count} · "
                    f"立场 {stance or '未标注'} · "
                    f"{'少数但重要' if cluster.is_minority else '非少数主题'} · "
                    f"{'程序性诉求' if cluster.is_procedural else '一般主题'}"
                )
                st.caption(" / ".join(cluster.representative_quotes[:2]))

            st.subheader("B. 总结覆盖地图")
            cluster_lookup = {cluster.cluster_id: cluster for cluster in omission.clusters}
            for assessment in omission.coverage_assessments:
                cluster = cluster_lookup[assessment.cluster_id]
                st.write(
                    f"{cluster.label}: **{COVERAGE_LABELS[assessment.status]}** "
                    f"(相似度 {assessment.semantic_similarity:.3f})"
                )
                st.caption(assessment.explanation)

            lost = [
                item
                for item in omission.coverage_assessments
                if item.status == CoverageStatus.OMITTED
            ]
            lost.sort(
                key=lambda item: (
                    not item.is_normatively_salient,
                    item.cluster_id not in omission.procedural_cluster_ids,
                    item.participant_count * -1,
                )
            )
            st.subheader("C. VOICES LOST IN SUMMARY")
            if not lost:
                st.success("未发现完全消失的真实原始主题。")
            for item in lost:
                cluster = cluster_lookup[item.cluster_id]
                st.error(
                    f"{cluster.label} · 涉及 {item.participant_count} 人 · "
                    f"{'少数主题' if item.is_minority else '非少数主题'}"
                )
                st.write("为什么重要：" + ("、".join(cluster.salience_reasons) or "低频普通主题"))
                for source_id, quote in zip(cluster.source_ids, cluster.representative_quotes, strict=False):
                    st.markdown(f"- `{source_id}` {quote}")
                st.caption(_suggest_revision(cluster.label, cluster.is_procedural, cluster.is_normatively_salient))

            st.subheader("D. 修改建议")
            suggestions = [
                _suggest_revision(
                    cluster_lookup[item.cluster_id].label,
                    cluster_lookup[item.cluster_id].is_procedural,
                    cluster_lookup[item.cluster_id].is_normatively_salient,
                )
                for item in lost
            ]
            if any(
                item.status in {CoverageStatus.WEAKENED, CoverageStatus.DISTORTED}
                for item in omission.coverage_assessments
            ):
                suggestions.append("检查是否把强烈反对写成轻微担忧，或把条件支持写成无条件支持。")
            for suggestion in list(dict.fromkeys(suggestions)):
                st.markdown(f"- {suggestion}")

        st.subheader("代言凭证")
        st.markdown(
            f"""
            - 来源：{passport.traceable_claim_count}/{passport.claim_count} 个主张可追溯
            - 代表性：覆盖 {len(passport.covered_clusters)}/{passport.cluster_count} 个主题
            - 授权：{passport.authorization_status.value}
            - 最终状态：**{passport.final_status.value}**
            """
        )
        if passport.required_actions:
            st.warning("\n".join(f"- {item}" for item in passport.required_actions))

        st.subheader("修订工作台")
        revision = passport.revision_result
        left, right = st.columns(2)
        with left:
            st.markdown("**原AI总结**")
            st.write(summary)
        with right:
            st.markdown("**MANDATE忠实修订版**")
            st.write(revision.revised_summary if revision else "未生成修订。")
        if revision:
            st.caption(
                "删除无来源主张：" + ", ".join(revision.removed_claims)
                + " | 修正主张：" + ", ".join(revision.modified_claims)
                + " | 补回主题：" + ", ".join(revision.restored_clusters)
            )

        with st.expander("结构化 AuditPassport JSON"):
            st.json(_passport_json(passport))
        exporter = PassportExporter()
        st.download_button("下载JSON", exporter.to_json(passport), file_name="mandate_passport.json")
        st.download_button("下载Markdown", exporter.to_markdown(passport), file_name="mandate_passport.md")
        st.download_button("下载HTML", exporter.to_html(passport), file_name="mandate_passport.html")


if __name__ == "__main__":
    main()
