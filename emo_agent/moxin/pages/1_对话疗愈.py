"""Backward-compatible entry for the old chat page name."""

from __future__ import annotations

import streamlit as st

st.set_page_config(page_title="墨心智愈 | 疗愈对话", layout="wide")
try:
    st.switch_page("pages/1_疗愈对话.py")
except Exception:
    st.page_link("pages/1_疗愈对话.py", label="进入疗愈对话", use_container_width=True)
