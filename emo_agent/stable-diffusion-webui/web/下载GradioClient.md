# 下载 Gradio Client 到本地（解决 CORS 问题）

如果 CDN 加载遇到 CORS 问题，可以将 Gradio Client 下载到本地。

## 方法 1：使用 npm 下载（推荐）

```bash
cd d:\stable-diffusion-webui\web
npm install @gradio/client@0.15.0
```

然后修改 `voice-clone.html` 中的导入语句：

```javascript
import { Client } from "./node_modules/@gradio/client/dist/index.mjs";
```

## 方法 2：手动下载

1. 访问：https://unpkg.com/@gradio/client@0.15.0/dist/
2. 下载 `index.mjs` 文件
3. 保存到 `web/gradio-client/` 目录
4. 修改导入语句：

```javascript
import { Client } from "./gradio-client/index.mjs";
```

## 方法 3：使用其他 CDN（已实现）

当前代码已使用 `esm.sh` CDN，它支持 CORS。如果仍有问题，可以尝试：

- `https://cdn.jsdelivr.net/npm/@gradio/client@0.15.0/dist/index.mjs`
- `https://cdn.skypack.dev/@gradio/client@0.15.0`

