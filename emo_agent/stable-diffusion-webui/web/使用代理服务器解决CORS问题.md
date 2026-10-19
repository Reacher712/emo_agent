# 使用代理服务器解决 CORS 问题

## 问题说明

当您通过 `http://localhost:8000` 访问可灵 API 时，可能会遇到 CORS（跨域资源共享）错误。这是因为可灵 API 服务器没有设置允许来自 `http://localhost:8000` 的跨域请求。

## 解决方案：使用代理服务器

我已经为您创建了一个代理服务器脚本 `proxy-server.py`，它可以：
1. 转发请求到可灵 API
2. 添加 CORS 头，允许跨域请求
3. 支持创建任务和查询任务状态

## 使用步骤

### 步骤 1：启动代理服务器

打开命令行，进入项目目录：

```bash
cd d:\stable-diffusion-webui\web
python proxy-server.py
```

您应该看到：

```
🚀 CORS 代理服务器已启动
📡 监听地址: http://localhost:8888
🔗 代理端点: http://localhost:8888/proxy/kling
⚠️  按 Ctrl+C 停止服务器
```

**重要：保持这个命令行窗口打开，不要关闭！**

### 步骤 2：启用代理服务器

打开 `script.js` 文件，找到以下两处代码：

1. **在 `callKlingAPI` 函数中（约第 3490 行）**：
   ```javascript
   const useProxy = false; // 设置为 true 以使用代理服务器
   ```
   改为：
   ```javascript
   const useProxy = true; // 设置为 true 以使用代理服务器
   ```

2. **在 `pollKlingTask` 函数中（约第 3765 行）**：
   ```javascript
   const useProxy = false; // 与 callKlingAPI 中的设置保持一致
   ```
   改为：
   ```javascript
   const useProxy = true; // 与 callKlingAPI 中的设置保持一致
   ```

### 步骤 3：刷新页面并测试

1. 保存 `script.js` 文件
2. 刷新浏览器页面（按 `F5`）
3. 尝试生成视频

## 验证代理服务器是否工作

在浏览器控制台（F12）中，您应该看到：
- API 地址变为：`http://localhost:8888/proxy/kling`
- 不再出现 CORS 错误
- 如果 API 密钥正确，应该可以成功创建任务

## 注意事项

1. **代理服务器必须运行**：使用代理时，必须保持 `proxy-server.py` 运行
2. **API 密钥仍然需要**：代理服务器只是解决 CORS 问题，您仍然需要正确配置可灵 API 密钥
3. **性能影响**：通过代理服务器会有轻微的性能影响，但通常可以忽略

## 如果仍然失败

如果使用代理服务器后仍然失败，请检查：

1. **代理服务器是否正在运行**：
   - 检查命令行窗口是否显示 "🚀 CORS 代理服务器已启动"
   - 尝试访问：`http://localhost:8888/proxy/kling`（应该返回 404，但不会报连接错误）

2. **API 密钥是否正确**：
   - 打开页面设置
   - 检查"可灵访问密钥"和"可灵密钥"是否正确填写

3. **查看控制台错误**：
   - 打开浏览器控制台（F12）
   - 查看具体的错误信息

## 停止代理服务器

当您不需要使用代理服务器时：
1. 在运行 `proxy-server.py` 的命令行窗口中按 `Ctrl+C`
2. 将 `script.js` 中的 `useProxy` 改回 `false`

