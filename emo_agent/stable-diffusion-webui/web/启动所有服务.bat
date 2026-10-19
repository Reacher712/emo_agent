@echo off
echo ========================================
echo 启动所有服务（前端 + 后端）
echo ========================================
echo.

cd /d %~dp0

REM 检测并激活虚拟环境
set VENV_ACTIVATE=
set VENV_ACTIVATED=0

REM 尝试激活虚拟环境
if exist "..\venv\Scripts\activate.bat" (
    call ..\venv\Scripts\activate.bat 2>nul
    if %ERRORLEVEL% EQU 0 (
        set VENV_ACTIVATE=call ..\venv\Scripts\activate.bat
        set VENV_ACTIVATED=1
    )
) else if exist "..\.venv\Scripts\activate.bat" (
    call ..\.venv\Scripts\activate.bat 2>nul
    if %ERRORLEVEL% EQU 0 (
        set VENV_ACTIVATE=call ..\.venv\Scripts\activate.bat
        set VENV_ACTIVATED=1
    )
) else if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat 2>nul
    if %ERRORLEVEL% EQU 0 (
        set VENV_ACTIVATE=call venv\Scripts\activate.bat
        set VENV_ACTIVATED=1
    )
) else if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat 2>nul
    if %ERRORLEVEL% EQU 0 (
        set VENV_ACTIVATE=call .venv\Scripts\activate.bat
        set VENV_ACTIVATED=1
    )
)

if %VENV_ACTIVATED% EQU 1 (
    echo [检测到虚拟环境] 将在虚拟环境中启动服务...
) else (
    echo [警告] 未找到虚拟环境或激活失败，将使用系统Python
    echo [建议] 如果遇到问题，请运行"重新创建虚拟环境.bat"
)

echo.
echo 将启动以下服务：
echo   1. 可灵AI后端服务 (http://localhost:5000)
echo   2. 前端HTTP服务器 (http://localhost:8000)
echo.
echo 请确保已安装以下Python包：
echo   - flask
echo   - flask-cors
echo   - pyjwt
echo   - requests
echo   - python-dotenv
echo.
echo 如果未安装，请运行：
echo   pip install flask flask-cors pyjwt requests python-dotenv
echo.
echo 按 Ctrl+C 停止所有服务器
echo ========================================
echo.

echo.
echo [1/2] 启动可灵AI后端服务...
if defined VENV_ACTIVATE (
    start "可灵AI后端服务" cmd /k "%VENV_ACTIVATE% && python kling_backend.py"
) else (
    start "可灵AI后端服务" cmd /k "python kling_backend.py"
)

timeout /t 3 /nobreak >nul

echo.
echo [2/2] 启动前端HTTP服务器...
if defined VENV_ACTIVATE (
    start "前端HTTP服务器" cmd /k "%VENV_ACTIVATE% && python -m http.server 8000"
) else (
    start "前端HTTP服务器" cmd /k "python -m http.server 8000"
)

timeout /t 2 /nobreak >nul

echo.
echo ========================================
echo ✅ 所有服务已启动！
echo ========================================
echo.
echo 后端服务: http://localhost:5000
echo 前端页面: http://localhost:8000/index.html
echo 图生视频: http://localhost:8000/image-to-video.html
echo.
echo 提示：
echo   - 两个服务窗口将分别打开
echo   - 关闭窗口即可停止对应的服务
echo   - 请保持两个窗口都打开，不要关闭
echo.
pause

