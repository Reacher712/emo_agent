@echo off
echo ========================================
echo 安装可灵AI后端依赖
echo ========================================
echo.

cd /d %~dp0

REM 尝试激活虚拟环境，如果失败则使用系统Python
set USE_VENV=0
if exist "..\venv\Scripts\activate.bat" (
    echo [检测到虚拟环境] 尝试激活 venv 虚拟环境...
    call ..\venv\Scripts\activate.bat 2>nul
    if %ERRORLEVEL% EQU 0 (
        set USE_VENV=1
        echo [成功] 虚拟环境已激活
    ) else (
        echo [警告] 虚拟环境激活失败，可能是路径不匹配
        echo [提示] 将使用系统Python安装依赖
        set USE_VENV=0
    )
) else if exist "..\.venv\Scripts\activate.bat" (
    echo [检测到虚拟环境] 尝试激活 .venv 虚拟环境...
    call ..\.venv\Scripts\activate.bat 2>nul
    if %ERRORLEVEL% EQU 0 (
        set USE_VENV=1
        echo [成功] 虚拟环境已激活
    ) else (
        echo [警告] 虚拟环境激活失败，可能是路径不匹配
        echo [提示] 将使用系统Python安装依赖
        set USE_VENV=0
    )
) else (
    echo [提示] 未找到虚拟环境，将使用系统Python安装依赖
    echo [建议] 如果遇到问题，可以重新创建虚拟环境：
    echo   cd ..
    echo   python -m venv venv
    echo   venv\Scripts\activate
    echo   pip install flask flask-cors pyjwt requests python-dotenv
    echo.
    set USE_VENV=0
)

echo.
echo 正在安装以下Python包：
echo   - flask
echo   - flask-cors
echo   - pyjwt
echo   - requests
echo   - python-dotenv
echo.

REM 使用 python -m pip 而不是直接使用 pip，更可靠
python -m pip install flask flask-cors pyjwt requests python-dotenv

echo.
echo ========================================
if %ERRORLEVEL% EQU 0 (
    echo ✅ 依赖安装成功！
) else (
    echo ❌ 依赖安装失败，请检查错误信息
    echo.
    echo 如果虚拟环境路径不匹配，可以：
    echo   1. 删除旧的虚拟环境
    echo   2. 重新创建虚拟环境
    echo   3. 或使用系统Python（当前方式）
)
echo ========================================
echo.

pause

