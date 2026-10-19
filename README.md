# emo_agent

墨心智愈：基于 Streamlit 的对话、情绪识别、国画生成、音乐与语音演示项目。

## 本地启动

安装依赖、准备模型并配置本地 `.env` 后，在项目根目录的两个 PowerShell 窗口分别运行：

```powershell
powershell -ExecutionPolicy Bypass -File .\start_local.ps1 -Mode Image
powershell -ExecutionPolicy Bypass -File .\start_local.ps1 -Mode Demo
```

打开 http://127.0.0.1:8502 。完整环境与配置说明见 [项目复现文档](emo_agent/moxin/README_项目复现.md)。

## 传输与协作

Git 和源码 ZIP 包不包含 API 密钥、模型权重、Python 环境、运行输出及 SD WebUI 下载的依赖仓库。换电脑需要按复现文档重新准备；不要将本地 `.env` 上传到仓库。

回归测试、历史聊天、修改方案、赛事资料和第三方源码保留供后续开发参考。废弃文档提取中间文件和旧运行日志仅保留在本地，不随源码传输。未来 Agent 重构尚未实现。
