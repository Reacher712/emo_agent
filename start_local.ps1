param([ValidateSet('Portal', 'Demo', 'Image')][string]$Mode = 'Portal')
$ErrorActionPreference = 'Stop'
$appRoot = Join-Path $PSScriptRoot 'emo_agent\moxin'
if ($Mode -eq 'Image') {
    $workRoot = Join-Path $PSScriptRoot 'emo_agent\stable-diffusion-webui'
    $pythonExe = Join-Path $workRoot 'venv\Scripts\python.exe'
    if (-not (Test-Path -LiteralPath $pythonExe)) { throw 'WebUI environment is missing. See emo_agent/moxin/README_项目复现.md.' }
    Push-Location $workRoot
    try {
        & $pythonExe -u webui.py --nowebui --server-name=127.0.0.1 --port=7860 --disable-extra-extensions --no-download-sd-model --no-half-vae --opt-sdp-attention --ckpt=models/Stable-diffusion/sd_xl_base_1.0.safetensors
    } finally { Pop-Location }
} else {
    $pythonExe = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
    if (-not (Test-Path -LiteralPath $pythonExe)) { throw 'Application environment is missing. See emo_agent/moxin/README_项目复现.md.' }
    $entryFile = if ($Mode -eq 'Demo') { 'demo_frontend.py' } else { 'Home.py' }
    $port = if ($Mode -eq 'Demo') { 8502 } else { 8501 }
    Push-Location $appRoot
    try {
        & $pythonExe -m streamlit run $entryFile --server.address=127.0.0.1 --server.port=$port --browser.gatherUsageStats=false
    } finally { Pop-Location }
}
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
