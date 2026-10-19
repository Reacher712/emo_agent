# .env 填写说明

## 一、豆包对话（已配置 ✅）

| 变量 | 说明 | 你的值 |
|------|------|--------|
| DOUBAO_API_KEY | 豆包 API Key（Bearer Token） | 已填 |
| DOUBAO_MODEL_ID | 模型 ID | doubao-1-5-pro-32k-250115 |

## 二、豆包语音 TTS（朗读）— 还需补充

| 变量 | 说明 | 获取方式 |
|------|------|----------|
| TTS_APP_ID | 应用 ID | 已填 4381278990 |
| **TTS_TOKEN** | Access Token | **需填写**：语音合成大模型控制台 → 服务接口认证信息 → 点 Access Token 旁 👁 复制 |
| TTS_CLUSTER | 集群 | 保持 volcano_tts（若控制台有不同值则改） |
| TTS_VOICE_1 | 女声音色 ID | 默认即可，报错 3050 时再改 |
| TTS_VOICE_2 | 男声音色 ID | 默认即可，报错 3050 时再改 |

## 三、填写示例

```env
# 把下面这行的空字符串换成你复制的 Access Token
TTS_TOKEN=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
```

Token 通常是一段 UUID 格式字符串，复制后直接粘贴，**不要加引号**。

## 四、403「requested resource not granted」说明

说明：当前账号没有对应**音色**的调用权限，需在控制台**下单/授权音色**。

操作步骤：
1. 进入 **语音合成大模型** 控制台
2. 找到 **「音色详情」**、**「资源包」** 或 **「音色下单」**
3. 选择试用/免费音色，进行 **0 元下单**（即使免费也需完成下单）
4. 下单后，在 **音色详情** 中查看可用音色的 **voice_type**（如 BV001_streaming）
5. 将可用音色 ID 填入 `.env` 的 `TTS_VOICE_1`、`TTS_VOICE_2`

当前已临时改为 `BV001_streaming`、`BV002_streaming`（文档说明无需单独下单），若仍 403，请按上述步骤在控制台完成音色授权。

## 五、检查清单

- [ ] TTS_TOKEN 已从控制台复制并粘贴
- [ ] 服务已点击「开通」
- [ ] 音色已下单/授权（含 0 元试用）
- [ ] 运行测试：`python -c "from doubao_voice import tts_with_voice; p,e=tts_with_voice('测试'); print('OK' if p else e)"`
