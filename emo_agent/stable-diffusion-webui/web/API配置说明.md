# Stable Diffusion WebUI API 配置说明

## 一、启动 Stable Diffusion WebUI 的 API 模式

### 方法1：使用启动参数（推荐）

在运行 Stable Diffusion WebUI 时，添加以下启动参数：

#### Windows (webui-user.bat):
```batch
set COMMANDLINE_ARGS=--api --listen 0.0.0.0 --enable-insecure-extension-access
```

或者直接编辑 `webui-user.bat` 文件，找到 `COMMANDLINE_ARGS` 行，修改为：
```batch
set COMMANDLINE_ARGS=--api --listen 0.0.0.0 --enable-insecure-extension-access
```

#### Linux/Mac (webui.sh):
```bash
export COMMANDLINE_ARGS="--api --listen 0.0.0.0 --enable-insecure-extension-access"
```

### 启动参数说明：
- `--api`: 启用 API 接口
- `--listen 0.0.0.0`: 允许外部设备访问（如果不加这个，只能本机访问）
- `--enable-insecure-extension-access`: 允许扩展访问（可选，如果需要扩展功能）

### 方法2：修改 launch.py

如果方法1不适用，可以修改 `launch.py` 文件，找到启动参数部分，添加 `--api` 参数。

## 二、查找运行 WebUI 设备的 IP 地址

### Windows:
1. 打开命令提示符（CMD）或 PowerShell
2. 输入：`ipconfig`
3. 找到 "IPv4 地址"，例如：`192.168.1.100`

### Linux/Mac:
1. 打开终端
2. 输入：`ifconfig` 或 `ip addr`
3. 找到对应网络接口的 IP 地址

### 注意事项：
- 确保前端设备和 WebUI 设备在同一局域网内
- 如果使用 WiFi，确保连接到同一个 WiFi 网络
- 如果使用有线网络，确保在同一子网内

## 三、配置前端页面

### 方法1：在页面中设置（推荐）

1. 打开前端页面
2. 点击右上角"设置"按钮
3. 在"Stable Diffusion WebUI API 地址"中输入：
   ```
   http://[WebUI设备的IP地址]:7860
   ```
   例如：`http://192.168.1.100:7860`
4. 点击"保存"

### 方法2：直接修改代码

编辑 `script.js` 文件，找到：
```javascript
apiUrl: localStorage.getItem('apiUrl') || 'http://localhost:7860',
```

修改为：
```javascript
apiUrl: localStorage.getItem('apiUrl') || 'http://[WebUI设备的IP地址]:7860',
```

## 四、解决跨域问题（CORS）

如果遇到跨域错误，需要在 WebUI 设备上处理 CORS。

### 方法1：使用 CORS 扩展（推荐）

1. 在 Stable Diffusion WebUI 中安装 CORS 扩展
2. 或者使用以下启动参数：
   ```
   --cors-allow-origins="*"
   ```

### 方法2：修改 WebUI 代码

如果上述方法不行，可以修改 WebUI 的启动脚本，添加 CORS 头。

### 方法3：使用代理服务器（高级）

在前端设备和 WebUI 设备之间设置代理服务器来处理 CORS。

## 五、测试连接

### 测试 API 是否可用：

在浏览器中访问（将 IP 替换为实际 IP）：
```
http://192.168.1.100:7860/sdapi/v1/ping
```

或者：
```
http://192.168.1.100:7860/docs
```

如果能看到 API 文档页面，说明 API 已经启用。

### 在前端页面测试：

1. 打开前端页面
2. 切换到"图片生成"标签
3. 输入一个简单的描述，例如："a cat"
4. 点击"生成图片"
5. 观察是否能够成功生成

## 六、常见问题排查

### 1. 连接被拒绝（Connection Refused）
- **原因**：WebUI 未启动 API 模式或防火墙阻止
- **解决**：
  - 检查 WebUI 是否已启动
  - 确认启动时添加了 `--api` 参数
  - 检查防火墙设置，允许 7860 端口

### 2. 跨域错误（CORS Error）
- **原因**：浏览器阻止跨域请求
- **解决**：参考第四部分的 CORS 配置

### 3. 404 Not Found
- **原因**：API 路径错误
- **解决**：确认 API 地址格式为 `http://IP:7860`，不要加 `/api` 后缀

### 4. 请求超时（Timeout）
- **原因**：网络连接问题或生成时间过长
- **解决**：
  - 检查网络连接
  - 在 `script.js` 中增加超时时间设置
  - 检查 WebUI 设备性能

### 5. 生成的图片是黑色的
- **原因**：模型加载问题或参数设置错误
- **解决**：
  - 检查 WebUI 中的模型是否正确加载
  - 尝试在 WebUI 界面手动生成一次图片
  - 检查 API 参数是否正确

## 七、API 参数说明

前端代码中使用的 API 参数：

- `prompt`: 正面提示词
- `negative_prompt`: 负面提示词
- `steps`: 采样步数（默认 20）
- `cfg_scale`: 引导强度（默认 7）
- `width/height`: 图片尺寸
- `sampler_index`: 采样器（默认 DPM++ 2M Karras）
- `batch_size`: 批量生成数量（最多 4）

可以在 `script.js` 的 `mockImageGeneration` 函数中调整这些参数。

## 八、安全注意事项

1. **仅在内网使用**：不要将 WebUI 暴露到公网，除非你清楚安全风险
2. **使用防火墙**：限制访问来源
3. **定期更新**：保持 WebUI 和模型文件的更新
4. **访问控制**：如果可能，添加身份验证

## 九、性能优化建议

1. **批量生成**：一次生成多张图片时，使用 `batch_size` 而不是多次调用
2. **图片尺寸**：较小的尺寸生成更快
3. **采样步数**：减少步数可以加快生成速度（但可能影响质量）
4. **使用 GPU**：确保 WebUI 使用 GPU 加速

## 十、联系与支持

如果遇到问题：
1. 检查 WebUI 的终端输出，查看错误信息
2. 打开浏览器开发者工具（F12），查看控制台错误
3. 确认 API 地址和网络连接

