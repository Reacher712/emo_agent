# DeepSeek API 调用过程

## 概述

DeepSeek 是一个强大的 AI 对话模型，在本项目中用于 AI 助手功能，包括剧本生成和提示词生成。本文档详细介绍了 DeepSeek API 的调用过程和技术实现。

## 技术架构

### API 端点
- **基础URL**: `https://api.deepseek.com`
- **接口路径**: `/chat/completions`
- **请求方法**: `POST`
- **认证方式**: Bearer Token (API Key)

### 认证配置

API Key 的配置方式有两种：

1. **代码中配置**（默认值）:
```javascript
const DEEPSEEK_API_KEY = 'YOUR_DEEPSEEK_API_KEY';
```

2. **设置界面配置**（优先级更高）:
- 用户可以在设置界面中配置自己的 API Key
- 配置会保存到 `localStorage` 中
- 代码会优先使用 `localStorage` 中的值

## 调用流程

### 1. 初始化配置

```javascript
// 从 localStorage 或默认配置中获取 API Key
const state = {
  deepseekApiKey: localStorage.getItem('deepseekApiKey') || DEEPSEEK_API_KEY
};
```

### 2. 构建请求

#### 2.1 系统提示词构建

根据不同的功能类型，构建不同的系统提示词：

**剧本生成模式** (`script`):
```javascript
systemPrompt = `你是一个专业的剧本创作助手。你的任务是**只生成剧本内容**，不要添加任何解释、说明或其他文字。

要求：
1. 直接输出剧本内容，包括场景描述、人物对话、动作提示等
2. 使用标准的剧本格式（场景标题、人物名称、对话内容等）
3. 不要添加"以下是剧本"、"剧本如下"等前缀
4. 不要添加任何解释性文字、说明或建议
5. 只输出纯粹的剧本内容`;
```

**提示词生成模式** (`prompt`):
```javascript
systemPrompt = `你是一个专业的AI提示词生成助手。你的任务是**只生成Stable Diffusion提示词**，不要添加任何解释、说明或其他文字。

要求：
1. 直接输出英文提示词（prompt），使用逗号分隔关键词
2. 可以包含负面提示词（negative prompt），用"Negative:"标记
3. 不要添加"以下是提示词"、"提示词如下"等前缀
4. 不要添加任何解释性文字、说明或建议
5. 只输出纯粹的提示词内容`;
```

#### 2.2 请求体构建

```javascript
const requestBody = {
  model: 'deepseek-chat',           // 模型名称
  messages: [
    { role: 'system', content: systemPrompt },  // 系统提示词
    { role: 'user', content: userPrompt }     // 用户输入
  ],
  stream: false,                     // 是否流式返回
  temperature: 0.7,                  // 温度参数（控制随机性）
  max_tokens: 2000                   // 最大生成token数
};
```

### 3. 发送请求

```javascript
const response = await fetch('https://api.deepseek.com/chat/completions', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${state.deepseekApiKey}`
  },
  body: JSON.stringify(requestBody)
});
```

### 4. 处理响应

#### 4.1 成功响应

```javascript
if (response.ok) {
  const data = await response.json();
  
  // 提取回复内容
  if (data.choices && data.choices.length > 0 && data.choices[0].message) {
    return data.choices[0].message.content;
  } else {
    throw new Error('API 返回格式不正确');
  }
}
```

#### 4.2 错误处理

```javascript
if (!response.ok) {
  const errorData = await response.json().catch(() => ({ error: { message: '未知错误' } }));
  throw new Error(errorData.error?.message || `API 请求失败: ${response.status}`);
}
```

### 5. 错误处理策略

```javascript
catch (error) {
  console.error('DeepSeek API 调用失败:', error);
  
  if (error.message.includes('API Key')) {
    throw new Error('DeepSeek API Key 无效，请检查设置中的配置');
  } else if (error.message.includes('网络') || error.message.includes('fetch')) {
    throw new Error('无法连接到 DeepSeek API，请检查网络连接');
  } else {
    throw error;
  }
}
```

## 完整代码示例

```javascript
async function callAIChatAPI(message, tabType) {
  // 检查是否配置了 DeepSeek API Key
  if (!state.deepseekApiKey || state.deepseekApiKey.trim() === '') {
    throw new Error('请先在设置中配置 DeepSeek API Key');
  }
  
  // 根据标签类型构建不同的提示词
  let systemPrompt = '';
  let userPrompt = message;
  
  if (tabType === 'script') {
    // 剧本生成系统提示词
    systemPrompt = `你是一个专业的剧本创作助手...`;
  } else if (tabType === 'prompt') {
    // 提示词生成系统提示词
    systemPrompt = `你是一个专业的AI提示词生成助手...`;
  }
  
  try {
    // 调用 DeepSeek API
    const response = await fetch('https://api.deepseek.com/chat/completions', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${state.deepseekApiKey}`
      },
      body: JSON.stringify({
        model: 'deepseek-chat',
        messages: [
          { role: 'system', content: systemPrompt },
          { role: 'user', content: userPrompt }
        ],
        stream: false,
        temperature: 0.7,
        max_tokens: 2000
      })
    });
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ error: { message: '未知错误' } }));
      throw new Error(errorData.error?.message || `API 请求失败: ${response.status}`);
    }
    
    const data = await response.json();
    
    // 提取回复内容
    if (data.choices && data.choices.length > 0 && data.choices[0].message) {
      return data.choices[0].message.content;
    } else {
      throw new Error('API 返回格式不正确');
    }
    
  } catch (error) {
    console.error('DeepSeek API 调用失败:', error);
    if (error.message.includes('API Key')) {
      throw new Error('DeepSeek API Key 无效，请检查设置中的配置');
    } else if (error.message.includes('网络') || error.message.includes('fetch')) {
      throw new Error('无法连接到 DeepSeek API，请检查网络连接');
    } else {
      throw error;
    }
  }
}
```

## 使用场景

### 1. 剧本生成
- **触发方式**: 用户在 AI 助手中选择"剧本"标签页
- **输入**: 用户输入的剧本需求描述
- **输出**: 标准格式的剧本内容

### 2. 提示词生成
- **触发方式**: 用户在 AI 助手中选择"提示词"标签页
- **输入**: 用户想要生成的图片描述
- **输出**: Stable Diffusion 格式的提示词（英文，逗号分隔）

## 参数说明

| 参数 | 类型 | 说明 | 默认值 |
|------|------|------|--------|
| `model` | string | 模型名称 | `deepseek-chat` |
| `messages` | array | 对话消息数组 | 必填 |
| `stream` | boolean | 是否流式返回 | `false` |
| `temperature` | number | 温度参数（0-2） | `0.7` |
| `max_tokens` | number | 最大生成token数 | `2000` |

## 注意事项

1. **API Key 安全**: 
   - 不要在代码中硬编码 API Key（生产环境）
   - 建议使用环境变量或配置文件
   - 前端代码中的 API Key 可以被用户查看，仅用于开发测试

2. **网络请求**:
   - 需要确保网络可以访问 `api.deepseek.com`
   - 如果遇到 CORS 错误，可能需要使用代理服务器

3. **错误处理**:
   - 始终检查 API Key 是否配置
   - 处理网络错误和 API 错误
   - 提供友好的错误提示给用户

4. **响应格式**:
   - API 返回的格式为 OpenAI 兼容格式
   - 需要从 `data.choices[0].message.content` 中提取内容

## 相关文件

- **主要实现**: `web/script.js` (第 3398-3491 行)
- **配置位置**: `web/script.js` (第 319 行)
- **状态管理**: `web/script.js` (第 330 行)

