# Stable Diffusion 大模型调用过程与技术使用

## 概述

Stable Diffusion 是一个强大的文本到图像生成模型，在本项目中用于图片生成功能。本文档详细介绍了 Stable Diffusion WebUI API 的调用过程、参数配置、LoRA 模型使用等技术细节。

## 技术架构

### API 端点
- **基础URL**: `http://localhost:7860` (默认) 或用户配置的地址
- **接口路径**: `/sdapi/v1/txt2img` (文生图) / `/sdapi/v1/img2img` (图生图)
- **请求方法**: `POST`
- **数据格式**: JSON

### 服务要求

- **Stable Diffusion WebUI**: 需要运行 Stable Diffusion WebUI 服务
- **API 模式**: 确保 WebUI 已启用 API 模式（默认启用）
- **网络访问**: 确保前端可以访问 WebUI 的 API 地址

## API 调用流程

### 1. 配置 API 地址

```javascript
// 从 localStorage 或默认配置中获取
const state = {
  apiUrl: localStorage.getItem('apiUrl') || 'http://localhost:7860'
};

// 获取 API 基础 URL
function getApiBaseUrl() {
  return state.apiUrl;
}
```

### 2. 构建请求参数

#### 2.1 基础参数

```javascript
const requestBody = {
  prompt: prompt,                    // 正向提示词
  negative_prompt: negativePrompt,   // 负向提示词
  steps: 20,                         // 采样步数（1-150）
  cfg_scale: 7,                      // 引导强度（1-30）
  width: 1024,                       // 图片宽度
  height: 1024,                      // 图片高度
  sampler_index: 'DPM++ 2M Karras',  // 采样器
  batch_size: 1,                     // 批量大小（1-4）
  n_iter: 1                          // 迭代次数
};
```

#### 2.2 LoRA 模型处理

```javascript
// 加载 LoRA 列表
async function loadLoras() {
  const baseUrl = getApiBaseUrl();
  const possibleLoraUrls = [
    `${baseUrl}/sdapi/v1/extra-networks/lora`,
    `${baseUrl}/sdapi/v1/loras`,
    `${baseUrl}/sdapi/v1/extra-networks`
  ];
  
  for (const url of possibleLoraUrls) {
    try {
      const res = await fetch(url, {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' }
      });
      
      if (res.ok) {
        const data = await res.json();
        const loraData = Array.isArray(data) ? data : 
                        (data.loras || data.networks?.filter(n => n.type === 'lora') || []);
        
        // 填充下拉框
        elements.loraSelect.innerHTML = '<option value="">不使用 LoRA</option>';
        loraData.forEach((lora) => {
          const opt = document.createElement('option');
          opt.value = lora.name;
          opt.textContent = lora.alias || lora.name;
          elements.loraSelect.appendChild(opt);
        });
        
        return;
      }
    } catch (error) {
      continue;
    }
  }
  
  throw new Error('无法连接到 Stable Diffusion WebUI 或获取 LoRA 列表');
}

// 应用 LoRA 到提示词
let finalPrompt = prompt;
if (elements.loraSelect && elements.loraSelect.value) {
  const loraName = elements.loraSelect.value;
  let weight = parseFloat(elements.loraWeight?.value || 0.8);
  
  // 限制权重范围
  if (isNaN(weight) || weight < 0) weight = 0.8;
  if (weight > 2) weight = 2;
  
  // 清理 LoRA 名称（移除文件扩展名和特殊字符）
  const cleanLoraName = loraName
    .replace(/\.(safetensors|ckpt|pt)$/i, '')
    .replace(/[^a-zA-Z0-9_-]/g, '');
  
  // 添加到提示词
  finalPrompt = `<lora:${cleanLoraName}:${weight}> ` + finalPrompt;
  console.log(`✅ LoRA 应用: <lora:${cleanLoraName}:${weight}>`);
}
```

#### 2.3 风格提示词处理

```javascript
let stylePrompt = '';
switch (style) {
  case 'anime':
    stylePrompt = ', anime style, 2d, highly detailed';
    break;
  case 'oil-painting':
    stylePrompt = ', oil painting, textured, artstation';
    break;
  case 'watercolor':
    stylePrompt = ', watercolor, soft, light colors';
    break;
  case 'sketch':
    stylePrompt = ', pencil sketch, lineart';
    break;
  case 'cyberpunk':
    stylePrompt = ', cyberpunk, neon lights, futuristic';
    break;
  case 'fantasy':
    stylePrompt = ', fantasy, epic, highly detailed';
    break;
  default:
    stylePrompt = '';
}

const finalPrompt = (prompt || '') + stylePrompt;
```

### 3. 发送请求

```javascript
async function callTxt2Img(prompt, style, width, height, batchSize, steps = 20) {
  const base = getApiBaseUrl();
  const url = `${base}/sdapi/v1/txt2img`;
  
  // 构建请求体
  const body = {
    prompt: finalPrompt,
    negative_prompt: negativePrompt || 'lowres, bad anatomy, bad hands, text, error, missing fingers, extra digit, fewer digits, cropped, worst quality, low quality, normal quality, jpeg artifacts, signature, watermark, username, blurry',
    steps: Math.max(1, Math.min(150, steps || 20)),
    cfg_scale: 7,
    width: parseInt(width),
    height: parseInt(height),
    sampler_index: 'DPM++ 2M Karras',
    batch_size: batchSize,
    n_iter: 1
  };
  
  // 发送请求
  const res = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(body)
  });
  
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`请求失败: ${res.status} ${text}`);
  }
  
  const data = await res.json();
  return data.images || [];
}
```

### 4. 处理响应

```javascript
async function mockImageGeneration(config) {
  // ... 构建请求参数 ...
  
  try {
    const response = await fetch(`${state.apiUrl}/sdapi/v1/txt2img`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(requestBody)
    });
    
    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`API请求失败: ${response.status} ${response.statusText}\n${errorText}`);
    }
    
    const data = await response.json();
    
    // 将 base64 图片数据转换为 data URL
    const images = data.images.map(base64Image => {
      return `data:image/png;base64,${base64Image}`;
    });
    
    return images;
    
  } catch (error) {
    console.error('API调用错误:', error);
    throw error;
  }
}
```

## 完整代码示例

```javascript
// 初始化图片生成
function initImageGeneration() {
  const generateBtn = elements.imageGenerateBtn;
  if (!generateBtn) return;
  
  generateBtn.addEventListener('click', async () => {
    const prompt = elements.imagePrompt?.value.trim() || '';
    if (!prompt) {
      alert('请输入图片描述');
      return;
    }
    
    // 构建配置
    const config = {
      prompt,
      negativePrompt: elements.imageNegativePrompt?.value.trim() || '',
      style: elements.imageStyle.value,
      size: elements.imageSize.value,
      count: parseInt(elements.imageCount.value) || 1,
      steps: parseInt(elements.imageSteps?.value) || 20
    };
    
    // 显示加载状态
    generateBtn.disabled = true;
    generateBtn.innerHTML = '<span class="btn-icon">⏳</span> <span>生成中...</span>';
    
    try {
      // 生成图片
      const images = await generateImage(config);
      
      // 显示结果
      displayImages(images);
      
      // 保存历史
      saveImageHistory(prompt, config);
      
    } catch (error) {
      console.error('生成失败:', error);
      alert('生成失败：' + error.message);
    } finally {
      generateBtn.disabled = false;
      generateBtn.innerHTML = '<span class="btn-icon">🎨</span> <span>生成图片</span>';
    }
  });
  
  // 加载 LoRA 列表
  loadLoras().catch(err => {
    console.warn('LoRA 加载失败:', err);
  });
}

// 生成图片
async function generateImage(config) {
  const [width, height] = config.size.split('x');
  
  // 构建提示词（包含 LoRA）
  let prompt = config.prompt;
  if (elements.loraSelect && elements.loraSelect.value) {
    const loraName = elements.loraSelect.value;
    const weight = parseFloat(elements.loraWeight?.value || 0.8);
    const cleanLoraName = loraName
      .replace(/\.(safetensors|ckpt|pt)$/i, '')
      .replace(/[^a-zA-Z0-9_-]/g, '');
    prompt = `<lora:${cleanLoraName}:${weight}> ` + prompt;
  }
  
  // 构建请求体
  const requestBody = {
    prompt: prompt,
    negative_prompt: config.negativePrompt || 'lowres, bad anatomy, bad hands, text, error, missing fingers, extra digit, fewer digits, cropped, worst quality, low quality, normal quality, jpeg artifacts, signature, watermark, username, blurry',
    steps: Math.max(1, Math.min(150, config.steps || 20)),
    cfg_scale: 7,
    width: parseInt(width),
    height: parseInt(height),
    sampler_index: 'DPM++ 2M Karras',
    batch_size: Math.min(config.count, 4),
    n_iter: 1
  };
  
  // 发送请求
  const response = await fetch(`${state.apiUrl}/sdapi/v1/txt2img`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(requestBody)
  });
  
  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`API请求失败: ${response.status} ${response.statusText}\n${errorText}`);
  }
  
  const data = await response.json();
  
  // 转换图片格式
  return data.images.map(base64Image => {
    return `data:image/png;base64,${base64Image}`;
  });
}
```

## 参数说明

### 请求参数

| 参数 | 类型 | 必填 | 说明 | 默认值 |
|------|------|------|------|--------|
| `prompt` | string | 是 | 正向提示词 | - |
| `negative_prompt` | string | 否 | 负向提示词 | - |
| `steps` | number | 否 | 采样步数（1-150） | 20 |
| `cfg_scale` | number | 否 | 引导强度（1-30） | 7 |
| `width` | number | 否 | 图片宽度 | 1024 |
| `height` | number | 否 | 图片高度 | 1024 |
| `sampler_index` | string | 否 | 采样器名称 | 'DPM++ 2M Karras' |
| `batch_size` | number | 否 | 批量大小（1-4） | 1 |
| `n_iter` | number | 否 | 迭代次数 | 1 |

### 响应参数

| 参数 | 类型 | 说明 |
|------|------|------|
| `images` | array | base64 编码的图片数组 |
| `parameters` | object | 生成参数 |
| `info` | string | 生成信息（JSON字符串） |

## LoRA 模型使用

### 1. LoRA 格式

在提示词中使用 LoRA 的格式：

```
<lora:模型名称:权重>
```

例如：
```
<lora:anime_v1:0.8> a beautiful anime girl
```

### 2. 权重范围

- **推荐范围**: 0.5 - 1.5
- **最小值**: 0（不使用）
- **最大值**: 2（强烈效果）

### 3. 名称清理

LoRA 名称需要清理：
- 移除文件扩展名（`.safetensors`、`.ckpt`、`.pt`）
- 移除特殊字符（只保留字母、数字、下划线、连字符）

## 采样器说明

常用的采样器：

| 采样器 | 特点 | 适用场景 |
|--------|------|----------|
| `DPM++ 2M Karras` | 快速、质量好 | 通用推荐 |
| `Euler a` | 快速、创意性强 | 快速生成 |
| `DDIM` | 稳定、可复现 | 需要固定种子 |
| `DPM++ SDE Karras` | 高质量 | 追求质量 |

## 使用场景

### 1. 基础图片生成
- 输入文本描述
- 选择图片尺寸
- 设置采样步数
- 点击生成

### 2. 风格化生成
- 选择风格（动漫、油画等）
- 系统自动添加风格提示词
- 生成对应风格的图片

### 3. LoRA 风格应用
- 选择 LoRA 模型
- 设置权重（0.5-1.5）
- 生成具有特定风格的图片

### 4. 批量生成
- 设置生成数量（1-4）
- 系统自动批量生成
- 返回多张图片

## 注意事项

1. **API 地址配置**:
   - 确保 WebUI 正在运行
   - 检查 API 地址是否正确
   - 注意 CORS 问题（如果跨域）

2. **提示词优化**:
   - 使用英文提示词效果更好
   - 使用逗号分隔关键词
   - 负面提示词可以排除不想要的效果

3. **性能优化**:
   - 采样步数影响生成时间（建议 20-50）
   - 批量生成会增加生成时间
   - 高分辨率会增加生成时间

4. **LoRA 使用**:
   - 确保 LoRA 模型已安装
   - 权重不要设置过高（避免过拟合）
   - 多个 LoRA 可以组合使用

5. **错误处理**:
   - 网络错误：检查 WebUI 是否运行
   - API 错误：检查参数格式
   - 生成错误：检查提示词和参数

## 相关文件

- **主要实现**: `web/script.js` (第 1028-1120 行)
- **LoRA 加载**: `web/script.js` (第 1122-1229 行)
- **API 调用**: `web/script.js` (第 65-120 行)
- **前端界面**: `web/image-gen.html`

