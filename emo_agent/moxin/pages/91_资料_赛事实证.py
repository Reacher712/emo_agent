"""Competition evidence wrapper."""

from __future__ import annotations

from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

from portal_nav import back_home

ROOT = Path(__file__).resolve().parent.parent
HTML_PATH = ROOT / "competition_evidence.html"

st.set_page_config(page_title="墨心智愈 | 赛事实证材料", layout="wide")
back_home()
st.title("赛事实证材料")

if HTML_PATH.exists():
    components.html(HTML_PATH.read_text(encoding="utf-8", errors="replace"), height=960, scrolling=True)
else:
    st.error(f"未找到文件：{HTML_PATH}")
