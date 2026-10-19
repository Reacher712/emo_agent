# SadTalker 大模型调用过程与技术使用

## 概述

SadTalker 是一个用于生成数字人说话视频的 AI 模型，在本项目中用于数字人生成功能。本文档详细介绍了 SadTalker API 的调用过程、Gradio API 集成、WebSocket 通信等技术细节。

## 技术架构

### API 端点
- **基础URL**: Stable Diffusion WebUI 的地址（默认 `http://localhost:7860`）
- **接口类型**: Gradio API（基于 HTTP/WebSocket）
- **通信方式**: 
  - HTTP POST（主要方式）
  - WebSocket（备用方式）

### 服务要求

- **Stable Diffusion WebUI**: 需要运行 Stable Diffusion WebUI
- **SadTalker 扩展**: 需要安装 SadTalker 扩展
- **API 模式**: 确保 WebUI 已启用 API 模式

## API 调用流程

### 1. 准备文件

#### 1.1 图片文件处理

```javascript
// 将图片文件转换为 base64
async function fileToBase64(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result);
    reader.onerror = reject;
    reader.readAsDataURL(file);
  });
}

// 处理图片数据
const imageBase64 = await fileToBase64(imageFile);
// 格式: "data:image/png;base64,..."
```

#### 1.2 音频文件处理

```javascript
// 处理音频数据
const audioBase64 = await fileToBase64(audioFile);

// 音频格式：{data: "data:audio/wav;base64,...", name: "audio.wav"}
const audioData = {
  data: audioBase64.startsWith('data:') 
    ? audioBase64 
    : `data:audio/wav;base64,${audioBase64}`,
  name: audioFile.name || 'audio.wav'
};
```

### 2. 生成 Session Hash

```javascript
function generateSessionHash() {
  // 生成一个随机字符串，类似 Gradio 的 session_hash
  return Math.random().toString(36).substring(2, 15) + 
         Math.random().toString(36).substring(2, 15);
}

const sessionHash = generateSessionHash();
```

### 3. 构建请求体

```javascript
// 读取 SadTalker 设置
const poseStyle = parseInt(elements.poseStyle.value) || 0;
const faceResolution = Array.from(elements.faceResolution)
  .find(r => r.checked)?.value || '256';
const preprocess = elements.preprocess.value || 'crop';
const stillMode = elements.stillMode.checked || false;
const batchSize = parseInt(elements.batchSize.value) || 2;
const gfpganEnhancer = elements.gfpganEnhancer.checked || false;

// 构建请求体
const requestBody = {
  data: [
    imageData,                    // 0: 人脸图片（base64 字符串）
    audioData,                    // 1: 驱动音频（对象）
    preprocess,                   // 2: 预处理方式
    stillMode,                    // 3: 是否静态模式
    false,                        // 4: 其他参数
    batchSize,                    // 5: 批量大小
    parseInt(faceResolution),     // 6: 人脸模型分辨率
    poseStyle                     // 7: 姿态风格
  ],
  event_data: null,
  fn_index: fnIndex,              // 函数索引（需要根据实际情况调整）
  session_hash: sessionHash
};
```

### 4. 发送请求（HTTP 方式）

```javascript
async function callSadTalkerAPI(imageFile, audioFile) {
  const base = getApiBaseUrl();
  const sessionHash = generateSessionHash();
  
  // 处理文件
  const imageBase64 = await fileToBase64(imageFile);
  const audioBase64 = await fileToBase64(audioFile);
  
  const imageData = imageBase64;
  const audioData = {
    data: audioBase64.startsWith('data:') 
      ? audioBase64 
      : `data:audio/wav;base64,${audioBase64}`,
    name: audioFile.name || 'audio.wav'
  };
  
  // 构建请求体
  const requestBody = {
    data: [
      imageData,
      audioData,
      'crop',      // preprocess
      false,       // still
      false,       // 其他参数
      2,           // batch_size
      256,         // face_resolution
      0            // pose_style
    ],
    event_data: null,
    fn_index: 73,  // 需要根据实际情况调整
    session_hash: sessionHash
  };
  
  // 发送请求
  const response = await fetch(`${base}/api/predict`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(requestBody)
  });
  
  if (!response.ok) {
    throw new Error(`API请求失败: ${response.status}`);
  }
  
  const result = await response.json();
  
  // 提取视频URL
  if (result.data && result.data[0]) {
    return result.data[0];
  }
  
  throw new Error('未获取到视频数据');
}
```

### 5. WebSocket 方式（备用）

```javascript
async function callSadTalkerAPIWebSocket(imageFile, audioFile) {
  const base = getApiBaseUrl();
  const wsUrl = base.replace(/^http(s?):\/\//, 'ws$1://') + '/queue/join';
  
  return new Promise((resolve, reject) => {
    const ws = new WebSocket(wsUrl);
    let state = 'connecting';
    let resolved = false;
    
    ws.onopen = () => {
      console.log('WebSocket 连接已建立');
      state = 'connected';
      
      // 发送加入队列消息
      ws.send(JSON.stringify({
        fn_index: 73,
        session_hash: generateSessionHash()
      }));
    };
    
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      
      if (data.msg === 'send_data') {
        // 发送数据
        ws.send(JSON.stringify({
          data: [imageData, audioData, ...],
          event_data: null,
          fn_index: 73,
          session_hash: sessionHash
        }));
        state = 'processing';
      } else if (data.msg === 'process_completed') {
        // 处理完成
        const videoUrl = data.output?.data?.[0];
        if (videoUrl && !resolved) {
          resolved = true;
          ws.close();
          resolve(videoUrl);
        }
      } else if (data.msg === 'process_generating') {
        // 生成中
        console.log('生成进度:', data.progress);
      }
    };
    
    ws.onerror = (error) => {
      if (!resolved) {
        resolved = true;
        reject(new Error('WebSocket 连接错误: ' + error.message));
      }
    };
    
    ws.onclose = (event) => {
      if (!resolved && state !== 'processing' && state !== 'completed') {
        reject(new Error(`WebSocket 连接已关闭 (代码: ${event.code})`));
      }
    };
  });
}
```

## 完整代码示例

```javascript
// 生成数字人
async function generateDigitalHuman(config) {
  try {
    elements.generateHumanBtn.disabled = true;
    elements.humanLoading.classList.remove('hidden');
    
    // 调用真实的 SadTalker API
    const videoUrl = await callSadTalkerAPI(config.imageFile, config.audioFile);
    
    if (!videoUrl) {
      throw new Error('视频生成成功，但未返回视频 URL');
    }
    
    // 显示结果
    displayHumanResult({ videoUrl, config });
    
    // 保存到图库
    saveToGallery({ videoUrl, config });
    
  } catch (error) {
    console.error('生成数字人失败:', error);
    
    let errorMessage = '生成数字人失败';
    if (error.message.includes('fetch')) {
      errorMessage = '无法连接到 SadTalker API\n\n请检查：\n1. WebUI 是否已启动并启用了 API 模式\n2. API 地址是否正确（在设置中配置）\n3. 是否已安装 SadTalker 扩展';
    } else {
      errorMessage = '生成失败：' + error.message;
    }
    
    alert(errorMessage);
  } finally {
    elements.generateHumanBtn.disabled = false;
    elements.humanLoading.classList.add('hidden');
  }
}

// 调用 SadTalker API
async function callSadTalkerAPI(imageFile, audioFile) {
  const base = getApiBaseUrl();
  const sessionHash = generateSessionHash();
  
  // 验证文件类型
  if (!imageFile.type.startsWith('image/')) {
    throw new Error('图片文件格式不支持，请使用 JPG、PNG 等图片格式');
  }
  
  if (!audioFile.type.startsWith('audio/')) {
    throw new Error('音频文件格式不支持，请使用 WAV、MP3 等音频格式');
  }
  
  // 处理文件
  const imageBase64 = await fileToBase64(imageFile);
  const audioBase64 = await fileToBase64(audioFile);
  
  const imageData = imageBase64;
  const audioData = {
    data: audioBase64.startsWith('data:') 
      ? audioBase64 
      : `data:audio/wav;base64,${audioBase64}`,
    name: audioFile.name || 'audio.wav'
  };
  
  // 读取设置
  const poseStyle = elements.poseStyle ? parseInt(elements.poseStyle.value) || 0 : 0;
  const faceResolution = elements.faceResolution ? 
    Array.from(elements.faceResolution).find(r => r.checked)?.value || '256' : '256';
  const preprocess = elements.preprocess ? elements.preprocess.value || 'crop' : 'crop';
  const stillMode = elements.stillMode ? elements.stillMode.checked : false;
  const batchSize = elements.batchSize ? parseInt(elements.batchSize.value) || 2 : 2;
  
  // 构建请求体
  const requestBody = {
    data: [
      imageData,                    // 0: 人脸图片
      audioData,                    // 1: 驱动音频
      preprocess,                   // 2: 预处理方式
      stillMode,                    // 3: 是否静态模式
      false,                        // 4: 其他参数
      batchSize,                    // 5: 批量大小
      parseInt(faceResolution),     // 6: 人脸模型分辨率
      poseStyle                     // 7: 姿态风格
    ],
    event_data: null,
    fn_index: 73,                   // 需要根据实际情况调整
    session_hash: sessionHash
  };
  
  // 方法1：使用 HTTP POST
  try {
    const response = await fetch(`${base}/api/predict`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(requestBody)
    });
    
    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`API请求失败: ${response.status} ${errorText}`);
    }
    
    const result = await response.json();
    
    // 提取视频URL
    if (result.data && result.data[0]) {
      const videoUrl = result.data[0];
      if (typeof videoUrl === 'string' && videoUrl.startsWith('http')) {
        return videoUrl;
      } else if (typeof videoUrl === 'object' && videoUrl.url) {
        return videoUrl.url;
      }
    }
    
    throw new Error('未获取到有效的视频数据');
    
  } catch (httpError) {
    console.warn('HTTP 方式失败，尝试 WebSocket 方式:', httpError);
    
    // 方法2：使用 WebSocket（备用）
    return await callSadTalkerAPIWebSocket(imageFile, audioFile);
  }
}
```

## 参数说明

### 请求参数

| 索引 | 参数 | 类型 | 说明 | 可选值 |
|------|------|------|------|--------|
| 0 | `image` | string | 人脸图片（base64） | - |
| 1 | `audio` | object | 驱动音频 | `{data: "...", name: "..."}` |
| 2 | `preprocess` | string | 预处理方式 | `crop`, `resize`, `full`, `extcrop`, `extfull` |
| 3 | `still` | boolean | 是否静态模式 | `true`, `false` |
| 4 | - | boolean | 其他参数 | `false` |
| 5 | `batch_size` | number | 批量大小 | `1`, `2`, `4` |
| 6 | `face_resolution` | number | 人脸模型分辨率 | `256`, `512` |
| 7 | `pose_style` | number | 姿态风格 | `0-45` |

### 预处理方式说明

| 方式 | 说明 |
|------|------|
| `crop` | 裁剪（推荐） |
| `resize` | 调整大小 |
| `full` | 完整 |
| `extcrop` | 扩展裁剪 |
| `extfull` | 扩展完整 |

### 姿态风格说明

- **范围**: 0-45
- **说明**: 控制数字人的头部姿态和表情
- **推荐值**: 0（默认）、10、20、30

## 使用场景

### 1. 基础数字人生成
- 上传人脸图片
- 上传驱动音频
- 使用默认设置
- 点击生成

### 2. 高质量生成
- 选择高分辨率（512）
- 启用 GFPGAN 增强
- 调整姿态风格
- 生成高质量视频

### 3. 批量生成
- 设置批量大小（2-4）
- 上传多组图片和音频
- 批量生成视频

## 注意事项

1. **fn_index 参数**:
   - 这个参数需要根据实际的 Gradio 应用调整
   - 可以通过查看 WebUI 的网络请求获取
   - 不同版本的 SadTalker 可能不同

2. **文件格式**:
   - 图片：支持 JPG、PNG 等常见格式
   - 音频：支持 WAV、MP3 等常见格式
   - 建议使用清晰的图片和音频

3. **性能优化**:
   - 高分辨率会增加生成时间
   - 批量生成会增加生成时间
   - 建议使用合适的批量大小

4. **错误处理**:
   - HTTP 方式失败时自动切换到 WebSocket
   - 检查 WebUI 是否运行
   - 检查 SadTalker 扩展是否安装

5. **Session Hash**:
   - 每次请求需要生成新的 session_hash
   - 用于标识不同的会话

## 相关文件

- **主要实现**: `web/script.js` (第 2199-2898 行)
- **API调用**: `web/script.js` (第 2276-2898 行)
- **前端界面**: `web/digital-human.html`

