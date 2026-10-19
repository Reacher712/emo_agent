# 豆包对话 + 语音朗读 接入指南

聊天现支持 DeepSeek 和豆包切换，与语音服务独立。使用 DeepSeek 时配置 `CHAT_PROVIDER=deepseek`、`DEEPSEEK_API_KEY`、`DEEPSEEK_MODEL=deepseek-flash`；接口固定为官方 `https://api.deepseek.com/chat/completions`，默认关闭思考模式以降低聊天等待时间。无需安装额外 SDK。2026-10-19 已完成真实 API 调用，以及对话界面中 DeepSeek 回复接新版豆包语音的连通验证。

## 当前推荐：新版语音控制台

2026-10-19 已接通新版 API Key 认证和 V3 HTTP 流式合成。聊天与语音使用各自服务的凭证。

在当前应用目录 `.env` 中填写：

```env
TTS_API_KEY=你的语音专用API_Key
TTS_RESOURCE_ID=seed-tts-2.0
TTS_V3_SPEAKER=zh_female_vv_uranus_bigtts
```

使用 [语音控制台](https://console.volcengine.com/speech/app) 的 API Key 管理创建凭证，并在同一项目开通语音合成 2.0。`TTS_API_KEY` 非空时优先使用新版接口，音色下拉框会使用配置的 2.0 音色；不需要旧版 APP ID、Token 或声音复刻。

代码等待成功结束帧后才保存音频，响应中断或服务报错不会把不完整音频当成功。接口说明：[官方 HTTP 单向流式合成](https://docs.volcengine.com/docs/DoubaoVoice/unidirectional-streaming-text-to-speech-http?lang=zh)。

以下保留旧版接入说明；使用旧版时 `TTS_API_KEY` 必须留空，旧文档中的 `D:\moxin` 替换为当前应用目录。

## 功能说明

- **豆包对话**：用豆包大模型生成更有温度、更自然的回复，替代规则式关键词回复
- **语音朗读**：用火山引擎 TTS 将助手回复转为语音播放
- **声音复刻**：可选，使用你定制的音色（需在控制台预先创建）

## 一、豆包对话 API

1. 登录 [火山引擎 Ark 控制台](https://console.volcengine.com/ark)
2. 开通豆包模型，创建 API Key
3. 在 `.env` 中设置：
   ```
   DOUBAO_API_KEY=你的API_Key
   DOUBAO_MODEL_ID=ep-xxx  # 可选，不填则用默认
   ```

## 二、豆包语音 TTS

- **接口**：`https://openspeech.bytedance.com/api/v1/tts`（V1 HTTP 一次性合成）
- **文档**：https://www.volcengine.com/docs/6561/1257584
- **认证**：`Authorization: Bearer;${Access_Token}`
- **控制台**：语音合成大模型 → 服务详情 → 复制 APP ID、Access Token
- **音色**：V1 不支持豆包语音2.0音色，请用 [音色列表](https://www.volcengine.com/docs/6561/1257544) 中的 voice_type

## 三、两种固定音色（无需复杂克隆）

在 `.env` 中配置：
```
TTS_VOICE_1=zh_female_shuangkuaisisi_moon_bigtts   # 女声
TTS_VOICE_2=zh_male_wanquanhao_bigtts              # 男声
```

- **用预设音色**：直接填上表中的发音人 ID，见 [音色列表](https://www.volcengine.com/docs/6561/79824)
- **用自己的两段音频**：在控制台分别上传两段音频，做声音复刻，得到两个 speaker_id 后填入 `TTS_VOICE_1` 和 `TTS_VOICE_2`

系统会在奇数轮用 VOICE_1，偶数轮用 VOICE_2，自动交替朗读。

## 四、依赖安装

```bash
pip install requests python-dotenv
```

## 五、前端使用

启动 `streamlit run demo_frontend.py` 后，在左侧栏勾选：
- **使用豆包 API 生成回复**
- **启用语音朗读**

若未配置，勾选后也会回退到规则回复，TTS 不生效。
