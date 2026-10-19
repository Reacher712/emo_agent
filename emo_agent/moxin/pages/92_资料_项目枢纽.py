"""Project information hub wrapper."""

from __future__ import annotations

from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

from portal_nav import back_home

ROOT = Path(__file__).resolve().parent.parent
HTML_PATH = ROOT / "project_info_hub.html"

st.set_page_config(page_title="听山 | 项目资料枢纽", layout="wide")
back_home()
st.title("项目资料枢纽")

if HTML_PATH.exists():
    components.html(HTML_PATH.read_text(encoding="utf-8", errors="replace"), height=960, scrolling=True)
else:
    st.error(f"未找到文件：{HTML_PATH}")
