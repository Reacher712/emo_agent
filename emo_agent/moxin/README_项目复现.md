# 墨心智愈项目复现说明

## 推荐启动方式

当前机器上默认 `python` 入口不可用，推荐使用 Anaconda 环境：

```powershell
cd /d D:\moxin
D:\anconda\python.exe -m streamlit run Home.py
```

启动后访问：

```text
http://localhost:8501
```

也可以直接双击：

```text
D:\moxin\start_portal.bat
```

## 已复现功能

- 首页演示门户
- 疗愈对话：离线共情回复，可选调用 `run_pipeline.py` 完整闭环
- 疗效评估：PHQ-9 / GAD-7 / WHO-5 自评与本地记录
- 多模态入口：文本、语音线索、面部自评融合并送入对话页
- 青年调研看板、赛事实证材料、项目资料枢纽

## 完整闭环依赖

如果需要演示“情绪识别 -> 国画生成 -> 音乐生成”的完整链路，请额外确认：

- Stable Diffusion WebUI/Forge API 已启动，默认地址 `http://127.0.0.1:7860`
- `.env` 中的大模型、音乐或语音服务配置已填写
- `run_pipeline.py` 可单独运行

## 环境依赖

当前 Anaconda 环境已包含主要依赖。若换机器复现，可安装：

```powershell
pip install -r requirements-repro.txt
```
