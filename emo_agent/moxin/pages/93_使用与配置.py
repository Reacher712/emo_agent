"""Usage and configuration page."""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from portal_nav import back_home

ROOT = Path(__file__).resolve().parent.parent

st.set_page_config(page_title="墨心智愈 | 使用与配置", layout="wide")
back_home()

st.title("使用与配置")

st.subheader("一键启动")
st.code(r".\start_local.ps1 -Mode Portal", language="powershell")
st.caption("在仓库根目录运行。需要本地出图时另开终端执行 .\\start_local.ps1 -Mode Image。")

st.subheader("核心目录")
st.markdown(
    f"""
| 路径 | 说明 |
|---|---|
| `{ROOT / 'Home.py'}` | Streamlit 演示门户 |
| `{ROOT / 'pages'}` | 多页面功能入口 |
| `{ROOT / 'run_pipeline.py'}` | 情绪识别、国画生成、音乐生成闭环脚本 |
| `{ROOT / 'outputs'}` | 生成图像、音频、量表记录 |
| `{ROOT / 'deliverables'}` | 可归档演示案例 |
| `{ROOT / '.env'}` | 外部模型/API 配置 |
"""
)

st.subheader("外部能力配置")
st.markdown(
    """
- 本地复现版默认可离线展示：主页、疗愈对话、疗效评估、多模态入口、资料看板均可打开。
- 如需完整生成闭环，请先启动 Stable Diffusion WebUI/Forge API，并确认地址为 `http://127.0.0.1:7860`。
- 如需语音、音乐或大模型接口，请检查 `.env` 和 `.env.music.template` 中的密钥与服务地址。
- 应用使用仓库根目录 `.venv`；WebUI 使用独立的 Python 3.10 环境，避免混装依赖。
- 仅测试本地模型时保留“跳过音乐 API”，无需任何云端密钥。
"""
)

st.subheader("演示建议")
st.markdown(
    """
1. 先从首页进入“多模态入口”，填写一段比赛压力或情绪困扰描述。
2. 点击“送入疗愈对话”，展示融合输入如何进入对话干预。
3. 进入“疗效评估”，完成一组量表并保存，展示可追踪证据链。
4. 打开资料页，展示青年调研、赛事实证和项目资料。
"""
)

env_doc = ROOT / "env填写说明.md"
if env_doc.exists():
    with st.expander("env 填写说明"):
        st.markdown(env_doc.read_text(encoding="utf-8", errors="replace")[:12000])
