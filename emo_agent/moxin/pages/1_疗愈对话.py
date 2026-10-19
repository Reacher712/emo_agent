"""Therapeutic chat demo page."""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import streamlit as st

from portal_nav import back_home

ROOT = Path(__file__).resolve().parent.parent
RUN_PIPELINE = ROOT / "run_pipeline.py"

st.set_page_config(page_title="墨心智愈 | 疗愈对话", layout="wide")
back_home()


def quick_reply(text: str) -> str:
    text = (text or "").strip()
    if any(k in text for k in ["焦虑", "紧张", "担心", "害怕", "压力"]):
        return "我听见你现在有一些紧绷和担心。我们先不急着解决所有问题，可以先把注意力放到此刻最明显的身体感受上，慢慢呼吸两次，再选一个最小、最可完成的下一步。"
    if any(k in text for k in ["难过", "低落", "失落", "崩溃", "累"]):
        return "谢谢你愿意把这些感受说出来。低落并不代表你不够好，它更像是身心在提醒你需要被照顾。此刻可以先允许自己停一下，再把今天必须完成的事情缩小到一件。"
    if any(k in text for k in ["开心", "平静", "放松", "还好"]):
        return "很好，你已经靠近一个相对稳定的区间了。可以把这种稳定感记录下来：现在是什么环境、什么动作或什么想法，让你稍微舒服了一点？"
    return "我在认真听。你可以再多描述一点：这件事最让你难受的部分是什么？我们可以一起把情绪拆小，再找到一个更容易承受的入口。"


def run_pipeline(text: str) -> dict:
    if not RUN_PIPELINE.exists():
        return {"ok": False, "error": "未找到 run_pipeline.py"}
    case_name = f"demo_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    cmd = [
        sys.executable,
        str(RUN_PIPELINE),
        "--text",
        text,
        "--sd-api-url",
        st.session_state.get("sd_api_url", "http://127.0.0.1:7860"),
        "--save-case-name",
        case_name,
        "--music-duration-sec",
        "30",
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    parsed = {}
    if proc.stdout.strip():
        try:
            parsed = json.loads(proc.stdout.strip().splitlines()[-1])
        except Exception:
            parsed = {}
    return {
        "ok": proc.returncode == 0,
        "case_name": case_name,
        "stdout": proc.stdout.strip(),
        "stderr": proc.stderr.strip(),
        "parsed": parsed,
    }


st.title("疗愈对话")
st.caption("演示目标：把用户情绪表达转化为共情回应，并在条件具备时联动国画生成与疗愈音乐。")

with st.sidebar:
    st.subheader("运行设置")
    st.text_input("Stable Diffusion API", value="http://127.0.0.1:7860", key="sd_api_url")
    use_pipeline = st.toggle("尝试调用完整闭环", value=False)
    st.caption("未启动外部模型或 SD 时，建议关闭完整闭环，使用本地演示回复。")

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "你好，我是墨心智愈。你可以用几句话描述现在的情绪，我会先陪你把状态稳定下来。"}
    ]

pending = st.session_state.pop("pending_chat_text", None)
if pending:
    st.session_state.messages.append({"role": "user", "content": pending})
    st.session_state.messages.append({"role": "assistant", "content": quick_reply(pending)})

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

user_text = st.chat_input("说说你现在的感受...")
if user_text:
    st.session_state.messages.append({"role": "user", "content": user_text})
    if use_pipeline:
        with st.spinner("正在尝试调用完整生成闭环..."):
            result = run_pipeline(user_text)
        if result["ok"]:
            reply = "完整闭环已运行完成，生成文件已写入 deliverables / outputs。你也可以继续描述感受，我会根据上下文回应。"
            if result.get("parsed"):
                reply += f"\n\n运行结果：`{result['case_name']}`"
            st.session_state.messages.append({"role": "assistant", "content": reply})
        else:
            fallback = quick_reply(user_text)
            detail = result.get("stderr") or result.get("error") or "外部接口未就绪"
            st.session_state.messages.append(
                {"role": "assistant", "content": f"{fallback}\n\n完整闭环暂未跑通：{detail}"}
            )
    else:
        st.session_state.messages.append({"role": "assistant", "content": quick_reply(user_text)})
    st.rerun()

st.divider()
st.info("提示：国赛现场可以先展示本地对话，再打开完整闭环开关演示生成链路。")
