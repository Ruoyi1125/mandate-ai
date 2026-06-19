"""Session state management for MANDATE."""
from __future__ import annotations

from typing import Any

import streamlit as st


def init_state() -> None:
    defaults: dict[str, Any] = {
        "passport": None,
        "audit_request": None,
        "source_records": [],
        "summary_text": "",
        "active_tab": 0,
        "demo_loaded": False,
        "audit_ran": False,
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


def set_passport(passport: Any) -> None:
    st.session_state["passport"] = passport
    st.session_state["audit_ran"] = True


def get_passport() -> Any:
    return st.session_state.get("passport")


def has_results() -> bool:
    return st.session_state.get("passport") is not None


def set_source_records(records: list) -> None:
    st.session_state["source_records"] = records


def get_source_records() -> list:
    return st.session_state.get("source_records", [])


def mark_demo_loaded() -> None:
    st.session_state["demo_loaded"] = True


def is_demo_loaded() -> bool:
    return st.session_state.get("demo_loaded", False)
