"""Progress stepper bar component."""
from __future__ import annotations

import streamlit as st

STEPS = [
    ("01", "上传材料"),
    ("02", "来源验证"),
    ("03", "声音地图"),
    ("04", "授权边界"),
    ("05", "代言凭证"),
    ("06", "忠实修订"),
]


def render_stepper(current: int, has_results: bool = False) -> None:
    """Render a horizontal step progress indicator.

    current: 0-indexed step currently active (in the results section, pass 1-5).
    has_results: if True, step 0 (upload) is marked done.
    """
    parts: list[str] = []
    for i, (num, label) in enumerate(STEPS):
        if has_results and i == 0:
            dot_cls = "done"
            lbl_cls = "done"
        elif i == current:
            dot_cls = "active"
            lbl_cls = "active"
        else:
            dot_cls = ""
            lbl_cls = ""

        parts.append(
            f'<div class="mandate-step">'
            f'  <div class="mandate-step-dot {dot_cls}">{num}</div>'
            f'  <span class="mandate-step-label {lbl_cls}">{label}</span>'
            f'</div>'
        )
        if i < len(STEPS) - 1:
            parts.append('<div class="mandate-step-line"></div>')

    st.markdown(
        f'<div class="mandate-stepper">{"".join(parts)}</div>',
        unsafe_allow_html=True,
    )
