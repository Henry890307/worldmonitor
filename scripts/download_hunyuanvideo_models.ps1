<#
.SYNOPSIS
    HunyuanVideo 1.5 模型一鍵下載腳本（Windows PowerShell 版，ComfyUI 用）

.DESCRIPTION
    自動下載文字編碼器 + VAE + 你選的 diffusion 模型，放進正確資料夾。
    來源：https://huggingface.co/Comfy-Org/HunyuanVideo_1.5_repackaged

.PARAMETER ComfyuiDir
    ComfyUI 根目錄（內含 models\ 資料夾）。預設：目前資料夾

.PARAMETER Mode
    模式：t2v | i2v | all

.PARAMETER Precision
    精度：fp16 | fp8（VRAM 小選 fp8）

.PARAMETER WithSr
    加上此旗標會一併下載超解析(sr)放大模型

.EXAMPLE
    # 8-12GB 顯卡、只玩文生影片（省顯存 fp8）
    .\download_hunyuanvideo_models.ps1 -ComfyuiDir "C:\ComfyUI" -Mode t2v -Precision fp8

.EXAMPLE
    # 16-24GB、要圖生影片 + 1080p 放大
    .\download_hunyuanvideo_models.ps1 -ComfyuiDir "C:\ComfyUI" -Mode i2v -Precision fp16 -WithSr
#>
param(
    [string]$ComfyuiDir = (Get-Location).Path,
    [ValidateSet('t2v', 'i2v', 'all')][string]$Mode = 't2v',
    [ValidateSet('fp16', 'fp8')][string]$Precision = 'fp16',
    [switch]$WithSr
)

$ErrorActionPreference = 'Stop'
$Repo = 'Comfy-Org/HunyuanVideo_1.5_repackaged'

# --- 找到 huggingface 下載指令 ---
if (Get-Command hf -ErrorAction SilentlyContinue) {
    $HfCmd = 'hf'
}
elseif (Get-Command huggingface-cli -ErrorAction SilentlyContinue) {
    $HfCmd = 'huggingface-cli'
}
else {
    Write-Error '找不到 huggingface CLI，請先安裝： pip install -U "huggingface_hub[cli]"'
    exit 1
}

$DmDir  = Join-Path $ComfyuiDir 'models\diffusion_models'
$TeDir  = Join-Path $ComfyuiDir 'models\text_encoders'
$VaeDir = Join-Path $ComfyuiDir 'models\vae'
$null = New-Item -ItemType Directory -Force -Path $DmDir, $TeDir, $VaeDir

function Fetch-Model {
    param([string]$RepoPath, [string]$DestDir)
    $fname = Split-Path $RepoPath -Leaf
    $dest = Join-Path $DestDir $fname
    if (Test-Path $dest) {
        Write-Host "✓ 已存在，略過：$fname"
        return
    }
    Write-Host "↓ 下載：$fname"
    $cached = (& $HfCmd download $Repo $RepoPath | Select-Object -Last 1)
    Copy-Item -Force $cached $dest
    Write-Host "✓ 完成：$dest"
}

Write-Host "=== HunyuanVideo 1.5 下載 ==="
Write-Host "ComfyUI: $ComfyuiDir | 模式: $Mode | 精度: $Precision | 含SR: $($WithSr.IsPresent)"
Write-Host ""

# --- 共用：文字編碼器 + VAE（一定要） ---
Fetch-Model 'split_files/text_encoders/qwen_2.5_vl_7b_fp8_scaled.safetensors' $TeDir
Fetch-Model 'split_files/text_encoders/byt5_small_glyphxl_fp16.safetensors'   $TeDir
Fetch-Model 'split_files/vae/hunyuanvideo15_vae_fp16.safetensors'             $VaeDir

# --- Diffusion 模型 ---
if ($Precision -eq 'fp8') {
    $T2v = 'split_files/diffusion_models/hunyuanvideo1.5_480p_t2v_cfg_distilled_fp8_scaled.safetensors'
    $I2v = 'split_files/diffusion_models/hunyuanvideo1.5_720p_i2v_cfg_distilled_fp8_scaled.safetensors'
    $Sr  = 'split_files/diffusion_models/hunyuanvideo1.5_720p_sr_distilled_fp8_scaled.safetensors'
}
else {
    $T2v = 'split_files/diffusion_models/hunyuanvideo1.5_720p_t2v_fp16.safetensors'
    $I2v = 'split_files/diffusion_models/hunyuanvideo1.5_720p_i2v_cfg_distilled_fp16.safetensors'
    $Sr  = 'split_files/diffusion_models/hunyuanvideo1.5_1080p_sr_distilled_fp16.safetensors'
}

switch ($Mode) {
    't2v' { Fetch-Model $T2v $DmDir }
    'i2v' { Fetch-Model $I2v $DmDir }
    'all' { Fetch-Model $T2v $DmDir; Fetch-Model $I2v $DmDir }
}

if ($WithSr.IsPresent -or $Mode -eq 'all') {
    Fetch-Model $Sr $DmDir
}

Write-Host ""
Write-Host "=== 全部完成！==="
Write-Host "下載到："
Write-Host "  $DmDir"
Write-Host "  $TeDir"
Write-Host "  $VaeDir"
Write-Host "接著開 ComfyUI → 載入 Hunyuan Video 模板即可。"
