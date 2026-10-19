# 豆包对话 + 语音朗读 接入指南

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
