"""
豆包对话 + 火山引擎 TTS（支持声音复刻）集成模块

功能：
1. 豆包对话 API：让回复更有灵魂，替代规则式 quick_reply
2. 火山引擎 TTS：将回复文本转为语音朗读
3. 声音复刻：使用定制音色（需在控制台预先创建）

依赖：pip install requests
配置：在 .env 中设置 DOUBAO_* 和 TTS_* 变量
"""

import base64
import csv
import json
import os
import uuid
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import requests
from project_paths import PROJECT_DIR, load_project_env

try:
    from dotenv import load_dotenv
except Exception:
    load_dotenv = None


DEFAULT_PROJECT_DIR = PROJECT_DIR
DEFAULT_TTS_OUTPUT_DIR = DEFAULT_PROJECT_DIR / "outputs" / "tts"
DEFAULT_TTS_VOICES_CSV = DEFAULT_PROJECT_DIR / "tts_voices.csv"


def _load_env() -> None:
    load_project_env()


# ========== 豆包对话 API ==========


ARK_CHAT_URL = "https://ark.cn-beijing.volces.com/api/v3/chat/completions"


def chat_reply(
    user_text: str,
    history: Optional[List[Dict[str, str]]] = None,
    system_prompt: Optional[str] = None,
    provider: Optional[str] = None,
) -> Optional[str]:
    """
    根据 CHAT_PROVIDER 调用 DeepSeek 或豆包；各服务使用独立凭证。
    """
    _load_env()
    provider = (provider or os.getenv("CHAT_PROVIDER", "doubao")).strip().lower()
    if provider == "deepseek":
        api_key = os.getenv("DEEPSEEK_API_KEY", "").strip()
        model = os.getenv("DEEPSEEK_MODEL", "deepseek-flash").strip()
        endpoint = "https://api.deepseek.com/chat/completions"
    elif provider == "doubao":
        api_key = os.getenv("DOUBAO_API_KEY", "").strip()
        model = os.getenv("DOUBAO_MODEL_ID", "doubao-1-5-pro-32k-250115").strip()
        endpoint = ARK_CHAT_URL
    else:
        return None
    if not api_key:
        return None

    _system = system_prompt or (
        "你是听山的情绪疗愈助手，温柔、共情、简洁。"
        "用第一人称与用户对话，语气像一位 calm 的朋友，不堆砌专业术语。"
        "每次回复控制在 50～120 字，避免过长。"
    )

    messages: List[Dict[str, str]] = [{"role": "system", "content": _system}]
    if history:
        for h in history[-6:]:
            messages.append({"role": h.get("role", "user"), "content": h.get("text", h.get("content", ""))})
    # Callers may already have appended the current user message to their history.
    if messages[-1] == {"role": "user", "content": user_text}:
        messages.pop()
    messages.append({"role": "user", "content": user_text})

    payload = {
        "model": model,
        "messages": messages,
        "max_tokens": 256,
        "temperature": 0.7,
    }
    if provider == "deepseek":
        payload["thinking"] = {"type": "disabled"}
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }

    try:
        r = requests.post(endpoint, json=payload, headers=headers, timeout=60)
        r.raise_for_status()
        data = r.json()
        choices = data.get("choices", [])
        if choices:
            content = choices[0].get("message", {}).get("content", "")
            return (content or "").strip()
    except Exception:
        pass
    return None


def doubao_chat(user_text: str, history=None, system_prompt=None) -> Optional[str]:
    """Compatibility entry for callers explicitly requesting the original provider."""
    return chat_reply(user_text, history=history, system_prompt=system_prompt, provider="doubao")


# ========== 火山引擎 TTS（豆包语音）==========


def volc_tts(
    text: str,
    speaker: str = "BV001_streaming",
    output_path: Optional[Path] = None,
    format_type: str = "wav",
) -> Tuple[Optional[Path], Optional[str]]:
    """
    调用火山引擎 V1 语音合成 API（HTTP 一次性合成）。
    文档：https://www.volcengine.com/docs/6561/1257584

    环境变量：TTS_APP_ID、TTS_TOKEN（Access Token）、TTS_CLUSTER
    V1 不支持豆包语音2.0音色，请用文档音色列表中的 voice_type。
    """
    _load_env()
    app_id = os.getenv("TTS_APP_ID", "").strip()
    token = os.getenv("TTS_TOKEN", "").strip()
    cluster = os.getenv("TTS_CLUSTER", "volcano_tts").strip()

    if not token or not app_id:
        return None, "TTS_APP_ID / TTS_TOKEN 未配置"

    url = "https://openspeech.bytedance.com/api/v1/tts"
    headers = {
        "Authorization": f"Bearer;{token}",
        "Content-Type": "application/json",
    }
    req_id = str(uuid.uuid4())
    enc = format_type.lower() if format_type.lower() in ("wav", "pcm", "mp3", "ogg_opus") else "wav"
    payload = {
        "app": {"appid": app_id, "token": "access", "cluster": cluster},
        "user": {"uid": "moxin_user"},
        "audio": {
            "voice_type": speaker,
            "encoding": enc,
            "speed_ratio": 0.95,
            "loudness_ratio": 1.25,
        },
        "request": {
            "reqid": req_id,
            "text": text[:1024],
            "operation": "query",
        },
    }

    try:
        r = requests.post(url, json=payload, headers=headers, timeout=60)
        if r.status_code != 200:
            try:
                err_body = r.json()
                return None, f"HTTP {r.status_code}: {err_body.get('message', r.text[:200])}"
            except Exception:
                return None, f"HTTP {r.status_code}: {r.text[:200]}"
        data = r.json()
        code = data.get("code", -1)
        if code != 3000:
            return None, data.get("message", f"TTS 错误 code={code}")
        audio_b64 = data.get("data")
        if not audio_b64:
            return None, data.get("message", "TTS 返回无音频")
        audio_bytes = base64.b64decode(audio_b64)
        if not output_path:
            DEFAULT_TTS_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
            ext = "wav" if enc == "wav" else "mp3" if enc == "mp3" else "pcm"
            output_path = DEFAULT_TTS_OUTPUT_DIR / f"{uuid.uuid4().hex[:12]}.{ext}"
        output_path.write_bytes(audio_bytes)
        return output_path, None
    except Exception as e:
        return None, str(e)


# ========== 音色列表（从 tts_voices.csv 或 .env 读取）==========


def _load_tts_voices(csv_path: Optional[Path] = None) -> List[str]:
    """从 tts_voices.csv 加载所有 voice_type，按行顺序。"""
    path = csv_path or DEFAULT_TTS_VOICES_CSV
    voices: List[str] = []
    if path.exists():
        try:
            with path.open("r", encoding="utf-8-sig", newline="") as f:
                for row in csv.DictReader(f):
                    vt = (row.get("voice_type") or "").strip()
                    if vt:
                        voices.append(vt)
        except Exception:
            pass
    return voices


def get_tts_voice_options(csv_path: Optional[Path] = None) -> List[Dict[str, str]]:
    """返回供前端下拉选择的音色列表，每项含 voice_type 和 name。"""
    _load_env()
    if csv_path is None and os.getenv("TTS_API_KEY", "").strip():
        return [{"voice_type": os.getenv("TTS_V3_SPEAKER", "zh_female_vv_uranus_bigtts"), "name": "豆包语音 2.0"}]
    path = csv_path or DEFAULT_TTS_VOICES_CSV
    out: List[Dict[str, str]] = []
    if path.exists():
        try:
            with path.open("r", encoding="utf-8-sig", newline="") as f:
                for row in csv.DictReader(f):
                    vt = (row.get("voice_type") or "").strip()
                    name = (row.get("name") or "").strip() or vt
                    if vt:
                        out.append({"voice_type": vt, "name": name})
        except Exception:
            pass
    if not out:
        out = [
            {"voice_type": "zh_female_meilinvyou_moon_bigtts", "name": "魅力女声"},
            {"voice_type": "zh_male_beijingxiaoye_moon_bigtts", "name": "北京小爷"},
        ]
    return out


def _get_tts_voice(round_index: int = 0, csv_path: Optional[Path] = None) -> str:
    """根据轮次从音色列表中循环选取。若无 CSV 则回退到 .env 的 TTS_VOICE_1/2。"""
    voices = _load_tts_voices(csv_path)
    if voices:
        return voices[round_index % len(voices)]
    _load_env()
    v1 = os.getenv("TTS_VOICE_1", "").strip() or "zh_female_meilinvyou_moon_bigtts"
    v2 = os.getenv("TTS_VOICE_2", "").strip() or "zh_male_beijingxiaoye_moon_bigtts"
    return v1 if round_index % 2 == 0 else v2


def tts_with_voice(
    text: str,
    voice_id: Optional[str] = None,
    round_index: int = 0,
    output_path: Optional[Path] = None,
) -> Tuple[Optional[Path], Optional[str]]:
    """
    用两种固定音色之一进行 TTS。
    voice_id: 直接指定音色；否则根据 round_index 在 TTS_VOICE_1 / TTS_VOICE_2 间切换。
    音色可为预设 ID（见音色列表）或你通过声音复刻得到的两段音频对应的 speaker_id。
    """
    _load_env()
    if os.getenv("TTS_API_KEY", "").strip():
        speaker = voice_id or os.getenv("TTS_V3_SPEAKER", "zh_female_vv_uranus_bigtts")
        return volc_tts_v3(text, speaker=speaker, output_path=output_path)
    speaker = voice_id or _get_tts_voice(round_index)
    return volc_tts(text, speaker=speaker, output_path=output_path)


def decode_v3_audio(lines) -> bytes:
    """Accept audio only after a complete successful response, never partial output."""
    chunks = []
    complete = False
    for line in lines:
        if isinstance(line, bytes):
            line = line.decode("utf-8")
        line = line.strip()
        if not line or line.startswith(("event:", ":")):
            continue
        if line.startswith("data:"):
            line = line[5:].strip()
        frame = json.loads(line)
        code = frame.get("code")
        if code not in (0, 20000000):
            raise RuntimeError(f"TTS V3 错误 {code}: {frame.get('message', 'unknown error')}")
        if frame.get("data"):
            chunks.append(base64.b64decode(frame["data"], validate=True))
        if code == 20000000:
            complete = True
            break
    if not complete:
        raise RuntimeError("TTS V3 响应未正常结束，未保存不完整音频")
    audio = b"".join(chunks)
    if not audio:
        raise RuntimeError("TTS V3 未返回音频")
    return audio


def volc_tts_v3(text: str, speaker: str, output_path: Optional[Path] = None) -> Tuple[Optional[Path], Optional[str]]:
    """New speech console authentication; separate from the Ark chat API key."""
    _load_env()
    api_key = os.getenv("TTS_API_KEY", "").strip()
    if not api_key:
        return None, "TTS_API_KEY 未配置"
    headers = {
        "X-Api-Key": api_key,
        "X-Api-Resource-Id": os.getenv("TTS_RESOURCE_ID", "seed-tts-2.0"),
        "X-Api-Request-Id": str(uuid.uuid4()),
        "Content-Type": "application/json",
    }
    encoding = "wav" if output_path and output_path.suffix.lower() == ".wav" else "mp3"
    payload = {"req_params": {"text": text[:1024], "speaker": speaker, "audio_params": {"format": encoding, "sample_rate": 24000}}}
    try:
        with requests.post("https://openspeech.bytedance.com/api/v3/tts/unidirectional", headers=headers, json=payload, stream=True, timeout=(10, 60)) as response:
            if response.status_code != 200:
                return None, f"TTS V3 HTTP {response.status_code}: {response.text[:300].replace(api_key, '<redacted>')}"
            audio = decode_v3_audio(response.iter_lines())
        path = output_path or DEFAULT_TTS_OUTPUT_DIR / f"{uuid.uuid4().hex[:12]}.{encoding}"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(audio)
        return path, None
    except Exception as exc:
        return None, str(exc).replace(api_key, "<redacted>")


def tts_with_clone(
    text: str,
    custom_speaker_id: Optional[str] = None,
    output_path: Optional[Path] = None,
) -> Tuple[Optional[Path], Optional[str]]:
    """兼容旧接口，内部调用 tts_with_voice。"""
    return tts_with_voice(text, voice_id=custom_speaker_id, output_path=output_path)


# ========== 一体化：豆包回复 + TTS 朗读 ==========


def get_reply_and_audio(
    user_text: str,
    history: Optional[List[Dict[str, str]]] = None,
    fallback_reply: Optional[str] = None,
    use_doubao: bool = True,
    use_tts: bool = True,
    voice_id: Optional[str] = None,
) -> Dict:
    """
    返回：{"text": str, "audio_path": Optional[Path], "audio_b64": Optional[str], "error": Optional[str]}
    """
    text = None
    if use_doubao:
        text = chat_reply(user_text, history=history)
    chat_fallback = bool(use_doubao and not text)
    if not text and fallback_reply:
        text = fallback_reply
    if not text:
        text = "我在认真听你说。你可以再多描述一点此刻最强烈的情绪，我会和你一起把状态慢慢拉稳。"

    result = {"text": text, "audio_path": None, "audio_b64": None, "error": None, "chat_fallback": chat_fallback}

    if use_tts:
        path, err = tts_with_voice(text, voice_id=voice_id)
        if err:
            result["error"] = err
        elif path and path.exists():
            result["audio_path"] = path
            result["audio_b64"] = base64.b64encode(path.read_bytes()).decode("utf-8")

    return result


if __name__ == "__main__":
    # 简单测试
    _load_env()
    r = get_reply_and_audio("最近有点焦虑", use_doubao=True, use_tts=True)
    print("text:", r["text"])
    print("audio_path:", r["audio_path"])
    print("error:", r["error"])
