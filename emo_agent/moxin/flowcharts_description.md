# 墨韵心调 · 流程图文字说明

本文档与 `flow_01_platform_main.png`、`flow_02_tech_architecture.png`、`flow_03_core_algorithm.png` 对应，对每张图作**逐块、可独立引用**的详细说明，便于写入报告、答辩稿或产品说明。

---

## 图 1：平台主流程（`flow_01_platform_main.png`）

### 1.1 总体含义

图 1 从**业务视角**概括「墨韵心调」闭环：用户侧输入 → 情感理解与引导 → 与情绪匹配的国画生成 → 多模态协同输出。不展开具体文件名与 API，突出**价值链条**。

### 1.2 从左到右四个阶段

**（1）用户多模态输入**

- 支持**对话文本**作为主线输入；设计上可扩展**语音**、**表情**等多模态信号，与「情感—内容」闭环一致。
- 该节点表示：系统感知层接收用户状态与表达，是后续诊断与生成的前提。

**（2）EmoLLM 情感诊断**

- 使用 **EmoLLM** 对用户输入进行**情绪与心理状态**的建模，形成可机器处理的情绪档案，并产生**引导性语义**（如疏导方向、关注维度），供后续模板与文案使用。
- 在业务表述上对应「情感诊断」而非单纯分类标签。

**（3）国画匹配或生成**

- 在情绪与引导信息确定后，系统通过 **Stable Diffusion 文生图**路径，生成与当前情绪、审美风格相匹配的**国画风画面**（流程图中概括为「国画匹配或生成 / SD 文生图」）。
- 强调「匹配」指与情绪模板、画风约束一致；「生成」指按需实时出图。

**（4）视听文协同输出**

- **画面**：上述生成的国画图像。
- **音乐**：与情绪画像、时长策略相关的疗愈/背景音乐（在技术架构图中由火山音乐链路实现）。
- **文本**：共情说明、解释与行动建议等舒缓文案（由流水线中的文案构建步骤产出）。

### 1.3 数据流关系

箭头表示**严格顺序依赖**：没有用户输入则无法诊断；没有诊断结果则难以稳定驱动画风与配乐策略；最终用户感知的是「画 + 声 + 文」的一体化体验。

---

## 图 2：系统技术架构（`flow_02_tech_architecture.png`）

### 2.1 总体含义

图 2 描述 **D:\moxin 仓库中已实现模块**的分层结构：从 **Streamlit 前端**、可选 **豆包 + TTS**，经 **子进程调用 `run_pipeline.py`**，到 **本地 EmoLLM**、**CSV 模板**、**SD WebUI API**、**火山音乐 API**，最后落到**文件与日志**。自上而下对应「展示 → 编排 → 推理与检索 → 外部服务 → 持久化」。

### 2.2 ① 展示层：`demo_frontend.py`（Streamlit）

- **界面**：全屏展示国画背景（图像以 **base64** 等形式嵌入页面）；聊天气泡承载多轮对话。
- **媒体**：背景音乐循环播放；若启用朗读，通过 **HTML5 audio** 播放豆包 TTS 返回的音频。
- **配置侧栏**：可配置 `run_pipeline.py` 路径、`deliverables` 目录、**Stable Diffusion WebUI** 的 API 根地址（`sd-api-url`）、是否启用豆包对话、TTS 音色等，使同一前端可对接不同本机/局域网服务。

### 2.3 ② 对话与朗读（可选）：`doubao_voice.py`

- **豆包对话**：通过火山方舟 **Ark** 接口（如 `POST .../api/v3/chat/completions`）完成多轮对话补全。
- **火山 TTS**：调用字节开放语音合成接口（如 `openspeech.bytedance.com/api/v1/tts`），支持响度等参数；音色可参考 **`tts_voices.csv`** 维护的列表。
- **降级**：当云端对话或 TTS 不可用时，可回退到本地 **`_quick_reply`** 规则回复，保证演示连续性。

### 2.4 ③ 闭环编排

- 前端通过 **`subprocess`** 启动独立进程：`python run_pipeline.py`，并传入 **`--text`**（用户文本）、**`--sd-api-url`**、可选 **`--save-case-name`**（案例归档名）、**`--music-duration-sec`**（音乐时长）等参数。
- 该层将「一次用户提交」映射为「一次完整离线/准离线流水线执行」，避免阻塞 Streamlit 主线程过久时可配合定时或异步策略（具体以 `demo_frontend` 实现为准）。

### 2.5 ④a 情绪推断：`emollm_infer.py`

- **模型**：本地 **EmoLLM**，基于 **Transformers**，推理设备可为 **CUDA** 或 **CPU**。
- **输出结构**：解析为 JSON，字段包括 **`emotion_label`**（取值在焦虑、压力、低落、平静、积极等集合内）、**`intensity`**（1～5）、**`guide_text`**、**`music_profile`**、**`image_style_hint`** 等，供模板与音乐 prompt 使用。
- **鲁棒性**：若解析失败，走 **`_fallback_rule`** 等关键词规则兜底，避免流水线中断。

### 2.6 ④b 模板检索：`prompt_selector.py`

- **数据**：**`emotion_to_prompt.csv`** 维护画风、色调、构图、意象关键词等列，支撑国画 prompt 组合。
- **逻辑**：**`select_template`** 按「同情绪 + 最近强度」匹配；仅启用 **`ab_active=1`** 的行；同一情绪强度下可有 **A/B/C/D** 等变体以增加多样性。
- **输出**：**`positive_prompt`**、**`negative_prompt`**，直接用于 SD 与后续文案上下文。

### 2.7 ⑤a 国画生成：`run_pipeline._sd_txt2img`

- **协议**：对 `{sd_url}/sdapi/v1/txt2img` 发起 **HTTP POST**（与 Automatic1111 WebUI API 约定一致）。
- **典型参数**（与实现一致时）：分辨率如 **768×768**，**steps=24**，**cfg=6**，采样器 **DPM++ 2M Karras** 等。
- **结果**：响应中的 **base64** 图像解码后保存为 **`PIPE-xxx.png`** 一类文件，供前端展示与归档。

### 2.8 ⑤b 疗愈音乐：`_music_submit_and_query`

- **服务**：火山 **imagination** 侧 **GenBGMForTime** 提交任务，获得 **TaskID**。
- **查询**：**QuerySong** 轮询直至返回 **AudioUrl**；请求使用 **HMAC-SHA256** 与 **AK/SK** 签名。
- **时长**：请求时长 **clamp** 在 **[30, 120] 秒**区间内；音频下载为 **WAV** 等到本地。

### 2.9 ⑥ 输出与日志

- **文案**：**`_build_soothing_response`** 生成共情与行动建议类文本。
- **结构化落盘**：写入 **`{PIPE}_payload.json`**，汇总情绪、模板信息与文案等。
- **资产**：**`outputs/*.png`**、**`*_music.json`**、**`*.wav`**；若指定案例名，则归入 **`deliverables/{case}/`**。
- **测试记录**：**`smoke_test_log.csv`** 记录 PIPE 运行与耗时等，便于回归与演示追溯。

### 2.10 层间关系小结

- ①② 主要服务人机交互；③ 是控制面；④a④b 是「语义 + 模板」核心；⑤a⑤b 是两个并行外部能力；⑥ 统一落盘。图 2 中竖向箭头表示**主序依赖**，④ 到 ⑤ 的分叉表示**情绪/模板结果同时驱动**图像与音乐两条链路。

---

## 图 3：闭环流水线核心算法（`flow_03_core_algorithm.png`，`run_pipeline.py`）

### 3.1 总体含义

图 3 将 **`run_pipeline.py`** 内部逻辑展开为**可执行步骤**：前半段为**串行**的情绪推断、模板选择、舒缓文案构建；中段**分叉**为 **SD 文生图**与**疗愈音乐**两条并行支路；末段**汇合**为持久化与日志。与图 2 相比，图 3 强调**算法顺序与并行汇合**，而非模块所属文件。

### 3.2 输入

- 用户文本由命令行参数 **`args.text`** 传入，作为 EmoLLM 与全流程的唯一主输入（若前端集成，则对应用户当前轮输入）。

### 3.3 Step 1：`infer_emotion()`

- 调用 **EmoLLM** 自回归生成，从模型输出中用正则等方式提取**首个合法 JSON**。
- **`_normalize_result`**：校验情绪标签合法性、将强度裁剪到约定范围、在缺失时补全默认 **`music_profile`** 等，保证下游 **CSV 匹配**与音乐 prompt 稳定。

### 3.4 Step 2：`select_template()`

- 以 **`emotion_label`** 与 **`intensity`** 为主键过滤 **`emotion_to_prompt.csv`**。
- 若无完全匹配强度，则取**数值上最近**的强度行；若仍有多行（如 A/B 变体），则**随机**选一，得到 **`id`**、**`positive_prompt`**、**`negative_prompt`**。

### 3.5 Step 3：`_build_soothing_response()`

- 生成**共情、解释、行动建议**等结构化或半结构化文案，并拼接 **`full_text`**，供前端展示或写入 **payload**，与「疗愈对话」产品形态对齐。

### 3.6 Step 4 与 Step 5：并行支路

**Step 4：SD 文生图**

- 使用 **`requests`** 对 WebUI 的 **`txt2img`** 端点 POST，提交 **prompt**、**negative_prompt**、**width/height**、**steps**、**cfg_scale** 等，与图 2 中 ⑤a 一致。

**Step 5：疗愈音乐**

- **`_render_music_prompt`**：根据当前情绪字典与选中模板构造音乐侧 prompt。
- 调用 **GenBGMForTime** 提交异步任务，再 **轮询 QuerySong**，拿到音频 URL 后 **GET** 下载为本地 **WAV**。

两路在逻辑上**互不阻塞语义**（实现上可为顺序或异步，以代码为准）；图中用「分叉—汇合」强调**输出物并列产生**。

### 3.7 Step 6：持久化

- 将 **payload JSON**（情绪、模板、路径、文案等）、**图像路径**、**music 元数据 JSON** 等写盘；调用 **`_append_log`** 追加 **`smoke_test_log.csv`**。
- 若传入 **`--save-case-name`**，将相关产物打包进 **`deliverables`** 下对应目录，便于案例演示与复现。

### 3.8 与图 1、图 2 的对应关系

| 概念 | 图 1（业务） | 图 3（算法） |
|------|----------------|----------------|
| 情感诊断 | EmoLLM 情感诊断 | Step 1～2 + 模板 |
| 国画 | 国画匹配或生成 | Step 4 |
| 音乐 | 视听文中的「乐」 | Step 5 |
| 文本引导 | 视听文中的「文」 | Step 3 + payload |

---

## 附录：文件与图对应关系

| 流程图文件 | 脚本中的生成函数 | 侧重 |
|------------|------------------|------|
| `flow_01_platform_main.png` | `fig1_platform_flow` | 产品级主流程 |
| `flow_02_tech_architecture.png` | `fig2_tech_architecture` | 模块、API、数据文件 |
| `flow_03_core_algorithm.png` | `fig3_core_algorithm` | `run_pipeline` 步骤与并行 |

重新出图命令（在 `D:\moxin` 下）：

```bash
python generate_flowcharts.py
```

---

*文档内容与 `generate_flowcharts.py` 中当前框图文案保持一致；若脚本中的技术参数或模块名有变更，请同步更新本说明相应段落。*
