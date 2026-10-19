# 可灵 (Kling) API 调用过程

## 概述

可灵 (Kling) 是快手推出的 AI 视频生成模型，在本项目中用于图生视频功能。本文档详细介绍了可灵 API 的调用过程、JWT Token 生成、任务轮询等完整流程。

## 技术架构

### API 端点
- **基础URL**: `https://api-beijing.klingai.com`
- **接口路径**: `/v1/videos/image2video`
- **请求方法**: `POST` (创建任务) / `GET` (查询任务)
- **认证方式**: JWT Token (Bearer Token)

### 认证机制

可灵 API 使用 JWT (JSON Web Token) 进行认证，使用 HS256 算法。

#### JWT Token 生成

**前端实现** (`web/script.js`):
```javascript
async function generateKlingJWTToken(accessKey, secretKey) {
  // 使用 crypto-js 库生成 JWT Token
  const header = {
    alg: 'HS256',
    typ: 'JWT'
  };
  
  const payload = {
    iss: accessKey,           // 发行者（Access Key）
    nbf: Math.floor(Date.now() / 1000),  // 生效时间
    iat: Math.floor(Date.now() / 1000),   // 签发时间
    exp: Math.floor(Date.now() / 1000) + 3600,  // 过期时间（1小时后）
    aud: 'kling-api'          // 受众
  };
  
  // 使用 HS256 算法签名
  const token = KJUR.jws.JWS.sign('HS256', header, payload, secretKey);
  return token;
}
```

**后端实现** (`web/kling_backend.py`):
```python
import jwt
import time

def generate_kling_token():
    """生成可灵API的JWT Token"""
    payload = {
        "iss": ACCESS_KEY,
        "nbf": int(time.time()),
        "iat": int(time.time()),
        "exp": int(time.time()) + 3600,
        "aud": "kling-api"
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
    return token
```

## 调用流程

### 1. 配置准备

#### 1.1 API Key 配置

```javascript
// 从 localStorage 或默认配置中获取
const state = {
  klingAccessKey: localStorage.getItem('klingAccessKey') || KLING_ACCESS_KEY,
  klingSecretKey: localStorage.getItem('klingSecretKey') || KLING_SECRET_KEY
};
```

#### 1.2 图片处理

```javascript
// 将图片文件转换为 base64
const imageBase64 = await new Promise((resolve, reject) => {
  const reader = new FileReader();
  reader.onload = () => {
    resolve(reader.result); // 包含 data:image/...;base64, 前缀
  };
  reader.onerror = reject;
  reader.readAsDataURL(config.imageFile);
});

// 去掉 data:image/...;base64, 前缀，只保留纯 base64 字符串
let imageData = imageBase64;
if (imageBase64.startsWith('data:')) {
  imageData = imageBase64.split(',')[1];
}
```

### 2. 构建提示词

根据动画类型自动添加动画提示词：

```javascript
let animationPrompt = '';
switch (config.animationType) {
  case 'zoom-in':
    animationPrompt = 'zoom in, smooth camera movement, cinematic';
    break;
  case 'zoom-out':
    animationPrompt = 'zoom out, smooth camera movement, cinematic';
    break;
  case 'pan-left':
    animationPrompt = 'pan left, smooth camera movement, cinematic';
    break;
  case 'pan-right':
    animationPrompt = 'pan right, smooth camera movement, cinematic';
    break;
  // ... 其他动画类型
  default:
    animationPrompt = 'smooth camera movement, cinematic';
}

const fullPrompt = config.prompt 
  ? `${config.prompt}, ${animationPrompt}`
  : animationPrompt;
```

### 3. 构建请求体

```javascript
const requestBody = {
  model_name: 'kling-v1-6',        // 模型名称
  image: imageData,                 // 参考图像（base64，无前缀）
  prompt: finalPrompt,              // 正向提示词（可选，不超过2500字符）
  negative_prompt: finalNegativePrompt, // 负向提示词（可选）
  mode: 'std' | 'pro',              // 模式：std（标准）或 pro（专家）
  duration: '5' | '10',             // 视频时长（秒）
  cfg_scale: 0.5                    // 自由度（0-1，仅 kling-v1.x 支持）
};
```

### 4. 发送创建任务请求

```javascript
// 生成 JWT Token
const jwtToken = await generateKlingJWTToken(cleanAccessKey, cleanSecretKey);

// 构建请求头
const headers = {
  'Authorization': `Bearer ${jwtToken}`,
  'Content-Type': 'application/json'
};

// 发送请求
const response = await fetch(apiUrl, {
  method: 'POST',
  headers: headers,
  body: JSON.stringify(requestBody)
});
```

### 5. 处理响应

#### 5.1 成功响应

```javascript
const data = await response.json();

// 响应格式：
// {
//   "code": 0,
//   "message": "string",
//   "request_id": "string",
//   "data": {
//     "task_id": "string",
//     "task_status": "submitted" | "processing" | "succeed" | "failed",
//     "created_at": 1722769557708,
//     "updated_at": 1722769557708
//   }
// }

if (data.code !== 0) {
  throw new Error(`可灵API返回错误 (code: ${data.code}): ${data.message}`);
}

const taskId = data.data.task_id;
```

#### 5.2 错误处理

```javascript
if (!response.ok) {
  const errorText = await response.text();
  throw new Error(`可灵API调用失败: ${response.status} - ${errorText}`);
}
```

### 6. 轮询任务状态

```javascript
async function pollKlingTask(taskId, maxAttempts = 60) {
  const apiUrl = `${apiBaseUrl}/v1/videos/image2video/${taskId}`;
  
  // 生成新的 JWT Token（每次查询都需要）
  const jwtToken = await generateKlingJWTToken(cleanAccessKey, cleanSecretKey);
  
  const headers = {
    'Authorization': `Bearer ${jwtToken}`,
    'Content-Type': 'application/json'
  };
  
  for (let i = 0; i < maxAttempts; i++) {
    // 第一次查询前等待2秒，后续每次等待3秒
    if (i > 0) {
      await new Promise(resolve => setTimeout(resolve, 3000));
    } else {
      await new Promise(resolve => setTimeout(resolve, 2000));
    }
    
    const response = await fetch(apiUrl, { headers });
    const data = await response.json();
    
    const taskStatus = data.data?.task_status;
    
    if (taskStatus === 'succeed') {
      // 任务成功，返回视频URL
      const videoUrl = data.data?.video_url;
      if (videoUrl) {
        return videoUrl;
      }
    } else if (taskStatus === 'failed') {
      throw new Error(`任务失败: ${data.data?.error_message || '未知错误'}`);
    }
    // 继续轮询...
  }
  
  throw new Error('任务超时，请稍后查询');
}
```

## 完整代码示例

### 前端实现

```javascript
async function callKlingAPI(config) {
  // 1. 检查配置
  if (!state.klingAccessKey || !state.klingSecretKey) {
    throw new Error('请先在设置中配置可灵API密钥');
  }
  
  // 2. 处理图片
  const imageBase64 = await new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result);
    reader.onerror = reject;
    reader.readAsDataURL(config.imageFile);
  });
  
  let imageData = imageBase64.split(',')[1]; // 去掉前缀
  
  // 3. 构建提示词
  const fullPrompt = buildPrompt(config);
  
  // 4. 生成 JWT Token
  const jwtToken = await generateKlingJWTToken(
    state.klingAccessKey,
    state.klingSecretKey
  );
  
  // 5. 构建请求体
  const requestBody = {
    model_name: 'kling-v1-6',
    image: imageData,
    prompt: fullPrompt,
    mode: config.quality === 'ultra' ? 'pro' : 'std',
    duration: config.duration <= 5 ? '5' : '10',
    cfg_scale: 0.5
  };
  
  // 6. 发送请求
  const response = await fetch(apiUrl, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${jwtToken}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(requestBody)
  });
  
  // 7. 处理响应
  const data = await response.json();
  if (data.code !== 0) {
    throw new Error(`API错误: ${data.message}`);
  }
  
  // 8. 轮询任务状态
  const taskId = data.data.task_id;
  return await pollKlingTask(taskId);
}
```

### 后端实现

```python
from flask import Flask, request, jsonify
from flask_cors import CORS
import jwt
import time
import requests

app = Flask(__name__)
CORS(app)

ACCESS_KEY = os.getenv('KLING_ACCESS_KEY')
SECRET_KEY = os.getenv('KLING_SECRET_KEY')

def generate_kling_token():
    payload = {
        "iss": ACCESS_KEY,
        "nbf": int(time.time()),
        "iat": int(time.time()),
        "exp": int(time.time()) + 3600,
        "aud": "kling-api"
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")

@app.route('/api/generate-video', methods=['POST'])
def generate_video():
    data = request.get_json()
    
    # 生成 Token
    token = generate_kling_token()
    
    # 调用可灵API
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    request_body = {
        'model_name': 'kling-v1-6',
        'image': data['image'],
        'prompt': data['prompt'],
        'mode': data.get('mode', 'std'),
        'duration': data.get('duration', '5')
    }
    
    response = requests.post(
        'https://api-beijing.klingai.com/v1/videos/image2video',
        headers=headers,
        json=request_body,
        timeout=60
    )
    
    if response.status_code == 200:
        result = response.json()
        return jsonify({
            'success': True,
            'task_id': result.get('data', {}).get('task_id')
        })
    else:
        return jsonify({
            'success': False,
            'error': f'API调用失败: {response.status_code}'
        }), 500
```

## 模型版本

可灵 API 支持以下模型版本：

| 模型名称 | 说明 |
|---------|------|
| `kling-v1` | 基础版本 |
| `kling-v1-5` | 1.5版本 |
| `kling-v1-6` | 1.6版本（推荐） |
| `kling-v2-master` | V2主版本 |
| `kling-v2-1` | V2.1版本 |
| `kling-v2-1-master` | V2.1主版本 |
| `kling-v2-5-turbo` | V2.5加速版 |
| `kling-v2-6` | V2.6版本 |

## 参数说明

### 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `model_name` | string | 否 | 模型名称，默认 `kling-v1` |
| `image` | string | 是 | 参考图像（base64或URL） |
| `prompt` | string | 否 | 正向提示词（不超过2500字符） |
| `negative_prompt` | string | 否 | 负向提示词（不超过2500字符） |
| `mode` | string | 否 | 模式：`std`（标准）或 `pro`（专家） |
| `duration` | string | 否 | 视频时长：`"5"` 或 `"10"` |
| `cfg_scale` | float | 否 | 自由度（0-1，仅v1.x支持） |

### 响应参数

| 参数 | 类型 | 说明 |
|------|------|------|
| `code` | number | 错误码，0表示成功 |
| `message` | string | 错误信息 |
| `request_id` | string | 请求ID |
| `data.task_id` | string | 任务ID |
| `data.task_status` | string | 任务状态 |
| `data.video_url` | string | 视频URL（任务成功时） |

## 注意事项

1. **JWT Token 有效期**: Token 有效期为1小时，需要定期刷新
2. **图片格式要求**: 
   - 支持 `.jpg`、`.jpeg`、`.png`
   - 大小不超过 10MB
   - 宽高不小于 300px
   - 宽高比介于 1:2.5 ~ 2.5:1 之间
3. **提示词长度**: 正向和负向提示词都不能超过 2500 字符
4. **任务轮询**: 
   - 建议轮询间隔 3 秒
   - 最大轮询次数 60 次（约3分钟）
5. **CORS 问题**: 
   - 如果遇到 CORS 错误，可以使用本地代理服务器
   - 代理服务器地址：`http://localhost:8888/proxy/kling`

## 相关文件

- **前端实现**: `web/script.js` (第 3934-4517 行)
- **后端实现**: `web/kling_backend.py`
- **JWT生成**: `web/script.js` (第 3866-3931 行)
- **任务轮询**: `web/script.js` (第 4341-4517 行)

