# ============================================
# SD WebUI 全面问题检查脚本
# ============================================

Write-Host "`n🔍 SD WebUI 全面诊断开始..." -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Yellow

# 1. 基础环境检查
Write-Host "`n1. 🏗️  基础环境检查" -ForegroundColor Green
Write-Host "--------------------------------------------" -ForegroundColor DarkGray

$pythonPath = "D:\stable-diffusion-webui\venv\Scripts\python.exe"
if (Test-Path $pythonPath) {
    Write-Host "✅ Python 虚拟环境存在" -ForegroundColor Green
    
    # 检查Python版本
    $pythonVersion = & $pythonPath --version 2>&1
    Write-Host "   Python: $pythonVersion"
    
    # 检查关键包
    $checkCode = @"
import sys
print("=== 包版本检查 ===")
try:
    import numpy
    print(f"numpy: {numpy.__version__}")
except Exception as e:
    print(f"numpy: ❌ {e}")

try:
    import torch
    print(f"torch: {torch.__version__}")
    print(f"CUDA 可用: {torch.cuda.is_available()}")
except Exception as e:
    print(f"torch: ❌ {e}")

try:
    import gradio
    print(f"gradio: {gradio.__version__}")
except Exception as e:
    print(f"gradio: ❌ {e}")

try:
    import librosa
    print(f"librosa: {librosa.__version__}")
except Exception as e:
    print(f"librosa: ❌ {e}")
"@
    
    $checkCode | Out-File -FilePath "temp_check.py" -Encoding UTF8
    $result = & $pythonPath temp_check.py 2>&1
    Remove-Item temp_check.py -ErrorAction SilentlyContinue
    Write-Host $result
    
} else {
    Write-Host "❌ Python 虚拟环境不存在或路径错误" -ForegroundColor Red
}

# 2. 检查 WebUI 启动问题
Write-Host "`n2. 🚀 WebUI 启动检查" -ForegroundColor Green
Write-Host "--------------------------------------------" -ForegroundColor DarkGray

Write-Host "尝试启动 WebUI（测试模式）..."

$launchTest = @"
import sys
import os
sys.path.insert(0, r'D:\stable-diffusion-webui')

# 测试导入关键模块
modules = ['modules.initialize', 'modules.shared', 'webui']

for module in modules:
    try:
        __import__(module)
        print(f"✅ {module} 可导入")
    except Exception as e:
        print(f"❌ {module} 导入失败: {str(e)[:100]}")
        if 'numpy' in str(e) and 'complex' in str(e):
            print("   ⚠️  numpy 兼容性问题！需要 numpy==1.23.5")
"@

$launchTest | Out-File -FilePath "temp_launch.py" -Encoding UTF8
$launchResult = & $pythonPath temp_launch.py 2>&1
Remove-Item temp_launch.py -ErrorAction SilentlyContinue
Write-Host $launchResult

# 3. 检查端口和服务
Write-Host "`n3. 🔌 网络和端口检查" -ForegroundColor Green
Write-Host "--------------------------------------------" -ForegroundColor DarkGray

# 检查端口占用
Write-Host "检查端口 7860-7865:"
7860..7865 | ForEach-Object {
    $port = $_
    $netstat = netstat -ano 2>$null | Select-String ":$port\s"
    if ($netstat) {
        Write-Host "   端口 $port : 🔴 被占用" -ForegroundColor Red
        # 尝试获取进程信息
        $pidMatch = $netstat -match '(\d+)$'
        if ($pidMatch) {
            $pid = $Matches[1]
            $process = Get-Process -Id $pid -ErrorAction SilentlyContinue
            if ($process) {
                Write-Host "       进程: $($process.ProcessName) (PID: $pid)" -ForegroundColor Yellow
            }
        }
    } else {
        Write-Host "   端口 $port : 🟢 空闲" -ForegroundColor Green
    }
}

# 4. 检查扩展
Write-Host "`n4. 🔧 扩展检查" -ForegroundColor Green
Write-Host "--------------------------------------------" -ForegroundColor DarkGray

$extensionsPath = "D:\stable-diffusion-webui\extensions"
if (Test-Path $extensionsPath) {
    $extensions = Get-ChildItem $extensionsPath -Directory | Select-Object -ExpandProperty Name
    Write-Host "已安装扩展 ($($extensions.Count) 个):"
    foreach ($ext in $extensions) {
        Write-Host "   📁 $ext"
        
        # 检查 SadTalker 特别
        if ($ext -eq "SadTalker") {
            $sadTalkerPath = Join-Path $extensionsPath "SadTalker"
            $hasScript = Test-Path (Join-Path $sadTalkerPath "scripts\script.py")
            $hasApp = Test-Path (Join-Path $sadTalkerPath "app_sadtalker.py")
            
            if ($hasScript) { Write-Host "      ✅ 有 script.py (WebUI集成)" }
            if ($hasApp) { Write-Host "      ✅ 有 app_sadtalker.py (独立启动)" }
            
            # 检查 Gradio 配置
            $gradioFiles = Get-ChildItem $sadTalkerPath -Recurse -Filter "*.py" | Select-String -Pattern "gradio|launch\(|Interface" | Select-Object -First 3
            if ($gradioFiles) {
                Write-Host "      🔍 找到 Gradio 相关代码"
            }
        }
    }
}

# 5. 检查文件和权限
Write-Host "`n5. 📁 文件和权限检查" -ForegroundColor Green
Write-Host "--------------------------------------------" -ForegroundColor DarkGray

$criticalFiles = @(
    "D:\stable-diffusion-webui\webui.py",
    "D:\stable-diffusion-webui\launch.py",
    "D:\stable-diffusion-webui\requirements.txt",
    "D:\stable-diffusion-webui\venv\Scripts\activate",
    "D:\stable-diffusion-webui\models\Stable-diffusion\",
    "D:\stable-diffusion-webui\extensions"
)

foreach ($file in $criticalFiles) {
    if (Test-Path $file) {
        $type = if ((Get-Item $file).PSIsContainer) { "目录" } else { "文件" }
        Write-Host "   ✅ $type存在: $(Split-Path $file -Leaf)" -ForegroundColor Green
    } else {
        Write-Host "   ❌ 缺失: $file" -ForegroundColor Red
    }
}

# 6. 虚拟环境对比
Write-Host "`n6. 🔄 虚拟环境对比" -ForegroundColor Green
Write-Host "--------------------------------------------" -ForegroundColor DarkGray

Write-Host "当前环境:"
& python --version 2>&1
Write-Host "路径: $($env:PYTHONPATH)"

Write-Host "`nWebUI 虚拟环境包:"
$envCheck = @"
import pkg_resources
packages = ['numpy', 'gradio', 'torch', 'librosa']
for pkg in packages:
    try:
        dist = pkg_resources.get_distribution(pkg)
        print(f"{pkg}: {dist.version}")
    except:
        print(f"{pkg}: 未安装")
"@

$envCheck | Out-File -FilePath "temp_env.py" -Encoding UTF8
$envResult = & $pythonPath temp_env.py 2>&1
Remove-Item temp_env.py -ErrorAction SilentlyContinue
Write-Host $envResult

# 7. 问题总结
Write-Host "`n7. 📋 问题总结与建议" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Yellow

Write-Host "🔴 已确认问题:" -ForegroundColor Red
Write-Host "   1. numpy 兼容性问题 (librosa 需要 numpy<1.24)"
Write-Host "   2. SadTalker Gradio 资源 404 错误"
Write-Host "   3. 可能的端口冲突"

Write-Host "`n🟡 潜在问题:" -ForegroundColor Yellow
Write-Host "   1. 两个虚拟环境可能存在冲突"
Write-Host "   2. 扩展可能未正确加载"
Write-Host "   3. 权限或路径问题"

Write-Host "`n🟢 解决方案:" -ForegroundColor Green
Write-Host "   1. 修复 numpy: pip install numpy==1.23.5"
Write-Host "   2. 检查端口: 确保 7860 未被占用"
Write-Host "   3. 正确启动: 使用 webui-user.bat"
Write-Host "   4. 扩展测试: 逐个启用扩展"

Write-Host "`n🚀 立即执行的修复命令:" -ForegroundColor Magenta
Write-Host "   cd D:\stable-diffusion-webui"
Write-Host "   .\venv\Scripts\activate"
Write-Host "   pip install numpy==1.23.5 librosa==0.9.2 --upgrade"
Write-Host "   .\webui-user.bat"

Write-Host "`n============================================" -ForegroundColor Yellow
Write-Host "诊断完成！按问题严重性排序修复。" -ForegroundColor Cyan
