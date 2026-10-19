"""
根据用户当场表述估算「焦虑 / 心理态势」示意信号，用于对话界面展示。
均为 **健康教育层面的文字信号推测**，非临床诊断或量表测评。
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class MoodSnapshot:
    """单轮用户消息对应的一帧状态示意。"""

    anxiety_0_100: int  # 越高表示文字中紧张/担忧负荷越强（示意）
    mood_zh: str  # 情绪基调（筛查用语）
    arousal_zh: str  # 心理激活度：偏低 / 中等 / 偏高
    summary_zh: str  # 一句话说明
    source: str  # "heuristic" | "llm"


# 焦虑 / 担忧负荷（出现即加分，可重叠）
_ANXIETY_WEIGHTS: List[Tuple[str, int]] = [
    ("惊恐", 22),
    ("崩溃", 20),
    ("受不了", 18),
    ("失控", 18),
    ("慌", 16),
    ("焦虑", 18),
    ("紧张", 14),
    ("担心", 12),
    ("害怕", 14),
    ("恐惧", 16),
    ("不安", 12),
    ("发慌", 14),
    ("心慌", 12),
    ("睡不着", 10),
    ("失眠", 10),
    ("一直想", 8),
    ("反复想", 10),
    ("心慌意乱", 18),
    ("坐立不安", 14),
    ("心慌气短", 12),
    ("压力大", 14),
    ("喘不过气", 12),
    ("窒息", 14),
    ("濒危", 20),
    ("受不了", 16),
    ("完蛋", 10),
    ("烦躁", 10),
    ("焦躁", 12),
]

# 舒缓 / 稳定（降低焦虑示意识别）
_CALM_WEIGHTS: List[Tuple[str, int]] = [
    ("平静", -14),
    ("放松", -12),
    ("踏实", -10),
    ("稳定", -10),
    ("好多了", -12),
    ("缓过来了", -12),
    ("想开了", -8),
    ("还好", -6),
    ("能接受", -8),
    ("柔和", -8),
    ("安心", -10),
]

# 低落 / 沉重（单独影响「态势」标签，也会略抬高不利体感）
_LOW_WEIGHTS: List[Tuple[str, int]] = [
    ("绝望", 16),
    ("不想活", 22),
    ("自杀", 24),
    ("自残", 20),
    ("没意思", 10),
    ("空虚", 10),
    ("麻木", 8),
    ("抑郁", 12),
    ("崩溃大哭", 12),
    ("崩溃", 8),
    ("低落", 10),
    ("难过", 8),
    ("沮丧", 10),
    ("委屈", 8),
    ("累瘫", 8),
    ("好累", 8),
    ("疲惫", 6),
]

# 积极资源（略降低不利基调标签权重）
_POSITIVE_WEIGHTS: List[Tuple[str, int]] = [
    ("开心", -8),
    ("高兴", -8),
    ("轻松", -8),
    ("期待", -6),
    ("感谢", -6),
    ("暖", -4),
    ("希望", -6),
    ("好一点", -10),
]


def _clamp(n: int, lo: int, hi: int) -> int:
    return max(lo, min(hi, n))


def _score_keywords(text: str, weights: List[Tuple[str, int]]) -> int:
    t = text.strip()
    if not t:
        return 0
    s = 0
    for kw, w in weights:
        if kw in t:
            s += w
    return s


def estimate_heuristic(user_text: str) -> MoodSnapshot:
    """纯关键词 + 简单规则；不联网、无时延。"""
    t = (user_text or "").strip()
    if not t:
        return MoodSnapshot(
            anxiety_0_100=28,
            mood_zh="—",
            arousal_zh="—",
            summary_zh="尚未从你的文字中读取到有效描述。",
            source="heuristic",
        )

    anx = (
        32
        + _score_keywords(t, _ANXIETY_WEIGHTS)
        + _score_keywords(t, _CALM_WEIGHTS)
        + _score_keywords(t, _POSITIVE_WEIGHTS)
    )
    low_hit = _score_keywords(t, _LOW_WEIGHTS)

    # 低落语境下整体「心理负荷」上调，但不与焦虑简单相加到过饱和
    if low_hit >= 10:
        anx = anx + min(18, low_hit // 2)

    anx = _clamp(anx, 0, 100)

    # 情绪基调（多标签合并为一句）
    tags: List[str] = []
    if _score_keywords(t, _ANXIETY_WEIGHTS) >= 10 or any(x in t for x in ("慌", "焦虑", "紧张", "担心", "怕")):
        tags.append("紧张担忧")
    if low_hit >= 8:
        tags.append("情绪低落或沉重感")
    if not tags:
        if _score_keywords(t, _POSITIVE_WEIGHTS) <= -6 or any(x in t for x in ("平静", "放松", "还好", "稳定")):
            tags.append("相对平稳或偏积极")
        else:
            tags.append("中性或混合")

    mood_zh = "、".join(dict.fromkeys(tags))  # 去重保序

    # 激活度：感叹号、程度副词、高唤醒词
    arousal = "中等"
    if re.search(r"[!！]{2,}", t) or any(x in t for x in ("特别", "非常", "超级", "极其", "快疯了")):
        arousal = "偏高"
    elif any(x in t for x in ("麻木", "放空", "发呆", "什么都不想", "乏力", "累")) and "崩溃" not in t:
        arousal = "偏低"
    elif anx >= 62:
        arousal = "偏高"
    elif anx <= 28:
        arousal = "偏低"

    summary_zh = f"从你这句话的文字线索看，紧张担忧负荷约 **{anx}**/100（示意），整体态势偏 **{mood_zh[:20]}**…" if len(
        mood_zh
    ) > 10 else f"从你这句话的文字线索看，紧张担忧负荷约 **{anx}**/100（示意），态势：**{mood_zh}**。"

    return MoodSnapshot(
        anxiety_0_100=anx,
        mood_zh=mood_zh,
        arousal_zh=arousal,
        summary_zh=summary_zh,
        source="heuristic",
    )


def _parse_llm_json(raw: str) -> Optional[Dict[str, Any]]:
    raw = (raw or "").strip()
    if not raw:
        return None
    # 尝试从 markdown 代码块中抽 JSON
    m = re.search(r"\{[^{}]*\}", raw, re.DOTALL)
    chunk = m.group(0) if m else raw
    try:
        return json.loads(chunk)
    except Exception:
        return None


def estimate_with_optional_llm(user_text: str, use_llm: bool) -> MoodSnapshot:
    """
    先算启发式；若 use_llm 且能调到豆包，则用结构化 JSON 覆盖数字与标签（失败则回落）。
    """
    base = estimate_heuristic(user_text)
    if not use_llm or not (user_text or "").strip():
        return base

    try:
        from doubao_voice import doubao_chat
    except Exception:
        return base

    sys_prompt = (
        "你是临床心理学实验室用的「文本情绪信号」标注助手，只做开放式对话场景的粗粒度标注，"
        "输出必须是 **单独一行** 合法 JSON，不要 markdown，不要解释。"
        '键：anxiety（0-100整数，表示紧张担忧/不安的文字负荷，非诊断）、'
        'mood（中文短语，如：紧张担忧、低落沉重、相对稳定、愤怒憋屈、混合等）、'
        'arousal（必须从「偏低」「中等」「偏高」三选一）、'
        'reason（不超过20字，说明依据但不引用用户原话逐字）。'
    )
    raw = doubao_chat((user_text or "")[:1200], history=None, system_prompt=sys_prompt)
    data = _parse_llm_json(raw or "")
    if not data:
        return base

    try:
        anx = int(data.get("anxiety", base.anxiety_0_100))
    except Exception:
        anx = base.anxiety_0_100
    anx = _clamp(anx, 0, 100)

    mood = str(data.get("mood", base.mood_zh)).strip() or base.mood_zh
    arousal = str(data.get("arousal", base.arousal_zh)).strip()
    if arousal not in ("偏低", "中等", "偏高"):
        arousal = base.arousal_zh
    reason = str(data.get("reason", "")).strip()

    summary_zh = f"大模型辅助：**紧张担忧负荷约 {anx}/100**（示意），态势：**{mood}**，激活：**{arousal}**"
    if reason:
        summary_zh += f"。依据：{reason}"

    return MoodSnapshot(
        anxiety_0_100=anx,
        mood_zh=mood,
        arousal_zh=arousal,
        summary_zh=summary_zh,
        source="llm",
    )


def blend_with_history(current: MoodSnapshot, history_scores: List[int], alpha: float = 0.55) -> int:
    """与近几轮焦虑分数混合，得到更平滑的展示值。"""
    if not history_scores:
        return current.anxiety_0_100
    prev_avg = sum(history_scores) / len(history_scores)
    return int(round(alpha * current.anxiety_0_100 + (1 - alpha) * prev_avg))


def anxiety_level_label(score: int) -> str:
    if score <= 35:
        return "相对较低（示意）"
    if score <= 55:
        return "中等（示意）"
    if score <= 75:
        return "偏高（示意）"
    return "很高（示意，建议重视自我调节与专业支持）"
