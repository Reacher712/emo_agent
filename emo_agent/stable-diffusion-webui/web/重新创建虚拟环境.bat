@echo off
echo ========================================
echo 重新创建虚拟环境
echo ========================================
echo.
echo 此脚本将：
echo   1. 删除旧的虚拟环境（如果存在）
echo   2. 创建新的虚拟环境
echo   3. 安装可灵AI后端依赖
echo.
echo 警告：这将删除现有的虚拟环境！
echo.
set /p confirm=是否继续？(Y/N): 
if /i not "%confirm%"=="Y" (
    echo 已取消
    pause
    exit /b
)

cd /d %~dp0
cd ..

echo.
echo [1/3] 删除旧的虚拟环境...
if exist "venv" (
    echo 正在删除 venv 目录...
    rmdir /s /q venv 2>nul
    if %ERRORLEVEL% EQU 0 (
        echo ✅ 旧虚拟环境已删除
    ) else (
        echo ⚠️  删除失败，可能需要手动删除 venv 目录
    )
) else (
    echo ℹ️  未找到 venv 目录，跳过删除
)

if exist ".venv" (
    echo 正在删除 .venv 目录...
    rmdir /s /q .venv 2>nul
    if %ERRORLEVEL% EQU 0 (
        echo ✅ 旧虚拟环境已删除
    ) else (
        echo ⚠️  删除失败，可能需要手动删除 .venv 目录
    )
) else (
    echo ℹ️  未找到 .venv 目录，跳过删除
)

echo.
echo [2/3] 创建新的虚拟环境...
python -m venv venv
if %ERRORLEVEL% EQU 0 (
    echo ✅ 虚拟环境创建成功
) else (
    echo ❌ 虚拟环境创建失败
    echo 请检查Python是否正确安装
    pause
    exit /b
)

echo.
echo [3/3] 激活虚拟环境并安装依赖...
call venv\Scripts\activate.bat
if %ERRORLEVEL% EQU 0 (
    echo ✅ 虚拟环境已激活
) else (
    echo ❌ 虚拟环境激活失败
    pause
    exit /b
)

echo.
echo 正在安装依赖包...
python -m pip install --upgrade pip
python -m pip install flask flask-cors pyjwt requests python-dotenv

echo.
echo ========================================
if %ERRORLEVEL% EQU 0 (
    echo ✅ 虚拟环境创建和依赖安装完成！
    echo.
    echo 现在可以运行：
    echo   - start-kling-backend.bat
    echo   - 启动所有服务.bat
) else (
    echo ❌ 依赖安装失败，请检查错误信息
)
echo ========================================
echo.

pause

