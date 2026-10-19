@echo off
echo ========================================
echo 启动可灵AI后端服务
echo ========================================
echo.

cd /d %~dp0

REM 尝试激活虚拟环境，如果失败则使用系统Python
set VENV_ACTIVATED=0
if exist "..\venv\Scripts\activate.bat" (
    echo [检测到虚拟环境] 尝试激活 venv 虚拟环境...
    call ..\venv\Scripts\activate.bat 2>nul
    if %ERRORLEVEL% EQU 0 (
        set VENV_ACTIVATED=1
        echo [成功] 虚拟环境已激活
    ) else (
        echo [警告] 虚拟环境激活失败，可能是路径不匹配
        echo [提示] 将使用系统Python，如果遇到模块未找到错误，请运行"重新创建虚拟环境.bat"
        set VENV_ACTIVATED=0
    )
) else if exist "..\.venv\Scripts\activate.bat" (
    echo [检测到虚拟环境] 尝试激活 .venv 虚拟环境...
    call ..\.venv\Scripts\activate.bat 2>nul
    if %ERRORLEVEL% EQU 0 (
        set VENV_ACTIVATED=1
        echo [成功] 虚拟环境已激活
    ) else (
        echo [警告] 虚拟环境激活失败，可能是路径不匹配
        echo [提示] 将使用系统Python，如果遇到模块未找到错误，请运行"重新创建虚拟环境.bat"
        set VENV_ACTIVATED=0
    )
) else (
    echo [提示] 未找到虚拟环境，将使用系统Python
    echo [建议] 如果遇到模块未找到错误，请运行"重新创建虚拟环境.bat"
    echo.
    set VENV_ACTIVATED=0
)

echo.
echo 后端服务将在 http://localhost:5000 启动
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
echo 按 Ctrl+C 停止服务器
echo ========================================
echo.

python kling_backend.py

pause

