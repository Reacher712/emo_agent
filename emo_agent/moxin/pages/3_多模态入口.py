"""Multimodal input demo page."""

from __future__ import annotations

import streamlit as st

from portal_nav import back_home

st.set_page_config(page_title="听山 | 多模态入口", layout="wide")
back_home()

st.title("多模态情绪入口")
st.caption("把文本、语音线索和面部自评合成为一段情绪叙事，再送入疗愈对话。")

left, right = st.columns(2)
with left:
    text_main = st.text_area(
        "文本描述",
        placeholder="例如：最近准备比赛压力很大，晚上睡不着，白天又很难集中注意力。",
        height=150,
    )
    audio_file = st.file_uploader("语音文件（可选）", type=["wav", "mp3", "m4a", "flac"])
    audio_note = ""
    if audio_file is not None:
        audio_note = f"用户上传了语音文件：{audio_file.name}。当前复现版先记录语音线索，可后续接入 ASR 转写。"
        st.success(audio_note)

with right:
    face_label = st.selectbox(
        "面部/状态自评（辅助线索）",
        ["未选择", "平静", "紧张/警觉", "低落/疲惫", "愉悦/放松", "混合状态"],
    )
    photo = st.camera_input("拍摄一帧表情（可选）")
    if photo is not None:
        st.success("已采集一帧图像，可作为后续表情识别接口的输入。")

parts: list[str] = []
if text_main.strip():
    parts.append(f"用户文字：{text_main.strip()}")
if audio_note:
    parts.append(f"语音线索：{audio_note}")
if face_label != "未选择":
    parts.append(f"面部/状态自评：{face_label}")
if photo is not None:
    parts.append("面部图像：已采集，待后续 FER 模型分析。")

fused = ""
if parts:
    fused = "以下是同一时刻的多模态情绪输入，请综合理解用户状态并给出温和回应：\n" + "\n".join(parts)

st.divider()
st.text_area("融合预览", value=fused, height=220, disabled=True)

col1, col2 = st.columns([1, 3])
with col1:
    if st.button("送入疗愈对话", type="primary", use_container_width=True):
        if not fused.strip():
            st.error("请至少填写一种输入。")
        else:
            st.session_state["pending_chat_text"] = fused
            st.switch_page("pages/1_疗愈对话.py")
with col2:
    st.info("复现版已保留接口位置：语音可接 ASR，图像可接 FER，融合文本可进入 EmoLLM。")
