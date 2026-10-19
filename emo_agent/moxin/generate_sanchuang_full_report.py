from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt


def add_page_number(paragraph):
    run = paragraph.add_run()
    fld_begin = OxmlElement("w:fldChar")
    fld_begin.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText")
    instr.text = "PAGE"
    fld_end = OxmlElement("w:fldChar")
    fld_end.set(qn("w:fldCharType"), "end")
    run._r.append(fld_begin)
    run._r.append(instr)
    run._r.append(fld_end)


def set_document_layout(doc: Document) -> None:
    # 常见高校提交格式（可按学校模板微调）
    for section in doc.sections:
        section.top_margin = Cm(2.5)
        section.bottom_margin = Cm(2.5)
        section.left_margin = Cm(3.0)
        section.right_margin = Cm(2.5)
        section.header_distance = Cm(1.5)
        section.footer_distance = Cm(1.5)

        header_p = section.header.paragraphs[0]
        header_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        header_p.text = "三创赛项目报告书（墨韵心调）"
        header_run = header_p.runs[0]
        header_run.font.name = "宋体"
        header_run._element.rPr.rFonts.set(qn("w:eastAsia"), "宋体")
        header_run.font.size = Pt(10.5)

        footer_p = section.footer.paragraphs[0]
        footer_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        footer_p.text = "第 "
        add_page_number(footer_p)
        footer_p.add_run(" 页")
        for run in footer_p.runs:
            run.font.name = "宋体"
            run._element.rPr.rFonts.set(qn("w:eastAsia"), "宋体")
            run.font.size = Pt(10.5)


def set_style(doc: Document) -> None:
    normal = doc.styles["Normal"]
    normal.font.name = "宋体"
    normal._element.rPr.rFonts.set(qn("w:eastAsia"), "宋体")
    normal.font.size = Pt(12)  # 小四
    pf = normal.paragraph_format
    pf.line_spacing_rule = WD_LINE_SPACING.ONE_POINT_FIVE
    pf.first_line_indent = Cm(0.74)  # 约2字符
    pf.space_before = Pt(0)
    pf.space_after = Pt(0)

    h1 = doc.styles["Heading 1"]
    h1.font.name = "黑体"
    h1._element.rPr.rFonts.set(qn("w:eastAsia"), "黑体")
    h1.font.size = Pt(16)  # 三号
    h1.font.bold = True

    h2 = doc.styles["Heading 2"]
    h2.font.name = "黑体"
    h2._element.rPr.rFonts.set(qn("w:eastAsia"), "黑体")
    h2.font.size = Pt(14)  # 小三
    h2.font.bold = True


def add_cover(doc: Document) -> None:
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run("三创赛项目报告书")
    r.bold = True
    r.font.size = Pt(24)
    r.font.name = "黑体"
    r._element.rPr.rFonts.set(qn("w:eastAsia"), "黑体")

    p2 = doc.add_paragraph()
    p2.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r2 = p2.add_run("项目名称：墨韵心调——AI驱动的国画多模态情感疗愈平台")
    r2.font.size = Pt(14)
    r2.font.name = "宋体"
    r2._element.rPr.rFonts.set(qn("w:eastAsia"), "宋体")

    doc.add_paragraph("")
    for line in [
        "项目类型：大学生创新创业训练项目/三创赛参赛项目",
        "报告版本：评审提交版（排版统一）",
        "日期：2026年3月",
    ]:
        p3 = doc.add_paragraph(line)
        p3.alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_page_break()


def add_toc(doc: Document) -> None:
    doc.add_heading("目录", level=1)
    lines = [
        "第一章 执行摘要",
        "  1.1 项目一句话定位",
        "  1.2 核心价值主张",
        "  1.3 当前进展与阶段成果",
        "第二章 项目背景与问题定义",
        "  2.1 政策与行业背景",
        "  2.2 目标问题与痛点拆解",
        "  2.3 目标用户与核心场景",
        "第三章 市场与用户调研",
        "  3.1 调研方法与样本说明",
        "  3.2 核心调研结论",
        "  3.3 需求优先级与机会窗口",
        "  3.4 竞品分析与差异化定位",
        "第四章 解决方案与产品设计",
        "  4.1 产品总体方案与业务闭环",
        "  4.2 功能模块设计",
        "  4.3 用户旅程与关键交互流程",
        "第五章 技术方案与实现路径",
        "  5.1 系统架构设计",
        "  5.2 关键机制与算法逻辑",
        "  5.3 开发进度与部署计划",
        "第六章 创新点与核心竞争力",
        "  6.1 创新点一：智能体协同",
        "  6.2 创新点二：国画情感量化",
        "  6.3 创新点三：动态情绪追踪",
        "  6.4 创新点四：双人共绘与关系温度",
        "第七章 商业模式与运营推广",
        "  7.1 商业模式设计",
        "  7.2 推广路径与合作策略",
        "  7.3 核心运营指标",
        "第八章 实验验证与阶段成果",
        "  8.1 验证方法与评价指标",
        "  8.2 前后测结果与效果分析",
        "  8.3 阶段成果清单",
        "  8.4 局限性与优化计划",
        "第九章 风险控制、伦理与合规",
        "  9.1 数据隐私与安全治理",
        "  9.2 内容安全与应用边界",
        "  9.3 风险识别与应对预案",
        "第十章 团队组织与实施计划",
        "  10.1 团队结构与职责分工",
        "  10.2 里程碑计划与时间安排",
        "  10.3 资源保障与外部协同",
        "第十一章 财务预算与资源需求",
        "  11.1 预算结构与成本构成",
        "  11.2 资金使用原则",
        "  11.3 预期产出与投入产出关系",
        "第十二章 结论与合作诉求",
        "  12.1 项目结论",
        "  12.2 下一阶段目标",
        "  12.3 合作诉求",
        "附录",
    ]
    for line in lines:
        doc.add_paragraph(line)
    doc.add_page_break()


def add_section(doc: Document, title: str, body: list[str]) -> None:
    doc.add_heading(title, level=2)
    for para in body:
        p = doc.add_paragraph(para)
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY


def add_caption(doc: Document, text: str) -> None:
    p = doc.add_paragraph(text)
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    if p.runs:
        run = p.runs[0]
        run.font.name = "宋体"
        run._element.rPr.rFonts.set(qn("w:eastAsia"), "宋体")
        run.font.size = Pt(10.5)


def main() -> None:
    doc = Document()
    set_document_layout(doc)
    set_style(doc)
    add_cover(doc)
    add_toc(doc)

    doc.add_heading("第一章 执行摘要", level=1)
    add_section(doc, "1.1 项目一句话定位", [
        "“墨韵心调”项目面向青年群体高频情绪压力与亲密关系沟通需求，构建“情绪识别—国画生成—音乐匹配—结果反馈”的多模态数字疗愈闭环，旨在提供可追踪、可解释、低门槛的日常情绪支持服务。"
    ])
    add_section(doc, "1.2 核心价值主张", [
        "用户价值：通过艺术化、轻量化、私密化的交互方式帮助用户进行日常情绪调节，降低寻求心理支持的心理门槛。",
        "社会价值：将传统国画审美与数字心理健康服务融合，拓展“以美润心”的新型实践路径。",
        "项目价值：形成“技术能力+场景验证+数据闭环”的可复制样板，为校园与机构场景落地提供依据。"
    ])
    add_section(doc, "1.3 当前进展与阶段成果", [
        "截至当前，项目已完成总体方案设计、问卷数据汇总脚本、可视化看板、竞品证据页及路演材料初版，形成了较完整的展示链路。",
        "在阶段性验证中，已形成需求调研样本（n=180）和试用评估样本（n=60），并输出了可量化指标结果，为后续试点与评审环节提供了数据基础。"
    ])

    doc.add_heading("第二章 项目背景与问题定义", level=1)
    add_section(doc, "2.1 政策与行业背景", [
        "国家层面持续强调心理健康服务能力建设与美育融入育人体系，数字化心理支持与文化创新应用具有明确的政策协同空间。",
        "同时，生成式人工智能技术的发展为个性化内容供给提供了可行工具，使“文化疗愈内容+智能交互反馈”的融合路径具备实践基础。"
    ])
    add_section(doc, "2.2 目标问题与痛点拆解", [
        "现有心理咨询服务专业性较强，但在青年群体中普遍存在触达频率低、使用门槛高、持续性不足等问题。",
        "通用冥想或陪伴工具在文化适配与个性化反馈方面仍存在不足；单一AI绘画产品虽具备内容生成能力，但缺乏干预机制与效果评估闭环。",
        "据此，本项目聚焦“可进入、可坚持、可验证”三类核心问题，提出系统化解决路径。"
    ])
    add_section(doc, "2.3 目标用户与核心场景", [
        "目标用户一：高校学生与青年群体，主要需求为压力释放、情绪稳定和自我调节。",
        "目标用户二：亲子/伴侣等亲密关系用户，主要需求为低对抗、可表达的沟通方式。",
        "核心场景包括晚间个人减压、考试前情绪稳定、双人共绘沟通与关系反馈。"
    ])

    doc.add_heading("第三章 市场与用户调研", level=1)
    add_section(doc, "3.1 调研方法与样本说明", [
        "本项目采用问卷调查、半结构访谈与小规模试用评估相结合的混合研究方法。需求调研样本量为180，试用评估样本量为60。",
        "调研对象以15-22岁青少年与大学生为主，并纳入部分教师及家庭用户反馈，以提升场景定义与功能需求分析的现实性。"
    ])
    add_caption(doc, "图3-1 用户调研实施流程图（占位，待插入）")
    add_caption(doc, "表3-1 调研样本结构统计表（占位，待插入）")
    add_section(doc, "3.2 核心调研结论", [
        "近1个月压力较高及以上占比67.2%，说明高频轻干预需求明显。",
        "愿意尝试匿名线上心理支持占比77.2%，反映私密化、低门槛服务具备用户基础。",
        "愿意参加艺术化情绪调节活动占比81.7%，表明“国画+音乐”路径具备较高接受度。",
        "需求问卷中“希望看到情绪趋势而非一次性结果”均值较高，支持动态追踪模块建设。"
    ])
    add_caption(doc, "图3-2 核心调研结论可视化图（占位，待插入）")
    add_section(doc, "3.3 需求优先级与机会窗口", [
        "优先级1：个性化国画+音乐干预，解决“当下情绪承接”问题；",
        "优先级2：情绪看板与周报，解决“长期使用价值”问题；",
        "优先级3：双人共绘与关系温度报告，拓展“关系疗愈与沟通支持”场景。",
        "机会窗口在于当前市场少有产品能够在文化疗愈内容、可解释机制和关系场景上同时形成闭环。"
    ])
    add_section(doc, "3.4 竞品分析与差异化定位", [
        "冥想App优势在轻量化，但长期留存和文化差异化不足；心理咨询平台优势在专业深度，但可及性与成本存在门槛；AI绘画工具优势在生成能力，但缺乏心理干预闭环。",
        "墨韵心调的差异化定位为“文化疗愈内容+情绪追踪反馈+双人关系分析”，在用户体验层和评估层形成组合优势。"
    ])
    add_caption(doc, "图3-3 竞品定位矩阵图（占位，待插入）")

    doc.add_heading("第四章 解决方案与产品设计", level=1)
    add_section(doc, "4.1 产品总体方案与业务闭环", [
        "项目采用“输入—编排—生成—验证—反馈”闭环：用户输入情绪自述后，由协调层拆解任务并调用情感、艺术、音乐三个智能体，输出个性化国画与音乐，并基于反馈持续优化。",
        "该闭环将一次性体验转化为连续服务过程，支持用户形成稳定使用习惯。"
    ])
    add_caption(doc, "图4-1 产品业务闭环图（占位，待插入）")
    add_section(doc, "4.2 功能模块设计", [
        "模块一：个人疗愈流程（情绪识别、国画生成、音乐匹配、即时建议）。",
        "模块二：情绪看板（当日变化、周趋势、个性化周报）。",
        "模块三：双人共绘（房间协作、实时画布、互动行为记录）。",
        "模块四：关系温度报告（主导性、跟随性、协作度分析与沟通建议）。"
    ])
    add_caption(doc, "表4-1 核心功能模块说明表（占位，待插入）")
    add_section(doc, "4.3 用户旅程与关键交互流程", [
        "典型流程为：用户输入情绪 -> 系统完成诊断 -> 输出国画与音乐 -> 用户互动与反馈 -> 情绪指标更新 -> 周报生成。",
        "关系场景流程为：创建共绘房间 -> 双人实时创作 -> 行为特征分析 -> 生成关系温度报告 -> 给出沟通建议。"
    ])

    doc.add_heading("第五章 技术方案与实现路径", level=1)
    add_section(doc, "5.1 系统架构设计", [
        "用户层：Web端承载输入、展示和交互。",
        "协调层：负责任务编排、状态管理、反馈回流。",
        "智能体层：情感感知智能体、艺术生成智能体、音乐匹配智能体。",
        "数据层：情绪记录库、国画特征库、交互行为分析库。"
    ])
    add_caption(doc, "图5-1 系统总体架构图（占位，待插入）")
    add_section(doc, "5.2 关键机制与算法逻辑", [
        "关键机制一：智能体协同编排，避免简单串行调用导致的信息孤岛。",
        "关键机制二：情感验证回路，将生成结果与目标情绪向量比对并触发调整。",
        "关键机制三：时间序列追踪，对多次使用数据进行趋势分析并输出可执行建议。"
    ])
    add_caption(doc, "图5-2 关键机制流程图（占位，待插入）")
    add_section(doc, "5.3 开发进度与部署计划", [
        "已完成阶段：问卷数据脚本、可视化看板、竞品证据页、报告与路演材料。",
        "在研阶段：多模块联调、数据口径统一和演示流程打磨。",
        "下一阶段：校内试点部署、样本扩展、功能迭代与指标复测。"
    ])

    doc.add_heading("第六章 创新点与核心竞争力", level=1)
    add_section(doc, "6.1 创新点一：智能体协同", [
        "项目将情感、艺术、音乐能力重构为协同智能体系统，通过协调层实现任务拆解与信息共享，形成“会诊式”内容生成流程。"
    ])
    add_section(doc, "6.2 创新点二：国画情感量化", [
        "从传统“情感标签”升级到“艺术特征—心理指标”关联，强调可解释性与可验证性，为评估疗愈效果提供依据。"
    ])
    add_section(doc, "6.3 创新点三：动态情绪追踪", [
        "通过多次记录构建个人情绪轨迹，输出焦虑值、平静值变化和改善率，使服务从“单次体验”走向“持续陪伴”。"
    ])
    add_section(doc, "6.4 创新点四：双人共绘与关系温度", [
        "项目扩展至关系疗愈场景，基于共绘行为特征生成关系温度报告，帮助用户识别互动模式并优化沟通。"
    ])
    add_caption(doc, "表6-1 四大创新点对照表（占位，待插入）")

    doc.add_heading("第七章 商业模式与运营推广", level=1)
    add_section(doc, "7.1 商业模式设计", [
        "采用分层服务思路：C端提供普惠化日常情绪支持，B端面向学校心理中心和机构输出数据看板与团体分析能力。",
        "项目强调社会价值与科研示范并重，商业化路径以场景验证和可持续合作为主。"
    ])
    add_section(doc, "7.2 推广路径与合作策略", [
        "路径一：校内试点，完成真实场景验证。",
        "路径二：跨校复制，形成标准化实施包。",
        "路径三：与心理机构、艺术院校和文化场馆合作，拓展应用边界。"
    ])
    add_section(doc, "7.3 核心运营指标", [
        "核心指标包括7日复访率、单次停留时长、共绘完成率、周报查看率与用户满意度。",
        "通过指标看板开展周度复盘，实现产品迭代与运营优化。"
    ])
    add_caption(doc, "表7-1 运营指标定义与目标值（占位，待插入）")

    doc.add_heading("第八章 实验验证与阶段成果", level=1)
    add_section(doc, "8.1 验证方法与评价指标", [
        "验证指标包含心理状态量表指标（如DASS-21）、主观感受指标（平静感、可控感）和可用性指标（SUS、UEQ）。",
        "采用前后测对比与体验反馈结合的方法评估项目效果。"
    ])
    add_caption(doc, "表8-1 验证指标体系表（占位，待插入）")
    add_section(doc, "8.2 前后测结果与效果分析", [
        "现有示例数据中，压力、焦虑、抑郁维度均值均出现下降，平静感和情绪可控感提升，说明多模态干预具备积极趋势。",
        "SUS总分达到良好可用性区间，证明原型具备继续扩大试用的基础。"
    ])
    add_caption(doc, "图8-1 DASS-21前后测对比图（占位，待插入）")
    add_caption(doc, "图8-2 可用性评估结果图（占位，待插入）")
    add_section(doc, "8.3 阶段成果清单", [
        "成果一：项目总览文档与技术叙事框架。",
        "成果二：问卷数据整理脚本及可编辑Excel数据集。",
        "成果三：问卷可视化看板与竞品证据展示页面。",
        "成果四：18分钟路演PPT与项目报告书正文。"
    ])
    add_section(doc, "8.4 局限性与优化计划", [
        "当前局限主要在样本规模和群体覆盖范围，后续将扩大样本并提升长期追踪时长。",
        "将进一步推进Excel与看板联动，减少人工维护成本，提高数据一致性。"
    ])

    doc.add_heading("第九章 风险控制、伦理与合规", level=1)
    add_section(doc, "9.1 数据隐私与安全治理", [
        "坚持最小化采集原则，仅收集实现功能所需数据；对个人信息进行匿名化处理并分级授权访问。",
        "建立访问日志与审计机制，保证数据使用可追溯。"
    ])
    add_section(doc, "9.2 内容安全与应用边界", [
        "项目定位为心理健康辅助工具，不提供医疗诊断结论，不替代专业心理治疗。",
        "对于高风险情绪表达场景，系统提供风险提示与人工转介建议，确保使用边界清晰。"
    ])
    add_section(doc, "9.3 风险识别与应对预案", [
        "技术风险：模型偏差导致内容不稳定；应对策略为人工校验与反馈迭代。",
        "运营风险：初期用户留存不足；应对策略为场景优化和周报驱动复访。",
        "落地风险：机构协同成本高；应对策略为小规模试点先行和标准化复制。"
    ])
    add_caption(doc, "表9-1 风险识别与应对矩阵（占位，待插入）")

    doc.add_heading("第十章 团队组织与实施计划", level=1)
    add_section(doc, "10.1 团队结构与职责分工", [
        "团队由技术研发、产品设计、心理支持、艺术内容与运营协同组成，形成跨学科互补。",
        "技术组负责模型与系统开发，产品组负责用户体验与流程设计，心理与艺术方向负责内容科学性与文化表达。"
    ])
    add_section(doc, "10.2 里程碑计划与时间安排", [
        "阶段一：理论与数据准备；阶段二：协同架构联调；阶段三：共绘功能与关系分析上线；阶段四：校内试点与成果输出。",
        "各阶段均设置可量化交付项，便于过程评估与节点复盘。"
    ])
    add_caption(doc, "图10-1 项目里程碑甘特图（占位，待插入）")
    add_section(doc, "10.3 资源保障与外部协同", [
        "内部保障包括脚本化工具、演示材料和迭代机制；外部协同重点为学校心理中心、指导教师和合作机构。",
        "通过共建试点场景提升项目可信度和推广可行性。"
    ])

    doc.add_heading("第十一章 财务预算与资源需求", level=1)
    add_section(doc, "11.1 预算结构与成本构成", [
        "预算重点投向研发迭代、算力与运维、用户测试与试点活动、展示与传播材料制作。",
        "按照“阶段目标—资金投入—成果输出”进行分项管理。"
    ])
    add_caption(doc, "表11-1 预算结构明细表（占位，待插入）")
    add_section(doc, "11.2 资金使用原则", [
        "坚持专款专用、过程可追踪、复盘可验证原则；以阶段结果作为资源投入优化依据。"
    ])
    add_section(doc, "11.3 预期产出与投入产出关系", [
        "预期产出包括原型系统优化、样本扩展数据、可复制试点方案、论文/案例/软著等成果。",
        "通过精准投入提升项目落地效率与成果转化率。"
    ])

    doc.add_heading("第十二章 结论与合作诉求", level=1)
    add_section(doc, "12.1 项目结论", [
        "墨韵心调围绕真实需求构建了可展示、可验证、可迭代的项目闭环，兼具心理健康服务价值与文化创新价值。"
    ])
    add_section(doc, "12.2 下一阶段目标", [
        "短期目标是完成试点验证与核心指标优化；中期目标是形成跨校复制路径与机构合作模型。"
    ])
    add_section(doc, "12.3 合作诉求", [
        "希望获得试点学校场景支持、专家评估指导和跨学科合作资源，共同推进项目规范化与规模化发展。"
    ])

    doc.add_heading("附录", level=1)
    for item in [
        "附录A：问卷样本说明、题目与统计表",
        "附录B：访谈提纲与访谈纪要",
        "附录C：系统界面截图与流程图",
        "附录D：实验指标定义（DASS-21、SUS、UEQ）",
        "附录E：竞品对比与外部证据链接",
        "附录F：合规说明与高风险场景转介流程",
    ]:
        doc.add_paragraph(item)

    out = r"c:\Users\33788\Desktop\moxin\三创赛项目报告书_评审提交版_墨韵心调.docx"
    doc.save(out)
    print(out)


if __name__ == "__main__":
    main()
