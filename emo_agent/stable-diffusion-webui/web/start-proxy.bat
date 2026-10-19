@echo off
chcp 65001 >nul
echo ========================================
echo 启动 CORS 代理服务器
echo ========================================
echo.
echo 此服务器用于解决可灵 API 的 CORS 问题
echo.
echo 服务器将在 http://localhost:8888 启动
echo.
echo 代理端点: http://localhost:8888/proxy/kling
echo.
echo ⚠️  请保持此窗口打开，不要关闭！
echo.
echo 按 Ctrl+C 停止服务器
echo ========================================
echo.

cd /d %~dp0
python proxy-server.py

pause

