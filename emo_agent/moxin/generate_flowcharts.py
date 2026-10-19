# -*- coding: utf-8 -*-
"""
生成流程图：
- flow_01：平台主流程
- flow_02：技术架构
- flow_03：核心算法（run_pipeline）
- flow_04：五阶段技术路线图
- flow_05：墨韵心调 2.0 全文技术路线（四区块，对齐现行工程）
"""
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle
import matplotlib

matplotlib.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
matplotlib.rcParams["axes.unicode_minus"] = False

COLOR_MAIN = "#1E3A5F"
COLOR_BOX = "#F0F4FA"
COLOR_ACCENT = "#C45C26"
COLOR_ARROW = "#334155"
TEXT_COLOR = "#0F172A"

# 全局字号（再放大一档，便于投屏与 A4 打印阅读）
FS_BOX_TITLE = 19
FS_BOX_BODY = 15
FS_BOX_BODY_COMPACT = 14


def box(ax, x, y, w, h, title, body, title_fs=None, body_fs=None, accent=False):
    if title_fs is None:
        title_fs = FS_BOX_TITLE
    if body_fs is None:
        body_fs = FS_BOX_BODY
    fc = "#FFF5F0" if accent else COLOR_BOX
    ec = COLOR_ACCENT if accent else COLOR_MAIN
    patch = FancyBboxPatch(
        (x, y),
        w,
        h,
        boxstyle="round,pad=0.015,rounding_size=0.05",
        facecolor=fc,
        edgecolor=ec,
        linewidth=1.5,
    )
    ax.add_patch(patch)
    ax.text(x + w / 2, y + h - 0.28, title, ha="center", va="top", fontsize=title_fs, fontweight="bold", color=COLOR_MAIN)
    ax.text(x + w / 2, y + 0.14, body, ha="center", va="bottom", fontsize=body_fs, color=TEXT_COLOR, linespacing=1.38)


def v_arrow(ax, x, y1, y2):
    ax.annotate(
        "",
        xy=(x, y2),
        xytext=(x, y1),
        arrowprops=dict(arrowstyle="->", color=COLOR_ARROW, lw=1.8, shrinkA=3, shrinkB=3),
    )


def h_arrow(ax, x1, x2, y):
    ax.annotate(
        "",
        xy=(x2, y),
        xytext=(x1, y),
        arrowprops=dict(arrowstyle="->", color=COLOR_ARROW, lw=1.8, shrinkA=3, shrinkB=3),
    )


def region_bg(ax, x, y, w, h, color, alpha=0.38):
    r = Rectangle((x, y), w, h, facecolor=color, edgecolor="none", zorder=0, alpha=alpha)
    ax.add_patch(r)


def mini_box(ax, x, y, w, h, title, body, facecolor, title_fs=8.2, body_fs=6.6):
    patch = FancyBboxPatch(
        (x, y),
        w,
        h,
        boxstyle="round,pad=0.012,rounding_size=0.05",
        facecolor=facecolor,
        edgecolor=COLOR_MAIN,
        linewidth=1.15,
        zorder=2,
    )
    ax.add_patch(patch)
    ax.text(
        x + w / 2,
        y + h - 0.14,
        title,
        ha="center",
        va="top",
        fontsize=title_fs,
        fontweight="bold",
        color=COLOR_MAIN,
        zorder=3,
    )
    if body:
        ax.text(
            x + w / 2,
            y + 0.07,
            body,
            ha="center",
            va="bottom",
            fontsize=body_fs,
            color=TEXT_COLOR,
            linespacing=1.12,
            zorder=3,
        )


def fig1_platform_flow():
    fig, ax = plt.subplots(figsize=(13, 3.6))
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 3.2)
    ax.axis("off")

    boxes = [
        (0.3, 0.75, 2.2, 1.65, "用户多模态输入", "对话 / 语音 / 表情"),
        (3.0, 0.75, 2.2, 1.65, "EmoLLM 情感诊断", "情绪档案与引导"),
        (5.7, 0.75, 2.2, 1.65, "国画匹配或生成", "SD 文生图"),
        (8.4, 0.75, 2.7, 1.65, "视听文协同输出", "画面 + 音乐 + 文本"),
    ]
    for b in boxes:
        box(ax, b[0], b[1], b[2], b[3], b[4], b[5], FS_BOX_TITLE, FS_BOX_TITLE)

    h_arrow(ax, 2.55, 2.95, 1.58)
    h_arrow(ax, 5.25, 5.65, 1.58)
    h_arrow(ax, 7.95, 8.35, 1.58)

    plt.tight_layout()
    plt.savefig(r"D:\moxin\flow_01_platform_main.png", dpi=300, bbox_inches="tight", facecolor="white")
    plt.close()


def fig2_tech_architecture():
    """与 demo_frontend / run_pipeline / doubao_voice / emollm 对齐"""
    fig, ax = plt.subplots(figsize=(16, 18))
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 16)
    ax.axis("off")

    box(
        ax,
        0.6,
        12.6,
        12.8,
        1.75,
        "① 展示层  demo_frontend.py（Streamlit）",
        "全屏国画背景（base64）· 聊天气泡 · 背景音乐循环 + 豆包朗读（HTML5 audio）\n侧栏：run_pipeline.py 路径、deliverables、SD API URL、豆包对话 / TTS 音色",
        FS_BOX_TITLE,
        FS_BOX_BODY_COMPACT,
    )

    box(
        ax,
        0.6,
        10.55,
        12.8,
        1.75,
        "② 对话与朗读（可选）  doubao_voice.py",
        "豆包 Ark：POST ark.cn-beijing.volces.com/api/v3/chat/completions\n火山 TTS：openspeech.bytedance.com/api/v1/tts · loudness_ratio · tts_voices.csv\n失败时回退 _quick_reply 规则",
        FS_BOX_TITLE,
        FS_BOX_BODY_COMPACT,
    )

    box(
        ax,
        0.6,
        8.55,
        12.8,
        1.45,
        "③ 闭环编排",
        "subprocess：python run_pipeline.py --text … --sd-api-url … --save-case-name … --music-duration-sec",
        FS_BOX_TITLE,
        FS_BOX_BODY,
        accent=True,
    )

    v_arrow(ax, 7, 12.6, 12.3)
    v_arrow(ax, 7, 10.55, 10.0)

    box(
        ax,
        0.6,
        5.95,
        6.1,
        2.25,
        "④a 情绪推断  emollm_infer.py",
        "本地 EmoLLM（Transformers）· 设备 cuda/cpu\n解析 JSON：emotion_label ∈ {焦虑,压力,低落,平静,积极}\nintensity 1~5 · guide_text · music_profile · image_style_hint\n失败走 _fallback_rule 关键词规则",
        FS_BOX_TITLE,
        FS_BOX_BODY_COMPACT,
    )
    box(
        ax,
        7.3,
        5.95,
        6.1,
        2.25,
        "④b 模板检索  prompt_selector.py",
        "emotion_to_prompt.csv：style / color_tone / composition / imagery_keywords\nselect_template：同情绪 + 最近强度 · ab_active=1 · A/B/C/D 变体\n输出 positive_prompt / negative_prompt",
        FS_BOX_TITLE,
        FS_BOX_BODY_COMPACT,
    )

    v_arrow(ax, 3.65, 8.55, 8.22)
    v_arrow(ax, 10.35, 8.55, 8.22)

    box(
        ax,
        0.6,
        3.35,
        6.1,
        2.15,
        "⑤a 国画生成  run_pipeline._sd_txt2img",
        "POST {sd_url}/sdapi/v1/txt2img\n768×768 · steps=24 · cfg=6 · sampler DPM++ 2M Karras\n返回 base64 → 解码为 PIPE-xxx.png",
        FS_BOX_TITLE,
        FS_BOX_BODY_COMPACT,
    )
    box(
        ax,
        7.3,
        3.35,
        6.1,
        2.15,
        "⑤b 疗愈音乐  _music_submit_and_query",
        "火山 imagination：GenBGMForTime 提交 TaskID\nQuerySong 轮询至 AudioUrl · HMAC-SHA256 签名（AK/SK）\n时长 clamp [30,120]s · 下载 WAV",
        FS_BOX_TITLE,
        FS_BOX_BODY_COMPACT,
    )

    v_arrow(ax, 3.65, 5.95, 5.52)
    v_arrow(ax, 10.35, 5.95, 5.52)

    box(
        ax,
        0.6,
        0.85,
        12.8,
        2.1,
        "⑥ 输出与日志",
        "_build_soothing_response 共情文案 · 写入 {PIPE}_payload.json（情绪+模板+文案）\noutputs/*.png · *_music.json · *.wav · deliverables/{case}/ 归档\nsmoke_test_log.csv 记录 PIPE 测试与耗时",
        FS_BOX_TITLE,
        FS_BOX_BODY_COMPACT,
    )

    v_arrow(ax, 3.65, 3.35, 2.96)
    v_arrow(ax, 10.35, 3.35, 2.96)

    plt.tight_layout()
    plt.savefig(r"D:\moxin\flow_02_tech_architecture.png", dpi=300, bbox_inches="tight", facecolor="white")
    plt.close()


def fig3_core_algorithm():
    """run_pipeline 主链路逐步展开（Step4/5 并行后汇合 Step6）"""
    fig, ax = plt.subplots(figsize=(15, 15))
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 13)
    ax.axis("off")

    col = [
        (0.5, 10.55, 13, 1.55, "输入", "用户文本 args.text"),
        (
            0.5,
            8.72,
            13,
            1.65,
            "Step 1  infer_emotion()",
            "EmoLLM 自回归生成 → 正则提取首个 JSON → _normalize_result（合法情绪 + 强度裁剪 + 默认 music_profile）",
        ),
        (
            0.5,
            6.82,
            13,
            1.65,
            "Step 2  select_template()",
            "按 emotion_label + intensity 过滤 CSV；无精确强度则最近邻；同强度多行则随机 A/B 变体；得 id / positive_prompt / negative_prompt",
        ),
        (
            0.5,
            4.88,
            13,
            1.6,
            "Step 3  _build_soothing_response()",
            "共情 / 解释 / 行动建议 · 拼接 full_text（供前端或 payload 展示）",
        ),
    ]
    for i, s in enumerate(col):
        accent = i == 0
        box(ax, s[0], s[1], s[2], s[3], s[4], s[5], FS_BOX_TITLE, FS_BOX_BODY_COMPACT, accent=accent)

    box(
        ax,
        0.5,
        2.85,
        6.2,
        1.75,
        "Step 4  SD 文生图",
        "requests POST txt2img\nprompt / negative_prompt / width / height / steps / cfg_scale",
        FS_BOX_TITLE,
        FS_BOX_BODY_COMPACT,
    )
    box(
        ax,
        6.9,
        2.85,
        6.6,
        1.75,
        "Step 5  疗愈音乐",
        "_render_music_prompt(emotion, template)\nGenBGMForTime → 轮询 QuerySong → GET 音频 URL → 本地 WAV",
        FS_BOX_TITLE,
        FS_BOX_BODY_COMPACT,
    )

    box(
        ax,
        0.5,
        0.75,
        13,
        1.85,
        "Step 6  持久化",
        "payload JSON · 图像路径 · music JSON · _append_log(smoke_test_log)\n可选 --save-case-name → deliverables 目录打包",
        FS_BOX_TITLE,
        FS_BOX_BODY_COMPACT,
        accent=True,
    )

    def arrow_down(x, y_bottom_upper, y_top_lower):
        v_arrow(ax, x, y_bottom_upper, y_top_lower)

    arrow_down(7, 10.55, 10.37)
    arrow_down(7, 8.72, 8.37)
    arrow_down(7, 6.82, 6.48)

    y3_bot = 4.88
    y_fork = 4.72
    y45_top = 4.62
    ax.plot([7, 7], [y3_bot, y_fork], color=COLOR_ARROW, lw=2.2)
    ax.plot([3.6, 10.4], [y_fork, y_fork], color=COLOR_ARROW, lw=2.2)
    v_arrow(ax, 3.6, y_fork, y45_top + 0.02)
    v_arrow(ax, 10.4, y_fork, y45_top + 0.02)

    y6_top = 0.75 + 1.85
    y_merge = 2.55
    ax.plot([3.6, 3.6], [2.85, y_merge], color=COLOR_ARROW, lw=2.2)
    ax.plot([10.4, 10.4], [2.85, y_merge], color=COLOR_ARROW, lw=2.2)
    ax.plot([3.6, 10.4], [y_merge, y_merge], color=COLOR_ARROW, lw=2.2)
    v_arrow(ax, 7, y_merge, y6_top + 0.02)

    plt.tight_layout()
    plt.savefig(r"D:\moxin\flow_03_core_algorithm.png", dpi=300, bbox_inches="tight", facecolor="white")
    plt.close()


def fig4_technical_roadmap():
    """立项申请书：五阶段技术路线（单页横向）"""
    fig, ax = plt.subplots(figsize=(20, 5.2))
    ax.set_xlim(0, 19.2)
    ax.set_ylim(0, 5)
    ax.axis("off")

    fs_t, fs_b = 14, 9.8
    y, w, h = 1.0, 3.05, 2.55
    gap = 0.38
    x0 = 0.35

    stages = [
        (
            "阶段1 数据与规范制备",
            "国画筛选与素材授权\n标注规范与伦理说明\n情绪–美学三元数据雏形",
            False,
        ),
        (
            "阶段2 情绪推断与模板",
            "EmoLLM 情绪结构化输出\nemotion_to_prompt.csv\n正/负向 prompt 与疏导文案",
            False,
        ),
        (
            "阶段3 视觉/音频生成",
            "SD WebUI txt2img\n火山 BGM 异步生成\n音视频与 payload 落盘",
            False,
        ),
        (
            "阶段4 系统集成与评测",
            "Streamlit 与 run_pipeline\n场景用例与 smoke 日志\n可用性/主观量表评测",
            True,
        ),
        (
            "阶段5 试点与迭代",
            "校内或合作单位试点\n用户反馈回收\n模板库与管线迭代",
            False,
        ),
    ]

    centers_y = y + h / 2
    for i, (title, body, accent) in enumerate(stages):
        xi = x0 + i * (w + gap)
        box(ax, xi, y, w, h, title, body, title_fs=fs_t, body_fs=fs_b, accent=accent)
        if i > 0:
            x_left = x0 + (i - 1) * (w + gap) + w
            x_right = xi
            h_arrow(ax, x_left, x_right, centers_y)

    plt.tight_layout()
    plt.savefig(r"D:\moxin\flow_04_technical_roadmap.png", dpi=300, bbox_inches="tight", facecolor="white")
    plt.close()


def fig5_full_project_technical_route():
    """
    四区块技术路线；纵轴收紧、底栏上移，减少底部留白并放大框体与字号。
    """
    fig, ax = plt.subplots(figsize=(18, 13.2))
    ax.set_xlim(0, 20)
    ax.set_ylim(0.02, 13.28)
    ax.axis("off")

    # 一、背景研究
    region_bg(ax, 0.35, 11.82, 19.3, 1.2, "#C5DDF0", 0.45)
    ax.text(0.5, 12.98, "一、背景研究路线", fontsize=12.5, fontweight="bold", color=COLOR_MAIN)
    bx, bw, bh, yy = 0.85, 4.45, 0.85, 11.9
    gap = 0.26
    top_row = [
        ("政策文件解读", "健康中国等政策锚点"),
        ("国内外研究现状", "情感计算 / 艺术疗愈文献"),
        ("数据与坐标设计", "国画元数据与情绪维度"),
        ("对比与创新点", "东方美学坐标 vs 同类系统"),
    ]
    for i, (t, b) in enumerate(top_row):
        xi = bx + i * (bw + gap)
        mini_box(ax, xi, yy, bw, bh, t, b, "#E8F4FC", title_fs=10, body_fs=8.1)
        if i < len(top_row) - 1:
            h_arrow(ax, xi + bw, xi + bw + gap, yy + bh * 0.42)

    y_col_lo = 0.38
    h_col = 11.22
    region_bg(ax, 0.35, y_col_lo, 3.9, h_col, "#EDE7F6", 0.35)
    region_bg(ax, 4.38, y_col_lo, 9.05, h_col, "#FFF0E0", 0.35)
    region_bg(ax, 13.52, y_col_lo, 6.15, h_col, "#E8F5E9", 0.35)

    ax.text(0.5, 11.12, "二、市场调查", fontsize=12.5, fontweight="bold", color=COLOR_MAIN)
    ax.text(4.48, 11.12, "三、技术实现", fontsize=12.5, fontweight="bold", color=COLOR_MAIN)
    ax.text(13.62, 11.12, "四、项目实现", fontsize=12.5, fontweight="bold", color=COLOR_MAIN)

    # 二、市场调查
    col_x, cw, ch = 0.48, 3.52, 1.48
    y0 = 9.02
    xc_m = col_x + cw / 2
    mkt = [
        ("确定课题", "国画情绪支持与共感交互"),
        ("问卷调查", "青年情绪 / 审美偏好等"),
        ("验证场景价值", "高校 / 社区轻量试点"),
        ("推广与迭代计划", "演示包与反馈渠道"),
    ]
    cy = y0
    gap_m = 0.18
    for i, (t, b) in enumerate(mkt):
        mini_box(ax, col_x, cy, cw, ch, t, b, "#F3E5F5", title_fs=10.2, body_fs=8.2)
        if i < len(mkt) - 1:
            next_cy = cy - ch - gap_m
            v_arrow(ax, xc_m, cy, next_cy + ch)
            cy = next_cy

    # 三、技术实现（自下而上：底栏贴近 y_col_lo，整体放大）
    mx = 4.48
    mw, mh = 2.78, 1.28
    gap_w = 0.2
    y_ft = 0.42
    h_ft = 1.38
    mini_box(
        ax,
        mx,
        y_ft,
        8.48,
        h_ft,
        "模型与模板优化",
        "CSV / prompt 规则迭代 · smoke 回归\n（可选）SD LoRA — 非通义万相主线",
        "#F5F5F5",
        title_fs=10.5,
        body_fs=8.2,
    )

    y_ds = y_ft + h_ft + 0.2
    dh = 1.1
    dw = 1.96
    dx0 = mx
    gdw = 0.15
    ds = [
        ("收集国画", "授权与高清素材"),
        ("建立坐标", "东方美学情感轴"),
        ("国画—情感测试", "被试标注/体验"),
        ("对齐模板库", "emotion_to_prompt"),
    ]
    for i, (t, b) in enumerate(ds):
        mini_box(ax, dx0 + i * (dw + gdw), y_ds, dw, dh, t, b, "#FCE4EC", title_fs=9.2, body_fs=7.6)
        if i < len(ds) - 1:
            h_arrow(ax, dx0 + i * (dw + gdw) + dw, dx0 + (i + 1) * (dw + gdw), y_ds + dh * 0.42)

    y_int = y_ds + dh + 0.26
    h_int = 1.32
    mini_box(
        ax,
        mx,
        y_int,
        8.48,
        h_int,
        "模块整合",
        "侧栏 SD URL、run_pipeline 路径、deliverables\n豆包 Ark 对话 · 火山 TTS（可选）",
        "#FFF3E0",
        title_fs=10.8,
        body_fs=8.2,
    )

    y_fe = y_int + h_int + 0.26
    h_fe = 1.22
    mini_box(
        ax,
        mx,
        y_fe,
        8.48,
        h_fe,
        "前端 Streamlit",
        "demo_frontend：国画 base64 背景\n对话区 · HTML5 音频",
        "#FFF8E1",
        title_fs=10.8,
        body_fs=8.2,
    )
    v_arrow(ax, mx + 4.25, y_fe, y_int + h_int)

    y_pipe = y_fe + h_fe + 0.26
    h_pipe = 1.08
    mini_box(
        ax,
        mx + 0.75,
        y_pipe,
        6.05,
        h_pipe,
        "run_pipeline 闭环编排",
        "subprocess · CSV 模板 · payload/日志",
        "#FFE0B2",
        title_fs=11,
        body_fs=8.4,
    )

    my = y_pipe + h_pipe + 0.26
    mini_box(ax, mx, my, mw, mh, "EmoLLM（本地）", "文本→情绪 JSON\nemollm_infer", "#FFECB3", title_fs=10.5, body_fs=8.5)
    mini_box(ax, mx + mw + gap_w, my, mw, mh, "SD WebUI", "txt2img API\n国风 prompt", "#FFECB3", title_fs=10.5, body_fs=8.5)
    mini_box(ax, mx + 2 * (mw + gap_w), my, mw, mh, "火山 BGM", "GenBGMForTime\nQuerySong·WAV", "#FFECB3", title_fs=10.5, body_fs=8.5)
    for k in range(3):
        xc_k = mx + k * (mw + gap_w) + mw / 2
        v_arrow(ax, xc_k, my, y_pipe + h_pipe)

    # 四、项目实现
    gx, gw, gh = 13.52, 5.85, 1.42
    gy = 9.05
    xg = gx + gw / 2
    gap_g = 0.16
    impl = [
        ("「国画—情感」数据集", "标注规范与小样本集"),
        ("视觉与配乐管线固化", "SD + 火山接口与模板"),
        ("Streamlit + 流水线试点", "校内演示与用例"),
        ("场景试用与反馈", "心理/艺术机构意向对接"),
        ("可扩展工作流", "模块化后端 · 非多 Agent 堆叠"),
    ]
    for i, (t, b) in enumerate(impl):
        mini_box(ax, gx, gy, gw, gh, t, b, "#E8F5E9", title_fs=10.2, body_fs=8)
        if i < len(impl) - 1:
            next_gy = gy - gh - gap_g
            v_arrow(ax, xg, gy, next_gy + gh)
            gy = next_gy

    plt.tight_layout()
    plt.savefig(r"D:\moxin\flow_05_project_technical_route.png", dpi=300, bbox_inches="tight", facecolor="white")
    plt.close()


if __name__ == "__main__":
    fig1_platform_flow()
    fig2_tech_architecture()
    fig3_core_algorithm()
    fig4_technical_roadmap()
    fig5_full_project_technical_route()
    print(
        "OK: flow_01_platform_main.png, flow_02_tech_architecture.png, "
        "flow_03_core_algorithm.png, flow_04_technical_roadmap.png, flow_05_project_technical_route.png"
    )
