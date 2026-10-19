"""真·多模态入口：语音转写（可选依赖）与融合文本构建。"""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any, Tuple

try:
    import speech_recognition as _sr  # type: ignore
except Exception:
    _sr = None


def try_transcribe_audio(uploaded_file) -> Tuple[str, str]:
    """
    尝试将上传的音频转为文本。
    返回 (转写文本, 说明/错误信息)。无依赖或失败时转写为空。
    """
    if _sr is None or uploaded_file is None:
        return "", "未安装 speech_recognition 或未选择文件（可选：pip install SpeechRecognition pydub）"

    try:
        r = _sr.Recognizer()
        try:
            uploaded_file.seek(0)
        except Exception:
            pass
        raw = uploaded_file.read()
        if not raw:
            return "", "音频为空"
        suffix = Path(uploaded_file.name or "clip.wav").suffix.lower() or ".wav"
        if suffix not in {".wav", ".wave", ".flac"}:
            return (
                "",
                "演示版转写优先支持 WAV/FLAC；其它格式请先转码或仅使用文本描述",
            )
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=True) as tmp:
            tmp.write(raw)
            tmp.flush()
            with _sr.AudioFile(tmp.name) as source:
                audio = r.record(source)
        text = r.recognize_google(audio, language="zh-CN")
        return (text.strip(), "OK（Google Web Speech API，需联网）")
    except Exception as e:
        return "", f"转写失败：{e}"


def build_fused_narrative(
    *,
    text_main: str,
    transcript: str,
    transcript_note: str,
    face_self_label: str,
    face_image_captured: bool,
) -> str:
    """拼成一段可送入 EmoLLM / 对话的叙事（立项：文本+语音+面部辅助）。"""
    parts: list[str] = []
    t = (text_main or "").strip()
    if t:
        parts.append(f"【用户文字】{t}")
    tr = (transcript or "").strip()
    if tr:
        parts.append(f"【语音转写】{tr}")
    elif transcript_note and "失败" in transcript_note and not t:
        parts.append("【语音】用户上传了语音但未能转写，请结合上下文鼓励其改用文字补充。")
    fl = (face_self_label or "").strip()
    if fl and fl != "（未选择）":
        parts.append(f"【面部表情自评（辅助）】{fl}")
    parts.append(f"【面部图像】{'已采集（可作后续 FER 对接）' if face_image_captured else '未采集'}")
    if transcript_note and transcript_note != "OK（Google Web Speech API，需联网）":
        parts.append(f"【语音模块说明】{transcript_note}")
    body = "\n".join(parts)
    if not body.strip():
        return ""
    return (
        "以下是同一时刻的多模态输入汇总，请综合理解用户状态并回应，不要只重复标签：\n" + body
    )


def quick_video_frame_hint(image: Any) -> str:
    """占位：若未来接入 FER，可在此返回模型标签。"""
    if image is None:
        return ""
    return "image_ok"
