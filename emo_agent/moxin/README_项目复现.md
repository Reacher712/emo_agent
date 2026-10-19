# 听山——多模态情绪陪伴空间

本地运行与配置说明

本说明对应原项目，不包含三 Agent 改造。2026-10-19 已在当前电脑验证本地情绪推理、SDXL + 山水 LoRA 出图、新版语音合成，以及 DeepSeek 聊天回复接语音朗读的界面链路。火山纯音乐后付费接口已完成 30 秒音频提交、查询和下载，并通过本地情绪识别→SDXL→音乐的串联测试。

## 当前电脑启动

在仓库根目录的 PowerShell 中，分别打开终端运行：

```powershell
# 本地 SDXL API，地址 http://127.0.0.1:7860/docs
.\start_local.ps1 -Mode Image
# 门户，地址 http://127.0.0.1:8501
.\start_local.ps1 -Mode Portal
# 可选：原国画背景对话演示，地址 http://127.0.0.1:8502
.\start_local.ps1 -Mode Demo
```

启动脚本在前台运行，按 Ctrl+C 停止对应服务。端口已有服务时不必重复启动。如果执行策略拦截脚本，可用 `powershell -ExecutionPolicy Bypass -File .\start_local.ps1 -Mode Image`，仅对该进程生效。

门户进入“疗愈对话”，打开“尝试调用完整闭环”，保留“仅运行本地出图（跳过音乐 API）”。发送文字后执行本地情绪识别和出图，结果显示在对话中。Demo 默认也跳过音乐，豆包和 TTS 需手动开启。

当前电脑的音乐凭证已配置并验证；需要生成音乐时，取消“仅运行本地出图（跳过音乐 API）”。Demo 先聊天，再点击“生成新的国画背景与音乐”。完整测试结果位于 `outputs/full-connection-test`，12 步、768×768 图像加 30 秒音乐本次约 46 秒，耗时会随模型状态及远端排队变化。

Demo 音频由一个组件统一控制：生成音乐替换旧背景音乐；朗读期间暂停背景音乐，结束后按用户开关恢复；普通页面重绘不重播旧朗读。页面提供背景音乐开关和朗读重播按钮。同一浏览器、同一站点的多个新版对话页通过 BroadcastChannel 避免同时播放。更新前已打开的旧页面需刷新或关闭，才能停用旧的独立播放器。

如果电脑休眠或切换显卡状态后，出图返回 `CUDA error: unknown error`，停止并重新启动 Image 服务以重建 GPU 上下文。本次发现该问题后，重启出图服务即恢复；不需要为此重新安装模型或更换 API Key。

## 两个独立环境

| 用途 | 环境 | 已验证版本 |
|---|---|---|
| 门户、对话、情绪模型 | 仓库根目录 `.venv`，Python 3.11 | torch 2.9.0+cpu、transformers 4.46.3；界面依赖见 requirements-repro.txt |
| WebUI / SDXL | `emo_agent/stable-diffusion-webui/venv`，Python 3.10.20 | torch 2.9.0+cu130、torchvision 0.24.0+cu130、gradio 3.41.2、transformers 4.30.2 |

小型情绪模型使用 CPU，GPU 留给 SDXL。WebUI 环境通过修复 `venv/pyvenv.cfg` 的 home 恢复，解释器位于仓库 `.runtimes`；旧配置保存在同目录 `pyvenv.cfg.before-local-repair`。这些环境均不会进入 Git，不能直接复制到另一台电脑使用。

新建应用环境：

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r .\emo_agent\moxin\requirements-repro.txt
.\.venv\Scripts\python.exe -m pip install -r .\emo_agent\moxin\requirements-local-model.txt
```

WebUI 启动脚本直接运行 `webui.py`，复用原依赖和 repositories，仅启用内置扩展。不要直接运行旧 `launch.py` 自动安装流程，它默认安装的旧版 torch 不适合当前显卡。新电脑仍需单独安装 WebUI 依赖及与显卡兼容的 CUDA 版 PyTorch，不能只靠启动脚本复原现有环境。

## 本地资源

- 情绪模型：`emo_agent/moxin/EmoLLM/model`，配置为 Qwen1.5-0.5B-Chat；仅从本地加载，不自动下载。
- SDXL：`emo_agent/stable-diffusion-webui/models/Stable-diffusion/sd_xl_base_1.0.safetensors`。
- LoRA：`emo_agent/stable-diffusion-webui/models/Lora/landscape-painting-sdxl_v2 (1).safetensors`。
- 原模型较小，能运行不代表情绪判断或结构化输出已经可靠，仍保留原规则降级。

模型文件、WebUI 的外部依赖仓库、生成记录和缓存均已忽略，克隆 GitHub 仓库后需另行准备。

## 不调用云服务的端到端验证

先启动 Image 服务，再进入 `emo_agent/moxin`：

```powershell
& "..\..\.venv\Scripts\python.exe" run_pipeline.py --text "最近任务很多，感觉压力很大" --skip-music --ab-variant A --sd-seed 42 --output-dir outputs/local-runtime-check --log-csv outputs/local-runtime-check/smoke_test_log.csv
```

返回 `status: success` 且 `music_skipped: true` 表示本地识别与出图完成。失败返回非零退出码；成功时保存图片、输入结果和 `.metadata.json`（实际 seed、底模、LoRA 哈希和参数）。示例首轮 768×768、12 步、seed 42 在本机约 15 秒，非性能承诺。

## 云端服务

配置文件为应用目录 `.env`，通过 python-dotenv 加载，已有进程环境变量优先。不要将真实凭证提交到 Git。

- 云端聊天：设置 `CHAT_PROVIDER=deepseek`，填写 `DEEPSEEK_API_KEY` 和 `DEEPSEEK_MODEL=deepseek-flash`。也可设为 `doubao`，使用 `DOUBAO_API_KEY`、`DOUBAO_MODEL_ID`。两个前端都提供“启用云端聊天”开关；失败会明确标记本地规则降级，不自动跨服务发送请求。
- 音乐：当前使用 `MUSIC_AUTH_MODE=volc_aksk`，需要 `VOLC_ACCESS_KEY_ID`、`VOLC_SECRET_ACCESS_KEY`，并开通纯音乐生成服务；`GenBGMForTime` 对应按时长计费，套餐接口为 `GenBGM`，不能混用。
- 新版语音：`TTS_API_KEY`、`TTS_RESOURCE_ID=seed-tts-2.0`、`TTS_V3_SPEAKER`；已适配 V3 HTTP 流式接口。设置新版 Key 时优先走 V3，默认音色为 `zh_female_vv_uranus_bigtts`。
- 旧版 TTS V1 仍可使用 `TTS_APP_ID`、`TTS_TOKEN`、`TTS_CLUSTER` 和已授权的 1.0 音色，前提是 TTS_API_KEY 留空。两种凭证不要互换。

官方入口：

- [DeepSeek API Key](https://platform.deepseek.com/api_keys)
- [方舟 API Key](https://console.volcengine.com/ark/apiKey)
- [豆包语音控制台](https://console.volcengine.com/speech/app)
- [音乐服务控制台](https://console.volcengine.com/ai-music/product)
- [音乐服务开通说明](https://docs.volcengine.com/docs/Audiovideounderstandingandprocessing/ConsoleServiceActivationGuide?lang=zh)
- [音乐 AK/SK 管理](https://console.volcengine.com/iam/keymanage)

先分别验证单服务，再关闭“跳过音乐”运行云端链路。
