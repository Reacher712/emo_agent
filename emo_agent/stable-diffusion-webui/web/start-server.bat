@echo off
echo ========================================
echo 启动本地HTTP服务器
echo ========================================
echo.
echo 服务器将在 http://localhost:8000 启动
echo.
echo 请在浏览器中访问: http://localhost:8000/index.html
echo.
echo 按 Ctrl+C 停止服务器
echo ========================================
echo.

cd /d %~dp0
python -m http.server 8000

pause

