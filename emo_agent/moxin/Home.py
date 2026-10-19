"""Tingshan demo portal.

Run with:
    streamlit run Home.py
"""

from __future__ import annotations

from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parent

st.set_page_config(
    page_title="听山 | 演示门户",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
<style>
section[data-testid="stSidebar"] { display: none !important; }
div.block-container { padding-top: 1.2rem !important; max-width: 1120px !important; }
.mx-hero {
  background: linear-gradient(135deg, rgba(22, 60, 111, .96), rgba(17, 94, 133, .88));
  border: 1px solid rgba(186, 230, 253, .26);
  border-radius: 14px;
  padding: 1.35rem 1.55rem;
  margin-bottom: 1.1rem;
  box-shadow: 0 14px 42px rgba(15, 23, 42, .26);
}
.mx-hero h1 { margin: 0 0 .35rem 0; color: #f8fafc; font-size: 2rem; }
.mx-hero p { margin: 0; color: #e0f2fe; font-size: 1rem; line-height: 1.65; }
.mx-card {
  border: 1px solid rgba(15, 23, 42, .12);
  border-radius: 10px;
  padding: 1rem;
  min-height: 172px;
  background: rgba(248, 250, 252, .86);
}
.mx-card h3 { margin: 0 0 .45rem 0; font-size: 1.06rem; color: #0f172a; }
.mx-card p { color: #475569; font-size: .92rem; line-height: 1.55; margin-bottom: .7rem; }
</style>
""",
    unsafe_allow_html=True,
)

st.markdown(
    """
<div class="mx-hero">
  <h1>听山</h1>
  <p>多模态情绪陪伴空间</p>
  <p>AI 国画多模态情感疗愈平台。演示版复现了“识别 - 干预 - 评估 - 归档”的核心闭环：
  用户可以进行疗愈对话、完成 PHQ-9/GAD-7/WHO-5 自评、通过文本/语音/面部线索汇总情绪输入，并查看项目资料与赛事实证。</p>
</div>
""",
    unsafe_allow_html=True,
)

st.subheader("核心功能")
cols = st.columns(3)
cards = [
    (
        "疗愈对话",
        "多轮共情对话，支持本地快速回复；配置好外部接口后，可联动情绪识别、国画生成和疗愈音乐。",
        "pages/1_疗愈对话.py",
        "进入疗愈对话",
    ),
    (
        "疗效评估",
        "内置 PHQ-9、GAD-7、WHO-5 三类自评量表，自动生成筛查提示、建议和本地记录。",
        "pages/2_疗效评估.py",
        "进入疗效评估",
    ),
    (
        "多模态入口",
        "把文本、语音转写说明和面部自评线索融合成一段可送入对话系统的情绪叙事。",
        "pages/3_多模态入口.py",
        "进入多模态入口",
    ),
]
for col, (title, desc, page, label) in zip(cols, cards):
    with col:
        st.markdown(f'<div class="mx-card"><h3>{title}</h3><p>{desc}</p></div>', unsafe_allow_html=True)
        st.page_link(page, label=label, use_container_width=True)

st.divider()
st.subheader("资料与证据")
cols = st.columns(4)
resources = [
    ("青年调研看板", "pages/90_资料_青年调研看板.py"),
    ("赛事实证材料", "pages/91_资料_赛事实证.py"),
    ("项目资料枢纽", "pages/92_资料_项目枢纽.py"),
    ("使用与配置", "pages/93_使用与配置.py"),
]
for col, (label, page) in zip(cols, resources):
    with col:
        st.page_link(page, label=label, use_container_width=True)

st.divider()
st.subheader("本地复现状态")
checks = {
    "对话入口": ROOT / "demo_frontend.py",
    "疗效记录模块": ROOT / "efficacy_store.py",
    "多模态模块": ROOT / "multimodal_input.py",
    "项目背景图": ROOT / "背景.jpeg",
    "青年调研看板": ROOT / "youth_survey_dashboard.html",
    "赛事实证材料": ROOT / "competition_evidence.html",
}
rows = []
for name, path in checks.items():
    rows.append({"模块": name, "状态": "可用" if path.exists() else "缺失", "路径": str(path)})
st.dataframe(rows, hide_index=True, use_container_width=True)

st.caption("在仓库根目录启动：.\\start_local.ps1 -Mode Portal；本地出图服务：.\\start_local.ps1 -Mode Image")
