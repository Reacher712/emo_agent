import pandas as pd


def main():
    output_path_cn = r"c:\Users\33788\Desktop\moxin\青少年问卷结果汇总_可编辑.xlsx"
    output_path_en = r"c:\Users\33788\Desktop\moxin\youth_survey_results_editable.xlsx"

    # 1) 青少年样本概况（示例：N=180）
    sample_overview = pd.DataFrame(
        [
            ["总样本量", 180, "有效问卷，青少年样本占比高"],
            ["年龄15-17岁", 64, "35.6%"],
            ["年龄18-20岁", 79, "43.9%"],
            ["年龄21-22岁", 37, "20.6%"],
            ["在校高中生", 52, "28.9%"],
            ["在校大学生", 128, "71.1%"],
            ["女生", 101, "56.1%"],
            ["男生", 75, "41.7%"],
            ["其他/不便透露", 4, "2.2%"],
            ["近1个月压力较高及以上", 121, "67.2%（详见“压力分布_分层”）"],
        ],
        columns=["指标", "数值", "备注"],
    )

    # 1.1) 压力分布分层（青少年样本）
    pressure_distribution = pd.DataFrame(
        [
            ["很低", 9, "5.0%"],
            ["较低", 23, "12.8%"],
            ["中等", 27, "15.0%"],
            ["较高", 74, "41.1%"],
            ["很高", 47, "26.1%"],
            ["合计", 180, "100%"],
        ],
        columns=["压力等级（近1个月）", "人数", "占比"],
    )

    # 1.2) 心理画像扩展数据（需求调研阶段）
    psych_profile = pd.DataFrame(
        [
            ["持续紧张或担忧（每周>=3天）", 112, "62.2%"],
            ["入睡困难或睡眠质量差", 98, "54.4%"],
            ["因学业/考试产生明显压力", 126, "70.0%"],
            ["因人际关系产生明显压力", 79, "43.9%"],
            ["因家庭期待产生明显压力", 88, "48.9%"],
            ["情绪低落持续一周以上（近1月）", 67, "37.2%"],
            ["常感到孤独或缺乏支持", 72, "40.0%"],
            ["曾主动寻求心理帮助", 41, "22.8%"],
            ["愿意尝试匿名线上心理支持", 139, "77.2%"],
            ["愿意参加艺术化情绪调节活动", 147, "81.7%"],
        ],
        columns=["心理相关指标", "人数", "占比"],
    )

    # 1.3) 压力来源排序（多选题）
    stressor_ranking = pd.DataFrame(
        [
            [1, "学业与考试负担", "70.0%"],
            [2, "升学/就业不确定性", "58.9%"],
            [3, "家庭期待与比较压力", "48.9%"],
            [4, "人际沟通与关系冲突", "43.9%"],
            [5, "睡眠不足与作息紊乱", "41.7%"],
            [6, "自我要求过高", "39.4%"],
        ],
        columns=["排名", "主要压力来源", "选择占比"],
    )

    # 1.4) 心理健康分层（基于DASS-21前测，n=60）
    dass_severity = pd.DataFrame(
        [
            ["压力", "正常/轻度", 21, "35.0%"],
            ["压力", "中度", 20, "33.3%"],
            ["压力", "重度及以上", 19, "31.7%"],
            ["焦虑", "正常/轻度", 24, "40.0%"],
            ["焦虑", "中度", 18, "30.0%"],
            ["焦虑", "重度及以上", 18, "30.0%"],
            ["抑郁", "正常/轻度", 27, "45.0%"],
            ["抑郁", "中度", 16, "26.7%"],
            ["抑郁", "重度及以上", 17, "28.3%"],
        ],
        columns=["维度", "分层等级", "人数", "占比"],
    )

    # 2) 需求问卷核心题结果（5分制）
    demand_results = pd.DataFrame(
        [
            ["Q6", "希望有低门槛日常情绪调节方式", 4.42, "84.4%"],
            ["Q7", "更接受艺术化疗愈而非纯文字聊天", 4.18, "78.9%"],
            ["Q8", "传统心理服务门槛高/不便", 4.06, "73.9%"],
            ["Q9", "希望看到情绪趋势而非一次性结果", 4.31, "82.2%"],
            ["Q10", "愿与亲密关系对象共同情绪互动", 3.97, "69.4%"],
            ["Q11", "更接受具有中国文化元素的疗愈内容", 4.35, "83.3%"],
            ["Q12", "愿尝试情绪驱动的国画+音乐干预", 4.27, "81.1%"],
            ["Q13", "情绪看板/周报对长期调节有帮助", 4.21, "79.4%"],
            ["Q14", "愿尝试在线双人共绘沟通", 3.88, "66.7%"],
            ["Q15", "愿查看关系温度报告改善互动", 3.94, "68.9%"],
            ["Q16(反向)", "担心隐私安全问题", 3.72, "61.1%"],
            ["Q17", "在保障隐私前提下愿持续使用", 4.16, "77.2%"],
        ],
        columns=["题号", "题目", "均值(1-5)", "同意及以上占比"],
    )

    # 3) 场景与功能偏好
    preference_results = pd.DataFrame(
        [
            ["首选使用场景", "晚间个人减压", "49.4%"],
            ["首选使用场景", "学习/考试前稳定情绪", "27.8%"],
            ["首选使用场景", "亲子/伴侣共绘沟通", "18.9%"],
            ["首选使用场景", "其他", "3.9%"],
            ["最期待功能", "国画+音乐个性化生成", "41.7%"],
            ["最期待功能", "情绪趋势看板与周报", "30.0%"],
            ["最期待功能", "双人共绘与关系报告", "23.3%"],
            ["最期待功能", "纯聊天陪伴", "5.0%"],
        ],
        columns=["维度", "选项", "占比"],
    )

    # 4) 前后测效果（DASS-21，示例试用样本 n=60）
    effect_results = pd.DataFrame(
        [
            ["压力维度", 16.8, 13.1, "-22.0%"],
            ["焦虑维度", 13.6, 10.2, "-25.0%"],
            ["抑郁维度", 12.9, 10.8, "-16.3%"],
            ["主观平静感(0-100)", 48.7, 63.9, "+31.2%"],
            ["主观情绪可控感(0-100)", 45.2, 59.6, "+31.9%"],
        ],
        columns=["指标", "试用前均值", "试用后均值", "变化幅度"],
    )

    # 5) 可用性与体验（试用样本 n=60）
    usability_results = pd.DataFrame(
        [
            ["SUS总分(0-100)", 76.5, "达到良好可用性区间"],
            ["UEQ-吸引力", 1.62, "正向体验明显"],
            ["UEQ-易懂性", 1.38, "新用户上手较快"],
            ["UEQ-效率", 1.41, "主要任务完成顺畅"],
            ["UEQ-可靠性", 1.27, "可继续优化反馈稳定性"],
            ["UEQ-刺激性", 1.58, "疗愈互动兴趣较高"],
            ["UEQ-创新性", 1.71, "文化+AI融合感知突出"],
        ],
        columns=["指标", "结果", "说明"],
    )

    # 导出为 Excel 多工作表
    with pd.ExcelWriter(output_path_cn, engine="openpyxl") as writer:
        sample_overview.to_excel(writer, sheet_name="青少年样本概况", index=False)
        pressure_distribution.to_excel(writer, sheet_name="压力分布_分层", index=False)
        psych_profile.to_excel(writer, sheet_name="心理画像_扩展指标", index=False)
        stressor_ranking.to_excel(writer, sheet_name="压力来源排序", index=False)
        dass_severity.to_excel(writer, sheet_name="心理分层_DASS21前测", index=False)
        demand_results.to_excel(writer, sheet_name="需求问卷核心结果", index=False)
        preference_results.to_excel(writer, sheet_name="场景与功能偏好", index=False)
        effect_results.to_excel(writer, sheet_name="前后测效果_DASS21", index=False)
        usability_results.to_excel(writer, sheet_name="可用性与体验", index=False)

    with pd.ExcelWriter(output_path_en, engine="openpyxl") as writer:
        sample_overview.to_excel(writer, sheet_name="sample_overview", index=False)
        pressure_distribution.to_excel(writer, sheet_name="pressure_distribution", index=False)
        psych_profile.to_excel(writer, sheet_name="psych_profile", index=False)
        stressor_ranking.to_excel(writer, sheet_name="stressors_rank", index=False)
        dass_severity.to_excel(writer, sheet_name="dass21_severity_pre", index=False)
        demand_results.to_excel(writer, sheet_name="demand_results", index=False)
        preference_results.to_excel(writer, sheet_name="preference_results", index=False)
        effect_results.to_excel(writer, sheet_name="effect_dass21", index=False)
        usability_results.to_excel(writer, sheet_name="usability_ux", index=False)

    print(output_path_en)


if __name__ == "__main__":
    main()
