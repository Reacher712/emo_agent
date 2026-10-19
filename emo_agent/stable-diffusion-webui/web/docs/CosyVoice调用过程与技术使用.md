# CosyVoice 调用过程与技术使用

## 概述

CosyVoice 是阿里巴巴推出的语音合成和克隆模型，在本项目中用于音频克隆功能。本文档详细介绍了 CosyVoice API 的调用过程、技术实现和使用方法。

## 技术架构

### API 端点
- **本地服务**: `http://127.0.0.1:50000`
- **创空间服务**: `https://funaudiollm-fun-cosyvoice3-0-5b.ms.show`
- **接口类型**: Gradio API（基于 HTTP/WebSocket）

### 服务模式

项目支持两种服务模式：

1. **本地服务**（优先）:
   - 需要本地部署 CosyVoice 服务
   - 地址：`http://127.0.0.1:50000`
   - 优势：速度快、无网络限制、可自定义

2. **创空间服务**（备用）:
   - 使用 ModelScope 创空间提供的服务
   - 地址：`https://funaudiollm-fun-cosyvoice3-0-5b.ms.show`
   - 优势：无需本地部署、开箱即用

## API 端点

### 1. 生成随机种子

**端点**: `/generate_seed`

**方法**: `POST`

**请求**:
```javascript
const response = await fetch(`${API_BASE}/generate_seed`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ data: [] })
});
```

**响应**:
```json
{
  "data": [12345678]
}
```

### 2. 语音识别

**端点**: `/prompt_wav_recognition` (上传) 或 `/prompt_wav_recognition_1` (录制)

**方法**: `POST`

**请求**:
```javascript
const formData = new FormData();
formData.append('data', JSON.stringify([null]));
formData.append('files', audioFile);

const response = await fetch(`${API_BASE}/prompt_wav_recognition`, {
  method: 'POST',
  body: formData
});
```

**响应**:
```json
{
  "data": ["识别出的文本内容"]
}
```

### 3. 生成音频

**端点**: `/generate_audio`

**方法**: `POST`

**请求参数**:
```javascript
const formData = new FormData();
formData.append('data', JSON.stringify([
  tts_text,              // 要合成的文本
  mode_checkbox_group,   // 推理模式："3s极速复刻" 或 "自然语言控制"
  prompt_text,           // Prompt 文本（可选）
  null,                  // prompt_wav_upload 占位
  null,                  // prompt_wav_record 占位
  instruct_text,         // 指令文本（可选）
  seed,                  // 随机种子
  stream                 // 是否流式返回："true" 或 "false"
]));
formData.append('files', audioFile); // 参考音频文件
formData.append('files', audioFile); // 需要添加两次
```

## 调用流程

### 1. 服务连接检测

```javascript
async function updateApiBase() {
  const apiUrlInput = document.getElementById('api-url');
  let newApiBase = apiUrlInput.value.trim() || 'http://127.0.0.1:50000';
  
  // 尝试连接本地服务
  try {
    const response = await fetch(`${newApiBase}/`);
    if (response.ok) {
      API_BASE = newApiBase;
      isLocalServiceConnected = true;
      log(`API地址更新为: ${API_BASE} (本地服务)`, 'info');
      return;
    }
  } catch (error) {
    log(`连接本地服务失败: ${error.message}，尝试连接创空间`, 'warning');
  }
  
  // 如果本地服务连接失败，回退到创空间
  API_BASE = 'https://funaudiollm-fun-cosyvoice3-0-5b.ms.show';
  isLocalServiceConnected = false;
  log(`API地址更新为: ${API_BASE} (创空间服务)`, 'info');
}
```

### 2. 生成随机种子

```javascript
async function generateSeed() {
  try {
    const response = await fetch(`${API_BASE}/generate_seed`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ data: [] })
    });
    
    if (!response.ok) {
      throw new Error(`生成种子失败: ${response.status}`);
    }
    
    const result = await response.json();
    const seed = result.data[0];
    log(`生成的随机种子: ${seed}`, 'info');
    return seed;
  } catch (error) {
    log(`生成种子失败: ${error.message}，使用默认值`, 'warning');
    return Math.floor(Math.random() * 100000000);
  }
}
```

### 3. 语音识别

```javascript
async function recognizePromptWav(audioFile, fileSource = 'upload') {
  const apiName = fileSource === 'record' 
    ? '/prompt_wav_recognition_1' 
    : '/prompt_wav_recognition';
  
  const formData = new FormData();
  formData.append('data', JSON.stringify([null]));
  formData.append('files', audioFile);
  
  // 尝试多种API路径
  const possibleUrls = [
    `${API_BASE}${apiName}`,
    `${API_BASE}/api${apiName}`
  ];
  
  for (const url of possibleUrls) {
    try {
      const response = await fetch(url, {
        method: 'POST',
        body: formData
      });
      
      if (response.ok) {
        const result = await response.json();
        return result.data[0];
      }
    } catch (error) {
      continue;
    }
  }
  
  throw new Error('语音识别失败');
}
```

### 4. 生成音频

```javascript
async function generateAudio() {
  // 1. 获取输入参数
  const ttsText = document.getElementById('voice-text').value.trim();
  const mode = document.getElementById('voice-mode').value;
  const promptText = document.getElementById('voice-prompt-text').value.trim();
  const instructText = document.getElementById('voice-instruct-text').value.trim();
  
  // 2. 获取参考音频
  const audioFile = document.getElementById('voice-prompt-upload').files[0] ||
                    document.getElementById('voice-prompt-record').files[0];
  
  if (!audioFile) {
    throw new Error('请上传或录制 Prompt 音频文件');
  }
  
  // 3. 生成随机种子
  const seed = await generateSeed();
  
  // 4. 构建请求
  const formData = new FormData();
  formData.append('data', JSON.stringify([
    ttsText,              // tts_text
    mode,                 // mode_checkbox_group
    promptText || '',     // prompt_text
    null,                 // prompt_wav_upload
    null,                 // prompt_wav_record
    instructText || '',   // instruct_text
    seed,                 // seed
    'false'               // stream
  ]));
  formData.append('files', audioFile);
  formData.append('files', audioFile);
  
  // 5. 发送请求
  const response = await fetch(`${API_BASE}/generate_audio`, {
    method: 'POST',
    body: formData
  });
  
  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`生成音频失败: ${response.status} ${errorText}`);
  }
  
  // 6. 处理响应
  const result = await response.json();
  let audioUrl = null;
  
  if (result.data && result.data[0]) {
    const audioData = result.data[0];
    if (typeof audioData === 'string') {
      audioUrl = audioData;
    } else if (audioData.url) {
      audioUrl = audioData.url;
    } else if (audioData.data) {
      // 处理 base64 数据
      audioUrl = audioData.data;
    }
  }
  
  if (!audioUrl) {
    throw new Error('未获取到音频数据');
  }
  
  // 7. 播放音频
  const audioPlayer = document.getElementById('voice-result-player');
  audioPlayer.src = audioUrl;
  audioPlayer.load();
  audioPlayer.play();
  
  return audioUrl;
}
```

## 推理模式

### 1. 3s极速复刻

- **特点**: 快速克隆声音，适合短文本
- **使用场景**: 需要快速生成语音的场景
- **参数要求**: 
  - 需要参考音频（3秒以上）
  - 可选 Prompt 文本

### 2. 自然语言控制

- **特点**: 通过自然语言指令控制语音风格
- **使用场景**: 需要控制语音情感、语调等
- **参数要求**:
  - 需要参考音频
  - 需要指令文本（instruct_text）

## 完整代码示例

```javascript
// 全局变量
let API_BASE = 'http://127.0.0.1:50000';
const COSYVOICE_CLOUD_API_URL = "https://funaudiollm-fun-cosyvoice3-0-5b.ms.show/";
let isLocalServiceConnected = false;

// 初始化
async function initializeApp() {
  // 更新API地址（会尝试连接本地服务）
  await updateApiBase();
  
  // 测试API连接
  setTimeout(() => testConnection(), 1000);
}

// 生成语音
async function generateAudio() {
  try {
    // 获取输入
    const ttsText = document.getElementById('voice-text').value.trim();
    if (!ttsText) {
      throw new Error('请输入要合成的文本');
    }
    
    const mode = document.getElementById('voice-mode').value;
    const audioFile = getAudioFile();
    
    if (!audioFile) {
      throw new Error('请上传或录制 Prompt 音频文件');
    }
    
    // 生成种子
    const seed = await generateSeed();
    
    // 构建请求
    const formData = new FormData();
    formData.append('data', JSON.stringify([
      ttsText,
      mode,
      document.getElementById('voice-prompt-text').value.trim() || '',
      null,
      null,
      document.getElementById('voice-instruct-text').value.trim() || '',
      seed,
      'false'
    ]));
    formData.append('files', audioFile);
    formData.append('files', audioFile);
    
    // 发送请求
    log('正在生成音频...', 'info');
    const response = await fetch(`${API_BASE}/generate_audio`, {
      method: 'POST',
      body: formData
    });
    
    if (!response.ok) {
      throw new Error(`生成失败: ${response.status}`);
    }
    
    // 处理响应
    const result = await response.json();
    const audioUrl = extractAudioUrl(result);
    
    // 播放音频
    playAudio(audioUrl);
    
    // 保存历史
    saveToHistory({
      text: ttsText,
      mode: mode,
      audioUrl: audioUrl,
      timestamp: new Date().toISOString()
    });
    
    log('音频生成成功', 'success');
    return audioUrl;
    
  } catch (error) {
    log(`生成失败: ${error.message}`, 'error');
    throw error;
  }
}
```

## 参数说明

### 生成音频参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `tts_text` | string | 是 | 要合成的文本内容 |
| `mode_checkbox_group` | string | 是 | 推理模式："3s极速复刻" 或 "自然语言控制" |
| `prompt_text` | string | 否 | Prompt 文本（用于声音克隆） |
| `prompt_wav_upload` | file | 否 | 上传的参考音频文件 |
| `prompt_wav_record` | file | 否 | 录制的参考音频文件 |
| `instruct_text` | string | 否 | 指令文本（用于自然语言控制模式） |
| `seed` | number | 否 | 随机种子（用于控制生成结果） |
| `stream` | string | 否 | 是否流式返回："true" 或 "false" |

### 音频文件要求

- **格式**: 支持常见音频格式（WAV、MP3等）
- **采样率**: 不低于 16kHz
- **时长**: 建议 3 秒以上（3s极速复刻模式）
- **质量**: 清晰、无噪音的音频效果更好

## 使用场景

### 1. 声音克隆
- **步骤**: 
  1. 上传参考音频（3秒以上）
  2. 输入要合成的文本
  3. 选择"3s极速复刻"模式
  4. 点击生成

### 2. 情感语音合成
- **步骤**:
  1. 上传参考音频
  2. 输入要合成的文本
  3. 选择"自然语言控制"模式
  4. 输入指令文本（如："请用自然友好的语气说话"）
  5. 点击生成

### 3. 批量语音生成
- **步骤**:
  1. 准备参考音频
  2. 准备文本列表
  3. 循环调用生成API
  4. 保存生成的音频

## 注意事项

1. **服务连接**:
   - 优先使用本地服务（速度快）
   - 本地服务连接失败时自动切换到创空间服务
   - 确保本地服务正常运行（如果使用本地服务）

2. **音频文件**:
   - 确保音频文件清晰、无噪音
   - 采样率不低于 16kHz
   - 建议使用 WAV 格式

3. **API 调用**:
   - 使用 FormData 传递文件和参数
   - 参考音频文件需要在 `files` 字段中添加两次
   - 注意处理 base64 格式的音频数据

4. **错误处理**:
   - 网络错误：检查服务是否正常运行
   - API 错误：检查参数格式是否正确
   - 音频错误：检查音频文件是否符合要求

5. **性能优化**:
   - 本地服务响应速度更快
   - 可以缓存生成的音频
   - 批量生成时注意控制并发数

## 相关文件

- **主要实现**: `web/voice-clone.html`
- **API调用**: `web/voice-clone.html` (JavaScript部分)
- **参考实现**: `web/voice.html`

