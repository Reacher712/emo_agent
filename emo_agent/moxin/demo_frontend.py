import base64
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, cast

import streamlit as st
import streamlit.components.v1 as components

from chat_state_signal import (
    MoodSnapshot,
    anxiety_level_label,
    blend_with_history,
    estimate_with_optional_llm,
)

try:
    from doubao_voice import get_reply_and_audio, get_tts_voice_options
    DOUBAO_VOICE_AVAILABLE = True
except Exception:
    DOUBAO_VOICE_AVAILABLE = False
    get_reply_and_audio = None
    get_tts_voice_options = lambda: []


DEFAULT_PROJECT_DIR = Path(r"D:\moxin")
DEFAULT_RUN_PIPELINE = DEFAULT_PROJECT_DIR / "run_pipeline.py"
DEFAULT_DELIVERABLES = DEFAULT_PROJECT_DIR / "deliverables"
# 与 A1111/Forge 默认端口、常见 SSH 转发 (-L 7860:127.0.0.1:7860) 一致；本机若用其它端口请在侧栏修改
DEFAULT_SD_API_URL = "http://127.0.0.1:7860"
DEFAULT_INIT_BG = DEFAULT_PROJECT_DIR / "背景.jpeg"
DEFAULT_INIT_AUDIO = DEFAULT_PROJECT_DIR / "outputs" / "202603411507295627771905.wav"


def _image_mime_from_path(path: Path) -> str:
    ext = path.suffix.lower()
    if ext in (".jpg", ".jpeg"):
        return "image/jpeg"
    if ext == ".png":
        return "image/png"
    if ext == ".webp":
        return "image/webp"
    return "image/png"


def _to_b64(path: Path) -> str:
    if not path.exists():
        return ""
    return base64.b64encode(path.read_bytes()).decode("utf-8")


def _load_json(path: Path) -> Optional[Dict]:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _find_case_files(case_dir: Path) -> Dict[str, Optional[Path]]:
    png = sorted(case_dir.glob("*.png"), key=lambda p: p.stat().st_mtime, reverse=True)
    wav = sorted(case_dir.glob("*.wav"), key=lambda p: p.stat().st_mtime, reverse=True)
    payload = sorted(case_dir.glob("*payload.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    return {
        "image": png[0] if png else None,
        "audio": wav[0] if wav else None,
        "payload": payload[0] if payload else None,
    }


def _quick_reply(user_text: str) -> str:
    t = user_text.strip()
    if any(k in t for k in ["焦虑", "紧张", "慌", "担心"]):
        return "我听到了你的紧张感，我们先把节奏放慢一点。你可以先做两次缓慢呼吸，然后告诉我现在最明显的身体感受。"
    if any(k in t for k in ["压力", "忙", "任务", "累"]):
        return "我理解你现在压力比较满。先不用一次解决全部，我们把注意力放在“下一步最小动作”上。"
    if any(k in t for k in ["低落", "难过", "失落"]):
        return "谢谢你愿意说出来。你现在的状态值得被温柔对待，我们先做一个小小的稳定动作。"
    if any(k in t for k in ["平静", "放松", "轻松"]):
        return "很好，你已经在靠近稳定区间了。我们继续保持这种节奏，把这份平静巩固下来。"
    return "我在认真听你说。你可以再多描述一点此刻最强烈的情绪，我会和你一起把状态慢慢拉稳。"


def _run_pipeline(user_text: str, case_name: str, sd_api_url: str, run_pipeline_file: Path) -> Dict:
    cmd = [
        sys.executable,
        str(run_pipeline_file),
        "--text",
        user_text,
        "--sd-api-url",
        sd_api_url,
        "--save-case-name",
        case_name,
        "--music-duration-sec",
        "30",
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    stdout = proc.stdout.strip()
    parsed = {}
    if stdout:
        try:
            parsed = json.loads(stdout)
        except Exception:
            lines = [ln for ln in stdout.splitlines() if ln.strip()]
            if lines:
                try:
                    parsed = json.loads(lines[-1])
                except Exception:
                    parsed = {}
    return {
        "returncode": proc.returncode,
        "stdout": stdout,
        "stderr": proc.stderr.strip(),
        "parsed": parsed,
    }


def _streamlit_chrome_dark_css() -> str:
    """覆盖 Streamlit 原生区块与 chat_input，避免浅色主题下出现大块白底。"""
    return """
        /* 主区域透明，露出 .stApp 背景图或渐变 */
        [data-testid="stAppViewContainer"] > .main .block-container {
            background-color: transparent !important;
            padding-top: 0.75rem;
            padding-bottom: 6rem;
        }
        [data-testid="stAppViewContainer"] .main {
            background-color: transparent !important;
        }
        /* 顶栏 */
        header[data-testid="stHeader"] {
            background: rgba(15,23,42,0.72) !important;
        }
        /* 页面主标题 */
        .main h1 {
            color: #f8fafc !important;
            text-shadow: 0 1px 10px rgba(0,0,0,0.5);
        }
        /* 侧边栏深色 */
        section[data-testid="stSidebar"] {
            background-color: rgba(15, 23, 42, 0.97) !important;
            border-right: 1px solid rgba(148, 163, 184, 0.22);
        }
        section[data-testid="stSidebar"] .stMarkdown p,
        section[data-testid="stSidebar"] label,
        section[data-testid="stSidebar"] span {
            color: #e2e8f0 !important;
        }
        section[data-testid="stSidebar"] h1,
        section[data-testid="stSidebar"] h2,
        section[data-testid="stSidebar"] h3 {
            color: #f1f5f9 !important;
        }
        section[data-testid="stSidebar"] input,
        section[data-testid="stSidebar"] textarea {
            color: #f1f5f9 !important;
            background-color: rgba(30, 41, 59, 0.95) !important;
        }
        /* 底部输入区：深色条 + 遮罩（兼容多版本 DOM） */
        [data-testid="stBottomBlockContainer"] {
            background: linear-gradient(180deg, transparent 0%, rgba(15, 23, 42, 0.94) 28%) !important;
        }
        [data-testid="stChatInput"] {
            background-color: rgba(30, 41, 59, 0.96) !important;
            border: 1px solid rgba(148, 163, 184, 0.45) !important;
        }
        [data-testid="stChatInput"] textarea {
            color: #f1f5f9 !important;
            background-color: transparent !important;
            caret-color: #f1f5f9 !important;
        }
        [data-testid="stChatInput"] textarea::placeholder {
            color: #94a3b8 !important;
        }
        div[data-testid="stChatInputContainer"] {
            background-color: transparent !important;
        }
        .stChatFloatingInputContainer {
            background: rgba(15, 23, 42, 0.88) !important;
        }
    """


def _render_background() -> None:
    b64 = st.session_state.get("bg_b64", "")
    bg_mime = st.session_state.get("bg_mime") or "image/png"
    if b64:
        css = f"""
        <style>
        .stApp {{
            background: linear-gradient(rgba(10,10,10,0.48), rgba(10,10,10,0.48)),
                        url("data:{bg_mime};base64,{b64}") no-repeat center center fixed;
            background-size: cover;
        }}
        .chat-wrap {{
            max-width: 900px;
            margin: 0 auto;
        }}
        .bubble {{
            padding: 12px 14px;
            border-radius: 14px;
            margin: 8px 0;
            line-height: 1.6;
            font-size: 16px;
            max-width: 76%;
            white-space: pre-wrap;
        }}
        .user {{
            margin-left: auto;
            background: rgba(32, 86, 160, 0.90);
            color: #fff;
        }}
        .assistant {{
            margin-right: auto;
            background: rgba(255, 255, 255, 0.90);
            color: #1f2937;
        }}
        .meta {{
            color:#e5e7eb;
            font-size:13px;
            margin-bottom:6px;
        }}
        {_streamlit_chrome_dark_css()}
        </style>
        """
    else:
        css = f"""
        <style>
        .stApp {{ background: linear-gradient(120deg,#0f172a,#1f2937); }}
        .chat-wrap {{ max-width: 900px; margin: 0 auto; }}
        .bubble {{
            padding: 12px 14px; border-radius: 14px; margin: 8px 0; line-height: 1.6;
            font-size: 16px; max-width: 76%; white-space: pre-wrap;
        }}
        .user {{ margin-left: auto; background: rgba(32,86,160,0.92); color:#fff; }}
        .assistant {{ margin-right: auto; background: rgba(255,255,255,0.92); color:#1f2937; }}
        .meta {{ color:#e5e7eb; font-size:13px; margin-bottom:6px; }}
        {_streamlit_chrome_dark_css()}
        </style>
        """
    st.markdown(css, unsafe_allow_html=True)


def _render_mood_sidebar() -> bool:
    """侧栏：心理状态示意；返回是否点击「生成国画与音乐」。"""
    snap = cast(Optional[MoodSnapshot], st.session_state.get("latest_mood_snapshot"))
    disp = st.session_state.get("mood_display_anxiety")
    series = st.session_state.get("mood_anxiety_series") or []

    st.subheader("心理状态示意")
    st.caption(
        "随每条用户消息更新；**文本信号推测**，非诊断。不能替代量表与面谈。"
    )

    if snap is None or disp is None:
        st.info("发送首条用户消息后，此处显示紧张/担忧负荷与情绪态势。")
    else:
        st.metric("本句 · 紧张担忧负荷（示意）", f"{snap.anxiety_0_100} / 100")
        st.metric("平滑展示（近几轮混合）", f"{int(disp)} / 100")
        st.caption("估计方式：" + ("大模型辅助" if snap.source == "llm" else "本地关键词"))

        r = min(max(int(disp), 0), 100) / 100.0
        st.progress(r)
        st.caption(f"档位：{anxiety_level_label(int(disp))}")
        st.markdown(f"**情绪态势**：{snap.mood_zh}")
        st.markdown(f"**心理激活度**：{snap.arousal_zh}")
        st.markdown(snap.summary_zh)

        if len(series) >= 2:
            st.caption("近几轮本句负荷（示意）")
            st.line_chart({"本句": series}, height=140)

    st.divider()
    st.caption("国画与音乐将综合 **最近几条用户消息** 与 **心理状态示意**（若有），偏安抚、治愈向。")
    can_heal = bool(_compose_healing_pipeline_text().strip())
    return bool(
        st.button(
            "生成新的国画背景与音乐",
            key="mx_heal_gen_sidebar",
            disabled=not can_heal,
            help="至少需有一条用户消息；有心理状态示意时更贴当前心境",
        )
    )


def _push_mood_after_user_turn(user_text: str, use_llm_mood: bool) -> None:
    snap = estimate_with_optional_llm(user_text, use_llm_mood)
    hist = list(st.session_state.get("mood_anxiety_series") or [])
    display = blend_with_history(snap, hist[-3:])
    st.session_state["latest_mood_snapshot"] = snap
    st.session_state["mood_display_anxiety"] = display
    hist.append(snap.anxiety_0_100)
    st.session_state["mood_anxiety_series"] = hist[-24:]


def _compose_healing_pipeline_text() -> str:
    """拼成送入 run_pipeline / EmoLLM 的文本：最近发言 + 当前心理状态示意 + 疗愈取向。"""
    user_msgs = [m["text"] for m in st.session_state.messages if m["role"] == "user"]
    snap = cast(Optional[MoodSnapshot], st.session_state.get("latest_mood_snapshot"))
    disp = st.session_state.get("mood_display_anxiety")
    if not user_msgs and (snap is None or disp is None):
        return ""
    blocks: list[str] = []
    if user_msgs:
        blocks.append("【我最近说的内容】\n" + "\n".join(user_msgs[-3:]))
    if snap is not None and disp is not None:
        blocks.append(
            "【心理状态线索（由对话文本自动推测，用于匹配疗愈画面与音乐；非诊断）】\n"
            f"紧张担忧示意约 {snap.anxiety_0_100}/100；经平滑后示意约 {int(disp)}/100；"
            f"情绪态势：{snap.mood_zh}；心理激活度：{snap.arousal_zh}。"
        )
    blocks.append(
        "【疗愈方向】请为我匹配最能安抚情绪、带来安全感的国画意境与舒缓疗愈音乐，"
        "整体风格温柔、留白、利于情绪沉淀与自我调节。"
    )
    return "\n\n".join(blocks)


def _healing_followup_chat_user_line() -> str:
    """生成疗愈闭环后，向大模型发起「陪我观看聆听」的请求用语（不写入消息历史）。"""
    user_msgs = [m["text"] for m in st.session_state.messages if m["role"] == "user"]
    tail = (user_msgs[-1][:300] + "…") if user_msgs and len(user_msgs[-1]) > 300 else (user_msgs[-1] if user_msgs else "")
    lines = [
        "我刚根据当前对话与心理状态示意，请求系统生成了新的国画背景与舒缓疗愈音乐。",
        "请你用温柔、安抚的口吻，邀请我安静观看画面、放慢呼吸，在音乐里待一会儿。",
    ]
    if tail:
        lines.insert(1, f"我上一段最想表达的感受是：{tail}")
    return "\n".join(lines)


def _run_healing_deliverables(
    pipeline_text: str,
    *,
    use_doubao: bool,
    use_tts: bool,
    selected_voice: Optional[str],
    run_pipeline_file: Path,
    deliverables_dir: Path,
    sd_api_url: str,
) -> None:
    """手动触发：国画 + 音乐 + 助手安抚语，并更新背景与循环音乐。"""
    case_name = f"chat_case_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    with st.spinner("正在根据当前心理状态生成国画与疗愈音乐，请稍候…"):
        result = _run_pipeline(
            user_text=pipeline_text.strip(),
            case_name=case_name,
            sd_api_url=sd_api_url.strip(),
            run_pipeline_file=run_pipeline_file,
        )

    if result["returncode"] != 0 or result["parsed"].get("status") != "success":
        msg = "本轮生成失败，我已记录日志。可改述感受后再次点击生成。"
        if result.get("parsed", {}).get("error_message"):
            msg += f"\n错误：{result['parsed']['error_message']}"
        st.session_state.messages.append({"role": "assistant", "text": msg})
        st.rerun()

    files = _find_case_files(deliverables_dir / case_name)
    payload_json = _load_json(files["payload"]) if files["payload"] else None
    sr = (payload_json or {}).get("soothing_response") or {}
    fallback_answer = sr.get("full_text") if isinstance(sr, dict) else ""
    if not fallback_answer:
        fallback_answer = (
            "我已经根据你此刻的状态，为你换上一幅更贴近心境的国画与一段舒缓音乐。"
            "请先安静看一会儿画面，跟随音乐慢慢呼吸，不必急着评价自己。"
        )
    follow_user = _healing_followup_chat_user_line()
    if get_reply_and_audio and (use_doubao or use_tts):
        history = [{"role": m["role"], "text": m["text"]} for m in st.session_state.messages]
        with st.spinner("生成安抚语" + ("并合成语音…" if use_tts else "…")):
            r = get_reply_and_audio(
                follow_user,
                history=history,
                fallback_reply=fallback_answer,
                use_doubao=use_doubao,
                use_tts=use_tts,
                voice_id=selected_voice,
            )
        answer = r["text"]
        if r.get("audio_b64"):
            st.session_state.reply_audio_b64 = r["audio_b64"]
            st.session_state.reply_audio_version += 1
    else:
        answer = fallback_answer
    st.session_state.messages.append({"role": "assistant", "text": answer})

    if files["image"] and files["image"].exists():
        st.session_state.bg_b64 = _to_b64(files["image"])
        st.session_state.bg_mime = _image_mime_from_path(files["image"])
    if files["audio"] and files["audio"].exists():
        st.session_state.current_audio_b64 = _to_b64(files["audio"])
        st.session_state.current_audio_name = files["audio"].name
        st.session_state.audio_version += 1

    st.rerun()


def _render_chat() -> None:
    st.markdown("<div class='chat-wrap'>", unsafe_allow_html=True)
    st.markdown(
        "<div class='meta'>需要时点击 <b>生成新的国画背景与音乐</b>，系统会结合你<strong>最近说的话</strong>与侧栏<strong>心理状态示意</strong>匹配安抚、治愈向的画面与音乐。</div>",
        unsafe_allow_html=True,
    )
    for item in st.session_state.messages:
        cls = "user" if item["role"] == "user" else "assistant"
        st.markdown(f"<div class='bubble {cls}'>{item['text']}</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)


def _render_audio_player() -> None:
    b64 = st.session_state.get("current_audio_b64", "")
    name = st.session_state.get("current_audio_name", "")
    version = int(st.session_state.get("audio_version", 0))
    if not b64:
        return
    src = f"data:audio/wav;base64,{b64}"
    html = f"""
    <div style="position:fixed;right:16px;bottom:18px;background:rgba(0,0,0,.55);color:#fff;padding:10px 12px;border-radius:10px;font-size:12px;z-index:9999;">
      疗愈音乐循环播放
      <div id="mx-now">当前：{name}</div>
    </div>
    <audio id="mx-audio-{version}" autoplay loop style="display:none" data-volume="0.35">
      <source src="{src}" type="audio/wav" />
    </audio>
    <script>
      const a = document.getElementById("mx-audio-{version}");
      if (a) {{
        a.volume = 0.35;
        a.play().catch(() => {{}});
      }}
    </script>
    """
    components.html(html, height=0, scrolling=False)


def _render_reply_tts_player() -> None:
    """播放助手回复的 TTS 语音（一次性，不循环，音量稍大以便盖过背景音乐）"""
    b64 = st.session_state.get("reply_audio_b64", "")
    if not b64:
        return
    version = int(st.session_state.get("reply_audio_version", 0))
    src = f"data:audio/wav;base64,{b64}"
    html = f"""
    <audio id="mx-reply-tts-{version}" autoplay style="display:none">
      <source src="{src}" type="audio/wav" />
    </audio>
    <script>
      const a = document.getElementById("mx-reply-tts-{version}");
      if (a) {{
        a.volume = 1.0;
        a.play().catch(() => {{}});
      }}
    </script>
    """
    components.html(html, height=0, scrolling=False)


def _handle_after_user_append(
    user_text: str,
    *,
    use_doubao: bool,
    use_tts: bool,
    selected_voice: Optional[str],
    run_pipeline_file: Path,
    deliverables_dir: Path,
    sd_api_url: str,
) -> None:
    """在已写入用户消息且 round_count 已递增后，仅生成助手回复（国画/音乐改由手动按钮触发）。"""
    fallback = _quick_reply(user_text)
    history = [{"role": m["role"], "text": m["text"]} for m in st.session_state.messages]
    if get_reply_and_audio and (use_doubao or use_tts):
        with st.spinner("生成回复" + ("并合成语音..." if use_tts else "...")):
            r = get_reply_and_audio(
                user_text,
                history=history,
                fallback_reply=fallback,
                use_doubao=use_doubao,
                use_tts=use_tts,
                voice_id=selected_voice,
            )
        reply_text = r["text"]
        if r.get("audio_b64"):
            st.session_state.reply_audio_b64 = r["audio_b64"]
            st.session_state.reply_audio_version += 1
    else:
        reply_text = fallback
    st.session_state.messages.append({"role": "assistant", "text": reply_text})
    st.rerun()


def _init_state() -> None:
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {
                "role": "assistant",
                "text": "你好。你可以随时和我聊聊感受；当你希望换一幅更贴心情的画、配一段舒缓音乐时，点击 **生成新的国画背景与音乐** 即可（会参考你最近说的话和侧栏里的心理状态示意）。",
            }
        ]
    if "round_count" not in st.session_state:
        st.session_state.round_count = 0
    if "bg_b64" not in st.session_state:
        st.session_state.bg_b64 = _to_b64(DEFAULT_INIT_BG)
        st.session_state.bg_mime = _image_mime_from_path(DEFAULT_INIT_BG)
    elif "bg_mime" not in st.session_state:
        st.session_state.bg_mime = "image/png"
    if "current_audio_b64" not in st.session_state:
        st.session_state.current_audio_b64 = _to_b64(DEFAULT_INIT_AUDIO)
    if "current_audio_name" not in st.session_state:
        st.session_state.current_audio_name = DEFAULT_INIT_AUDIO.name if DEFAULT_INIT_AUDIO.exists() else ""
    if "audio_version" not in st.session_state:
        st.session_state.audio_version = 0
    if "reply_audio_b64" not in st.session_state:
        st.session_state.reply_audio_b64 = ""
    if "reply_audio_version" not in st.session_state:
        st.session_state.reply_audio_version = 0
    if "latest_mood_snapshot" not in st.session_state:
        st.session_state.latest_mood_snapshot = None
    if "mood_display_anxiety" not in st.session_state:
        st.session_state.mood_display_anxiety = None
    if "mood_anxiety_series" not in st.session_state:
        st.session_state.mood_anxiety_series = []


def render_app() -> None:
    """渲染对话疗愈界面（供多页面门户调用，不再重复 set_page_config）。"""
    _init_state()
    _render_background()

    with st.sidebar:
        click_heal_sidebar = _render_mood_sidebar()
        st.divider()
        st.header("系统配置")
        run_pipeline_file = Path(st.text_input("run_pipeline.py", str(DEFAULT_RUN_PIPELINE))).expanduser()
        deliverables_dir = Path(st.text_input("deliverables目录", str(DEFAULT_DELIVERABLES))).expanduser()
        sd_api_url = st.text_input("SD API URL", DEFAULT_SD_API_URL)
        st.divider()
        st.subheader("豆包对话 + 朗读")
        use_doubao = st.checkbox("使用豆包 API 生成回复", value=DOUBAO_VOICE_AVAILABLE, help="让回复更有灵魂")
        use_tts = st.checkbox("启用语音朗读", value=False, help="用豆包语音 TTS 朗读助手回复")
        voice_options = get_tts_voice_options() if (DOUBAO_VOICE_AVAILABLE and callable(get_tts_voice_options)) else []
        selected_voice = None
        if use_tts and voice_options:
            labels = [f"{v['name']} ({v['voice_type']})" for v in voice_options]
            idx = st.selectbox("朗读音色", range(len(labels)), format_func=lambda i: labels[i], key="tts_voice_select")
            selected_voice = voice_options[idx]["voice_type"]
        if not DOUBAO_VOICE_AVAILABLE:
            st.caption("需配置 .env 中 DOUBAO_API_KEY、TTS_*")
        use_llm_mood = st.checkbox(
            "大模型辅助状态估计",
            value=False,
            help="勾选后每轮用户发言会多调用一次豆包，仅用于生成结构化标签（更慢、需 API）",
        )
        if st.button("清空对话与队列"):
            st.session_state.messages = [{"role": "assistant", "text": "会话已重置。我们重新开始吧。"}]
            st.session_state.round_count = 0
            st.session_state.bg_b64 = _to_b64(DEFAULT_INIT_BG)
            st.session_state.bg_mime = _image_mime_from_path(DEFAULT_INIT_BG)
            st.session_state.current_audio_b64 = _to_b64(DEFAULT_INIT_AUDIO)
            st.session_state.current_audio_name = DEFAULT_INIT_AUDIO.name if DEFAULT_INIT_AUDIO.exists() else ""
            st.session_state.audio_version += 1
            st.session_state.reply_audio_b64 = ""
            st.session_state.reply_audio_version += 1
            st.session_state.latest_mood_snapshot = None
            st.session_state.mood_display_anxiety = None
            st.session_state.mood_anxiety_series = []
            st.rerun()

    st.title("墨心智愈 · 疗愈对话")
    multimodal_banner = st.session_state.pop("multimodal_banner", None)
    if multimodal_banner:
        st.info(multimodal_banner)
    _render_chat()

    can_heal = bool(_compose_healing_pipeline_text().strip())
    click_heal_main = st.button(
        "生成新的国画背景与音乐",
        type="primary",
        disabled=not can_heal,
        key="mx_heal_gen_main",
        help="根据最近对话与侧栏心理状态示意，生成安抚向国画与舒缓疗愈音乐",
    )

    pending = st.session_state.pop("pending_chat_text", None)
    user_text = st.chat_input("输入你的感受或近况...")
    effective = ""
    if pending and str(pending).strip():
        effective = str(pending).strip()
    elif user_text:
        effective = user_text.strip()

    if effective:
        st.session_state.messages.append({"role": "user", "text": effective})
        st.session_state.round_count += 1
        _push_mood_after_user_turn(effective, use_llm_mood)
        _handle_after_user_append(
            effective,
            use_doubao=use_doubao,
            use_tts=use_tts,
            selected_voice=selected_voice,
            run_pipeline_file=run_pipeline_file,
            deliverables_dir=deliverables_dir,
            sd_api_url=sd_api_url,
        )
    elif click_heal_main or click_heal_sidebar:
        composed = _compose_healing_pipeline_text().strip()
        if not composed:
            st.warning("请先发送至少一条消息，或待侧栏心理状态更新后再试。")
        else:
            _run_healing_deliverables(
                composed,
                use_doubao=use_doubao,
                use_tts=use_tts,
                selected_voice=selected_voice,
                run_pipeline_file=run_pipeline_file,
                deliverables_dir=deliverables_dir,
                sd_api_url=sd_api_url,
            )

    _render_audio_player()
    _render_reply_tts_player()


def main() -> None:
    st.set_page_config(page_title="墨心智愈 对话演示", layout="wide")
    render_app()


if __name__ == "__main__":
    main()
