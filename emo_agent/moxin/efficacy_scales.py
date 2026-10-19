"""PHQ-9 / GAD-7 / WHO-5：题干与指导语；解读由 `efficacy_professional` 生成结构化报告。

说明：工具为国际常用自评筛查/幸福感测量；中文版在国内临床与研究中常见。
下列题干与频率锚点参照公开领域常用译法整理，用于项目演示与症状严重度「趋势」记录，
不能替代执业医师或心理治疗师的面谈与诊断。
"""

from __future__ import annotations

from typing import List, Optional

from efficacy_professional import build_gad7_report, build_phq9_report, build_who5_report
# PHQ 系列常用频率锚点（0–3）
LIKERT_4 = [
    "完全不会",
    "好几天",
    "一半以上的天数",
    "几乎每天",
]

PHQ9_TIME_FRAME = (
    "**作答范围**：请根据 **过去 2 周** 的实际情况作答。"
    "每一题选择该问题 **困扰您的频繁程度**（反映症状出现频率，不等同于临床诊断标签）。"
)

GAD7_TIME_FRAME = (
    "**作答范围**：请根据 **过去 2 周** 内的情况，选择各题最符合的一项。"
    "本量表用于评估 **广泛性焦虑相关症状** 的困扰频率，结果为筛查线索，**非物质诊断**。"
)

# 量表来源（答辩/文档可引用；正文为常用学术表述，非版权文本复制）
REF_PHQ9 = (
    "Patient Health Questionnaire-9 (PHQ-9)，Kroenke K, Spitzer RL, Williams JB. "
    "中文版在国内外临床与研究中使用广泛，用于抑郁相关症状严重度的自评筛查与变化监测。"
)

REF_GAD7 = (
    "Generalized Anxiety Disorder 7-item (GAD-7)，Spitzer RL, Kroenke K, Williams JB, Löwe B. "
    "用于广泛性焦虑相关症状筛查及严重度大致分级的常用自评工具。"
)

REF_WHO5 = (
    "WHO-5 Well-Index：世界卫生组织 5 项幸福感指数，用于幸福感与心理健康促进效果的自评测量；"
    "指数分越高表示近期积极情绪体验越多。"
)

# WHO-5：0-5，越高表示该正向表述符合时间越长
LIKERT_WHO5 = [
    "从未有（0）",
    "偶尔（1）",
    "少于一半时间（2）",
    "一半以上时间（3）",
    "大多数时候（4）",
    "所有时间（5）",
]

WHO5_TIME_FRAME = (
    "**作答范围**：请根据 **过去 2 周** 内各题描述与您实际情况的符合程度作答。"
    "**注意**：本量表为 **幸福感/积极情绪** 导向，**分数越高表示感觉越好**（与 PHQ「症状越多分越高」方向相反）。"
)


def phq9_questions() -> List[str]:
    """PHQ-9 九项核心内容（通行中文表述，与临床常用译本一致）。"""
    return [
        "做事时提不起劲或没有乐趣",
        "感到心情低落、沮丧或绝望",
        "入睡困难、睡不安稳或睡眠过多",
        "感觉疲倦或没有活力",
        "食欲不振或吃太多",
        "觉得自己很糟糕、觉得自己失败，或让自己或家人失望",
        "对事物难以集中注意力，例如阅读或看电视时",
        "他人觉察到您动作或说话变缓慢，或相反——烦躁、坐立不安、动得比平常更多",
        "有不如死掉、或有用某种方式伤害自己的想法",
    ]


def gad7_questions() -> List[str]:
    return [
        "感觉紧张、焦虑或急切",
        "不能够停止或控制担忧",
        "对各种各样的事情担忧过多",
        "很难放松下来",
        "由于不安而难以静坐",
        "变得容易烦恼或急躁",
        "感到似乎将有可怕的事情发生，并因此害怕",
    ]


def who5_questions() -> List[str]:
    """WHO-5 五项（通行中文表述，语义为积极幸福感受）。"""
    return [
        "我感到愉快、心情惬意",
        "我感到平静放松",
        "我感到积极、精力充沛",
        "我睡醒时感到清醒、得到了足够休息",
        "我日常生活中对很多事感兴趣",
    ]


def interpret_phq9(total: int, item_scores: Optional[List[int]] = None) -> str:
    """结构化 Markdown 评估报告（分项计分表 + 切分 + 叙事）。"""
    _ = total  # 兼容旧调用；计分以分项为准
    scores = list(item_scores or [])
    r = build_phq9_report(scores, phq9_questions())
    return r.to_markdown()


def interpret_gad7(total: int, item_scores: Optional[List[int]] = None) -> str:
    scores = list(item_scores or [])
    r = build_gad7_report(scores, gad7_questions())
    return r.to_markdown()


def interpret_who5(total: int, item_scores: Optional[List[int]] = None) -> str:
    _ = total
    scores = list(item_scores or [])
    r = build_who5_report(scores, who5_questions())
    return r.to_markdown()
