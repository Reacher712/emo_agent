"""Shared navigation helpers for the Streamlit demo."""

from __future__ import annotations

import streamlit as st


def back_home() -> None:
    """Render a compact return-home link after each page's set_page_config."""
    c1, _ = st.columns([1, 10])
    with c1:
        st.page_link("Home.py", label="返回首页")
