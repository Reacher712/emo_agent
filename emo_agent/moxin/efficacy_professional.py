"""
结构化评估报告：面向用户展示「结论与建议」；完整计分细则仅保留在 to_markdown_full() 供可选导出。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List


@dataclass
class AssessmentReport:
    scale_id: str
    scale_title_zh: str
    raw_score: float
    max_raw: float
    index_score: float | None
    severity_code: str
    severity_label_zh: str
    cutoff_scheme: str
    item_labels: List[str]
    item_values: List[int]
    per_item_max: int
    clinical_summary_zh: List[str]  # 用于完整技术版
    advice_user_zh: List[str]  # 面向受试者：不出现「怎么加分、总分多少」等机制描述
    safety_flags: List[str] = field(default_factory=list)
    references_zh: List[str] = field(default_factory=list)
    disclaimer_zh: str = (
        "以上内容为筛查场景下的 **健康教育说明**，不能替代执业医师或心理治疗师的诊断与处置；"
        "解释与随访请以专业人员意见为准。"
    )

    def to_markdown_public(self) -> str:
        """面向网页展示：仅筛查提示与建议，不展示计分规则与逐题得分。"""
        lines: List[str] = []
        lines.append(f"### {self.scale_title_zh}")
        lines.append("")
        lines.append(f"**筛查提示（非诊断）**：{self.severity_label_zh}")
        lines.append("")
        for p in self.advice_user_zh:
            lines.append(p)
            lines.append("")
        if self.safety_flags:
            lines.append(
                "**重要**：如您近期出现伤害自己的想法，或有立即实施的风险，请联系 **亲友、当地急救或心理援助热线**，"
                "或尽快由他人陪同前往 **医院急诊**。本系统无法判断您的实时风险。"
            )
            lines.append("")
        lines.append("---")
        lines.append(self.disclaimer_zh)
        return "\n".join(lines)

    def to_markdown_full(self) -> str:
        """完整版：含粗分、切分说明、逐题记分（供研究/备案选配下载）。"""
        lines: List[str] = []
        lines.append(f"### {self.scale_title_zh} · 技术摘要")
        lines.append("")
        lines.append("| 项目 | 结果 |")
        lines.append("|------|------|")
        lines.append(f"| 粗分 | **{self.raw_score:g}** / {self.max_raw:g} |")
        if self.index_score is not None:
            lines.append(f"| 指数分（×4） | **{self.index_score:.1f}** |")
        lines.append(f"| 筛查分级 | **{self.severity_label_zh}** |")
        lines.append(f"| 分级编码（内部） | `{self.severity_code}` |")
        lines.append("")
        lines.append("#### 计分方案与常用切分")
        lines.append(self.cutoff_scheme)
        lines.append("")
        lines.append("#### 逐题记分")
        lines.append("| 题号 | 得分 | 满分 | 条目（摘录） |")
        lines.append("|------|------|------|--------------|")
        for i, (lab, v) in enumerate(zip(self.item_labels, self.item_values), start=1):
            short = lab if len(lab) <= 28 else lab[:27] + "…"
            lines.append(f"| {i} | {v} | {self.per_item_max} | {short} |")
        lines.append("")
        lines.append("#### 结构化说明")
        for p in self.clinical_summary_zh:
            lines.append(p)
            lines.append("")
        if self.safety_flags:
            lines.append("#### 安全提示（筛查）")
            for p in self.safety_flags:
                lines.append(f"- {p}")
            lines.append("")
        if self.references_zh:
            lines.append("#### 参考文献/工具来源")
            for p in self.references_zh:
                lines.append(f"- {p}")
            lines.append("")
        lines.append("#### 声明")
        lines.append(self.disclaimer_zh)
        return "\n".join(lines)

    def to_markdown(self) -> str:
        """兼容旧代码：默认与「简要版」一致，避免界面再次堆满技术细节。"""
        return self.to_markdown_public()

    def to_serializable(self) -> dict:
        return {
            "scale_id": self.scale_id,
            "raw_score": self.raw_score,
            "max_raw": self.max_raw,
            "index_score": self.index_score,
            "severity_code": self.severity_code,
            "severity_label_zh": self.severity_label_zh,
            "item_values": self.item_values,
            "safety_flags": self.safety_flags,
        }


def _advice_phq9(code: str) -> List[str]:
    if code == "minimal":
        return [
            "从您填写的情况来看，近两周情绪与动力相关困扰在筛查意义上 **较轻**。",
            "建议继续保持睡眠规律与适度运动，留意情绪变化；若低落 **持续两周以上** 或明显影响学习、工作与社交，可到 **医院心理科/精神科** 或正规心理咨询机构做一次面谈评估。",
        ]
    if code == "mild":
        return [
            "从您填写的情况来看，近两周可能存在 **轻度** 抑郁相关困扰（仅为筛查用语，不是诊断名称）。",
            "建议您安排作息、减少孤立，并与信任的人交流感受；若症状持续或加重，请 **预约专业初评**。",
        ]
    if code == "moderate":
        return [
            "从您填写的情况来看，筛查提示可能需要 **更认真地对待** 当前情绪状态（非诊断）。",
            "建议您在 **近期** 前往 **精神心理相关门诊** 或通过正规渠道预约心理咨询，由专业人员结合面谈进一步判断与制定支持方案。",
        ]
    if code == "mod_severe":
        return [
            "从您填写的情况来看，筛查提示情绪困扰可能 **偏重**（非诊断），需要 **尽快** 获得专业支持。",
            "建议您由亲友陪同或自行前往 **当地精神卫生机构/综合医院相关科室** 就诊评估，不要独自硬扛。",
        ]
    return [
        "从您填写的情况来看，筛查提示需要 **紧急重视** 当前情绪与安全（非诊断）。",
        "请务必 **尽快** 联系 **专业医疗机构**，如出现即时危险请拨打 **急救电话** 或前往 **最近急诊**。",
    ]


def _advice_gad7(code: str) -> List[str]:
    if code in ("minimal", "mild"):
        return [
            "从您填写的情况来看，近两周紧张与担忧在筛查意义上 **相对可控**（非诊断）。",
            "可尝试规律呼吸放松、限制咖啡因、保证睡眠；若担忧 **难以自控** 或影响明显，建议预约 **心理/精神科** 初评。",
        ]
    if code == "moderate":
        return [
            "从您填写的情况来看，焦虑相关困扰在筛查上达到 **需要认真对待** 的程度（非诊断）。",
            "建议在 **医疗或心理机构** 完成进一步评估，必要时讨论心理辅导或医学干预的可行性。",
        ]
    return [
        "从您填写的情况来看，筛查提示焦虑负荷 **较高**（非诊断），宜 **尽快** 寻求专业评估。",
        "若伴有明显躯体不适或惊恐发作，请 **优先** 排除躯体因素并接受规范处置建议。",
    ]


def _advice_who5(code: str) -> List[str]:
    if code == "wellbeing_good":
        return [
            "从您填写的情况来看，近两周 **积极感受较多**（幸福感自评方向，筛查用语）。",
            "可继续保持有益习惯；若同时仍有明显情绪低落，建议 **结合** 症状自评量表或专业解读。",
        ]
    if code == "wellbeing_moderate":
        return [
            "从您填写的情况来看，近两周整体情绪体验 **中等**（非诊断）。",
            "可关注压力源与休息质量，必要时与专业人士聊聊；干预后复测有助于观察变化。",
        ]
    return [
        "从您填写的情况来看，近两周 **积极感受偏少**（筛查提示，非诊断），可与抑郁等症状筛查 **对照** 理解。",
        "若长期心情压抑或影响生活，请预约 **医学/心理专业评估**，不要单凭自述量表自我贴标签。",
    ]


def build_phq9_report(item_scores: List[int], item_texts: List[str]) -> AssessmentReport:
    total = sum(item_scores)
    if total <= 4:
        code, lab = "minimal", "极低～轻微（筛查）"
    elif total <= 9:
        code, lab = "mild", "轻度（筛查）"
    elif total <= 14:
        code, lab = "moderate", "中度（筛查）"
    elif total <= 19:
        code, lab = "mod_severe", "中重度（筛查）"
    else:
        code, lab = "severe", "重度（筛查）"

    cutoff = (
        "**PHQ-9 粗分**：各题 0–3 之和，**理论范围 0–27**。\n\n"
        "**常用研究与筛查切分**（Kroenke 等，文献与指南中高频引用）：\n"
        "- **0–4**：极低～轻微；**5–9**：轻度；**10–14**：中度；**15–19**：中重度；**20–27**：重度。\n\n"
        "个体解释需结合 **病程、功能受损、精神病性症状、双相线索、物质因素** 等，本系统 **不** 收集也不判断上述维度。"
    )

    summary: List[str] = []
    summary.append(
        f"受试者自报在过去 2 周内，抑郁相关症状条目 **频率加权** 后粗分为 **{total}**，"
        f"落在 **{lab}** 常见区间（筛查语境）。"
    )
    if total >= 10:
        summary.append(
            "在该切分体系下，**中度及以上** 常见做法是建议由 **精神科/心理卫生机构** 进行结构化访谈与鉴别，"
            "并结合睡眠、食欲、认知与自伤风险等维度综合研判；可安排 **量表复测** 观察干预反应。"
        )
    elif total >= 5:
        summary.append(
            "**轻度** 区间提示需关注情绪、动力与睡眠等变化；若 **持续 ≥2 周** 或明显影响学习/工作/人际，"
            "建议预约 **初评** 并在专业人员指导下决定是否需要进一步检查。"
        )
    else:
        summary.append(
            "当前粗分位于 **极低～轻微** 常见区间，提示近期自报症状频率较低；仍建议保持规律作息与社会支持，并在症状波动时复测。"
        )

    safety: List[str] = []
    if len(item_scores) >= 9 and item_scores[8] >= 1:
        safety.append(
            "第 9 题（自伤/自杀意念相关）≥1：按筛查惯例列为 **高风险线索**，需 **尽快** 由 **精神科急诊/危机干预/家属陪同就医** 评估，"
            "本系统不能给出个体化风险分级与处置方案。"
        )

    refs = [
        "PHQ-9（Patient Health Questionnaire-9）：Kroenke K, Spitzer RL, Williams JB；中文版为研究/临床常用自评筛查工具。",
    ]

    advice_user = _advice_phq9(code)

    return AssessmentReport(
        scale_id="PHQ-9",
        scale_title_zh="病人健康问卷抑郁量表 9 项（PHQ-9）",
        raw_score=float(total),
        max_raw=27.0,
        index_score=None,
        severity_code=code,
        severity_label_zh=lab,
        cutoff_scheme=cutoff,
        item_labels=item_texts,
        item_values=list(item_scores),
        per_item_max=3,
        clinical_summary_zh=summary,
        advice_user_zh=advice_user,
        safety_flags=safety,
        references_zh=refs,
    )


def build_gad7_report(item_scores: List[int], item_texts: List[str]) -> AssessmentReport:
    total = sum(item_scores)
    if total <= 4:
        code, lab = "minimal", "极低～轻微（筛查）"
    elif total <= 9:
        code, lab = "mild", "轻度（筛查）"
    elif total <= 14:
        code, lab = "moderate", "中度（筛查）"
    else:
        code, lab = "severe", "重度（筛查）"

    cutoff = (
        "**GAD-7 粗分**：各题 0–3 之和，**理论范围 0–21**。\n\n"
        "**常用切分**（Spitzer / Kroenke / Löwe 等，筛查与研究）：\n"
        "- **0–4**：极低～轻微；**5–9**：轻度；**10–14**：中度；**15–21**：重度。\n\n"
        "广泛性焦虑障碍的 **诊断** 须符合病程、主诉与排除标准；本量表仅反映 **焦虑症状群困扰频率**。"
    )

    summary: List[str] = []
    summary.append(
        f"受试者自报在过去 2 周内，焦虑相关症状困扰频率加权粗分为 **{total}**，筛查分级为 **{lab}**。"
    )
    if total >= 10:
        summary.append(
            "**中度及以上** 时，建议在 **医疗/心理** 场景下完成焦虑谱系鉴别（含躯体疾病、物质、抑郁共病、惊恐等），"
            "并讨论 **心理治疗与/或药物** 的循证路径；本平台不提供个体化治疗建议。"
        )
    elif total >= 5:
        summary.append(
            "**轻度** 时，建议压力管理、放松训练、睡眠卫生；若担忧 **泛化、难以控制** 且影响功能，宜预约 **初评**。"
        )
    else:
        summary.append("粗分位于较低区间，提示近期自报焦虑困扰频率相对有限；可在应激增高时复测。")

    refs = [
        "GAD-7（Generalized Anxiety Disorder 7-item）：Spitzer RL, Kroenke K, Williams JB, Löwe B。",
    ]

    return AssessmentReport(
        scale_id="GAD-7",
        scale_title_zh="广泛性焦虑障碍 7 项量表（GAD-7）",
        raw_score=float(total),
        max_raw=21.0,
        index_score=None,
        severity_code=code,
        severity_label_zh=lab,
        cutoff_scheme=cutoff,
        item_labels=item_texts,
        item_values=list(item_scores),
        per_item_max=3,
        clinical_summary_zh=summary,
        advice_user_zh=_advice_gad7(code),
        safety_flags=[],
        references_zh=refs,
    )


def build_who5_report(item_scores: List[int], item_texts: List[str]) -> AssessmentReport:
    total = sum(item_scores)
    index_score = total * 4.0
    if index_score > 70:
        code, lab = "wellbeing_good", "幸福感较好（筛查）"
    elif index_score >= 52:
        code, lab = "wellbeing_moderate", "幸福感中等（筛查）"
    else:
        code, lab = "wellbeing_low", "幸福感偏低（筛查）"

    cutoff = (
        "**WHO-5 粗分**：5 题相加，每题 0–5，**范围 0–25**；**指数分 Index = 粗分 × 4**，**范围 0–100**。\n\n"
        "**方向**：分数 **越高** 表示近两周 **积极幸福感越好**（与 PHQ 类症状量表方向相反）。\n\n"
        "**常用筛查提示**（文献与 WHO 使用说明中常见）：指数分 **≤50** 常作为 **需进一步抑郁相关筛查** 的提示阈值之一，"
        "须结合 PHQ 等工具与面谈，**不能**单凭本分数诊断。"
    )

    summary: List[str] = []
    summary.append(
        f"受试者 WHO-5 粗分 **{total}**，指数分 **{index_score:.1f} / 100**，筛查标签为 **{lab}**。"
    )
    if index_score <= 50:
        summary.append(
            "指数分处于文献中常见的 **偏低** 区间：在项目/研究场景下，常建议 **并联** PHQ-9 等抑郁筛查并由专业人员解读；"
            "若伴有显著情绪低落或功能受损，应优先安排 **医学/心理评估**。"
        )
    else:
        summary.append(
            "指数分提示近期自报 **积极情绪的时段较多**；仍建议与症状量表、睡眠与现实功能一并观察，用于干预前后 **对照** 尤具价值。"
        )

    refs = [
        "WHO-5 Well-Index：世界卫生组织 5 项幸福感指数量表，用于人群与临床研究中幸福感与心理健康筛查的对照测量。",
    ]

    return AssessmentReport(
        scale_id="WHO-5",
        scale_title_zh="世界卫生组织 5 项幸福感指数（WHO-5）",
        raw_score=float(total),
        max_raw=25.0,
        index_score=index_score,
        severity_code=code,
        severity_label_zh=lab,
        cutoff_scheme=cutoff,
        item_labels=item_texts,
        item_values=list(item_scores),
        per_item_max=5,
        clinical_summary_zh=summary,
        advice_user_zh=_advice_who5(code),
        safety_flags=[],
        references_zh=refs,
    )