"""Method explanation page component."""
from __future__ import annotations

import streamlit as st

from ui.helpers import section_header


def render_method_page() -> None:
    section_header("METHODOLOGY", "方法说明")

    st.markdown(
        """
        <div class="mandate-card" style="margin-bottom:1.2rem;">
            <div class="mandate-label" style="margin-bottom:0.5rem;">MANDATE 是什么</div>
            <p style="color:var(--cream);font-size:0.95rem;line-height:1.8;">
            MANDATE（代言权）是一个AI代理表达审计原型系统，
            用于检查AI生成的群体意见总结是否忠实于原始材料、是否遗漏真实声音、
            是否在授权范围内使用。它不评价总结的"质量"，
            而是检查总结是否有资格代表它所代表的群体。
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    methods = [
        (
            "01  来源追踪",
            "Source Tracing",
            """将AI总结拆解为原子主张（Atomic Claims），通过TF-IDF语义相似度将每项主张
            与原始材料逐一匹配，识别：直接支持、部分支持、推断、无来源、矛盾五种状态。
            同时检查数量词（"普遍""大多数"）是否获得足够数量依据支持。""",
        ),
        (
            "02  声音地图",
            "Opinion Clustering & Coverage",
            """从原始材料中提取意见单元（Opinion Units），通过语义聚类建立原始声音地图。
            将AI总结与聚类结果对比，识别哪些主题被忠实覆盖（COVERED）、
            被弱化（WEAKENED）、被扭曲（DISTORTED）或被遗漏（OMITTED）。
            特别关注少数但具有规范重要性的意见。""",
        ),
        (
            "03  授权边界",
            "Authorization Boundary Check",
            """逐项比对原始授权条款（AuthorizationProfile）与当前实际用途（AuthorizationContext），
            识别越界操作。授权引擎基于规则文件（authorization_rules.yaml）进行判断，
            输出ALLOWED / CONDITIONAL / REAUTHORIZE / INTERNAL_ONLY / PROHIBITED五种状态。""",
        ),
        (
            "04  代言凭证",
            "Representation Passport",
            """将来源、声音、授权三个维度的审计结果汇总为代言凭证（AuditPassport），
            包含可追溯主张数、覆盖主题数、授权状态、必须完成的行动和必须增加的披露说明。
            支持JSON、Markdown、HTML三种格式导出。""",
        ),
        (
            "05  忠实修订",
            "Faithful Revision",
            """基于审计结果，生成忠实修订版本。删除无来源主张，
            修正过度数量词，补回被遗漏的重要主题，增加授权披露说明。
            修订版需经人工审核，不构成最终意见。""",
        ),
    ]

    for num_title, en_title, desc in methods:
        with st.expander(f"{num_title}  ·  {en_title}"):
            st.markdown(
                f'<p style="color:var(--cream);font-size:0.9rem;line-height:1.8;">{desc}</p>',
                unsafe_allow_html=True,
            )

    st.markdown(
        """
        <div class="method-note" style="margin-top:1.5rem;">
        <b>重要说明</b><br>
        MANDATE 是一个课程研究原型，演示用于AI代理表达审计的方法框架。
        所有分析结果均基于规则引擎和统计方法，需经人工复核。
        本工具不构成法律意见，不能替代真实授权文件和伦理审查程序。
        </div>
        """,
        unsafe_allow_html=True,
    )
