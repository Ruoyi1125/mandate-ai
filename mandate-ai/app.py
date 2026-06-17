"""Streamlit entry point for the MANDATE phase-one prototype."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import streamlit as st
from pydantic import ValidationError

from mandate.pipeline import AuditPipeline
from mandate.providers import MockProvider
from mandate.schemas import (
    AuditRequest,
    AuthorizationProfile,
    RepresentationMode,
    SourceRecord,
)


def _build_sources(raw_text: str) -> list[SourceRecord]:
    lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
    return [
        SourceRecord(
            source_id=f"source_{index + 1}",
            participant_id=None,
            text=line,
            metadata={"input_method": "streamlit_text_area"},
            consent_id=None,
        )
        for index, line in enumerate(lines)
    ]


def _passport_json(passport: Any) -> dict[str, Any]:
    return passport.model_dump(mode="json")


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
        st.info("第一阶段仅为 REAL_GROUP 提供可运行的最小审计流程。")
        return

    project_name = st.text_input("Project name", value="Demo group audit")
    source_text = st.text_area(
        "原始群体意见（一行一条）",
        value=(
            "多数参与者支持在公共服务中使用AI，但要求明确告知。\n"
            "部分参与者担心少数群体意见会被总结遗漏。\n"
            "有参与者只同意内部研究使用，不同意公开发布。"
        ),
        height=160,
    )
    summary = st.text_area(
        "AI生成总结",
        value="多数参与者支持在公共服务中使用AI，部分参与者要求明确告知。",
        height=120,
    )

    st.subheader("简单授权信息")
    represented_subject = st.text_input("Represented subject", value="workshop participants")
    intended_purpose = st.text_input("Intended purpose", value="research")
    intended_audience = st.text_input("Intended audience", value="internal_team")
    is_public = st.checkbox("Public use", value=False)
    withdrawal_supported = st.checkbox("Withdrawal supported", value=True)

    if st.button("运行审计", type="primary"):
        try:
            request = AuditRequest(
                project_name=project_name,
                representation_mode=RepresentationMode.REAL_GROUP,
                source_records=_build_sources(source_text),
                ai_generated_summary=summary,
                authorization_profile=AuthorizationProfile(
                    represented_subject=represented_subject,
                    source_type="submitted_opinion",
                    permitted_operations=["summarize", "audit"],
                    prohibited_operations=["public_release"],
                    permitted_purposes=["research", "governance_review"],
                    prohibited_purposes=["advertising"],
                    permitted_audiences=["internal_team", "course_reviewers"],
                    duration="course project phase one",
                    withdrawal_supported=withdrawal_supported,
                    required_disclosures=["Disclose source limitations."],
                ),
                intended_purpose=intended_purpose,
                intended_audience=intended_audience,
                is_public=is_public,
            )
            pipeline = AuditPipeline(
                provider=MockProvider(),
                rules_path=Path("rules/authorization_rules.yaml"),
            )
            passport = pipeline.run(request)
        except ValidationError as error:
            st.error("输入数据校验失败。")
            st.json(error.errors())
            return

        st.success("审计完成")
        st.json(_passport_json(passport))


if __name__ == "__main__":
    main()
