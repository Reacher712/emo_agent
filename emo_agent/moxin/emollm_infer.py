import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Dict, Tuple

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from project_paths import MODEL_DIR


DEFAULT_MODEL_DIR = MODEL_DIR
VALID_EMOTIONS = ["焦虑", "压力", "低落", "平静", "积极"]


def _pick_device() -> str:
    return "cuda" if torch.cuda.is_available() else "cpu"


@lru_cache(maxsize=1)
def _load_model_and_tokenizer(model_dir: str) -> Tuple[AutoTokenizer, AutoModelForCausalLM, str]:
    device = _pick_device()
    tokenizer = AutoTokenizer.from_pretrained(model_dir, local_files_only=True)
    model = AutoModelForCausalLM.from_pretrained(model_dir, local_files_only=True)
    model = model.to(device)
    model.eval()
    return tokenizer, model, device


def _extract_first_json(text: str) -> Dict:
    match = re.search(r"\{[\s\S]*\}", text)
    if not match:
        raise ValueError("未找到JSON对象")
    return json.loads(match.group(0))


def _fallback_rule(text: str) -> Dict:
    t = text.strip()
    if any(k in t for k in ["焦虑", "紧张", "慌", "担心"]):
        return {"emotion_label": "焦虑", "intensity": 4}
    if any(k in t for k in ["压力", "累", "疲惫", "忙不过来"]):
        return {"emotion_label": "压力", "intensity": 4}
    if any(k in t for k in ["难过", "无助", "失落", "不开心"]):
        return {"emotion_label": "低落", "intensity": 4}
    if any(k in t for k in ["平静", "放松", "稳定"]):
        return {"emotion_label": "平静", "intensity": 2}
    if any(k in t for k in ["开心", "有动力", "兴奋", "积极"]):
        return {"emotion_label": "积极", "intensity": 3}
    return {"emotion_label": "平静", "intensity": 2}


def _normalize_result(result: Dict, original_text: str) -> Dict:
    normalized = dict(result)

    if normalized.get("emotion_label") not in VALID_EMOTIONS:
        normalized["emotion_label"] = _fallback_rule(original_text)["emotion_label"]

    try:
        intensity = int(normalized.get("intensity", 2))
    except Exception:
        intensity = 2
    normalized["intensity"] = max(1, min(5, intensity))

    if "confidence" not in normalized:
        normalized["confidence"] = 0.6
    normalized["confidence"] = float(normalized["confidence"])

    normalized.setdefault(
        "guide_text",
        "先做三次缓慢呼吸，注意力放在呼气上，然后把此刻最真实的感受用一句话表达出来。",
    )
    normalized.setdefault("music_profile", {"style": "calm_piano", "duration_sec": 180})
    normalized.setdefault(
        "image_style_hint",
        {"tone": "cool_low_brightness", "composition": "high_negative_space"},
    )
    return normalized


def infer_emotion(user_text: str, model_dir: Path = DEFAULT_MODEL_DIR, max_new_tokens: int = 256) -> Dict:
    tokenizer, model, device = _load_model_and_tokenizer(str(model_dir))

    system_prompt = (
        "你是情绪识别与干预策略引擎。"
        "请仅返回JSON对象，不要返回任何额外解释。\n"
        "字段必须包含：emotion_label, intensity, confidence, guide_text, music_profile, image_style_hint。\n"
        "emotion_label取值仅限：焦虑、压力、低落、平静、积极。\n"
        "intensity范围1-5。\n"
        "music_profile包含style和duration_sec。\n"
        "image_style_hint包含tone和composition。"
    )
    user_prompt = f"用户输入：{user_text}"
    prompt = f"<|im_start|>system\n{system_prompt}<|im_end|>\n<|im_start|>user\n{user_prompt}<|im_end|>\n<|im_start|>assistant\n"

    inputs = tokenizer(prompt, return_tensors="pt").to(device)
    with torch.no_grad():
        out = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            do_sample=True,
            temperature=0.6,
            top_p=0.9,
            repetition_penalty=1.05,
        )
    generated = tokenizer.decode(out[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True).strip()

    try:
        parsed = _extract_first_json(generated)
    except Exception:
        parsed = _fallback_rule(user_text)
        parsed["confidence"] = 0.5
        parsed["guide_text"] = "我感受到你现在状态有些不稳。先做三次深呼吸，再告诉我此刻最强烈的情绪。"
        parsed["music_profile"] = {"style": "calm_piano", "duration_sec": 180}
        parsed["image_style_hint"] = {"tone": "cool_low_brightness", "composition": "high_negative_space"}

    result = _normalize_result(parsed, user_text)
    result["raw_output"] = generated
    return result


if __name__ == "__main__":
    sample = "我最近压力特别大，感觉总是紧张。"
    print(json.dumps(infer_emotion(sample), ensure_ascii=False, indent=2))
