#!/usr/bin/env bash
#
# HunyuanVideo 1.5 模型一鍵下載腳本（ComfyUI 用）
# 來源：https://huggingface.co/Comfy-Org/HunyuanVideo_1.5_repackaged
#
# 用法：
#   ./download_hunyuanvideo_models.sh -d /path/to/ComfyUI -m t2v -p fp16
#
#   -d  ComfyUI 根目錄（內含 models/ 資料夾）。預設：目前資料夾
#   -m  模式 mode：t2v | i2v | all   （要不要連 1080p 超解析 sr 一起抓）
#   -p  精度 precision：fp16 | fp8    （VRAM 小選 fp8）
#   -s  也下載 1080p/720p 超解析(sr)模型（i2v/t2v 想放大時用）
#
# 例：
#   8-12GB 顯卡、只玩文生影片：  -m t2v -p fp8
#   16-24GB、要圖生影片+放大：    -m i2v -p fp16 -s
#
set -euo pipefail

COMFYUI_DIR="$(pwd)"
MODE="t2v"
PRECISION="fp16"
WITH_SR="false"
REPO="Comfy-Org/HunyuanVideo_1.5_repackaged"

while getopts "d:m:p:sh" opt; do
  case "$opt" in
    d) COMFYUI_DIR="$OPTARG" ;;
    m) MODE="$OPTARG" ;;
    p) PRECISION="$OPTARG" ;;
    s) WITH_SR="true" ;;
    h) grep '^#' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) echo "未知參數，用 -h 看說明"; exit 1 ;;
  esac
done

# --- 找到 huggingface 下載指令 ---
if command -v hf >/dev/null 2>&1; then
  HF="hf download"
elif command -v huggingface-cli >/dev/null 2>&1; then
  HF="huggingface-cli download"
else
  echo "找不到 huggingface CLI，請先安裝： pip install -U \"huggingface_hub[cli]\""
  exit 1
fi

DM_DIR="$COMFYUI_DIR/models/diffusion_models"
TE_DIR="$COMFYUI_DIR/models/text_encoders"
VAE_DIR="$COMFYUI_DIR/models/vae"
mkdir -p "$DM_DIR" "$TE_DIR" "$VAE_DIR"

# 下載單一檔案到目標資料夾（hf download 會印出快取路徑，再複製過去）
fetch() {
  local repo_path="$1" dest_dir="$2"
  local fname; fname="$(basename "$repo_path")"
  if [ -f "$dest_dir/$fname" ]; then
    echo "✓ 已存在，略過：$fname"
    return
  fi
  echo "↓ 下載：$fname"
  local cached; cached="$($HF "$REPO" "$repo_path" | tail -n1)"
  cp -f "$cached" "$dest_dir/$fname"
  echo "✓ 完成：$dest_dir/$fname"
}

echo "=== HunyuanVideo 1.5 下載 ==="
echo "ComfyUI: $COMFYUI_DIR | 模式: $MODE | 精度: $PRECISION | 含SR: $WITH_SR"
echo

# --- 共用：文字編碼器 + VAE（一定要） ---
fetch "split_files/text_encoders/qwen_2.5_vl_7b_fp8_scaled.safetensors" "$TE_DIR"
fetch "split_files/text_encoders/byt5_small_glyphxl_fp16.safetensors"   "$TE_DIR"
fetch "split_files/vae/hunyuanvideo15_vae_fp16.safetensors"             "$VAE_DIR"

# --- Diffusion 模型 ---
if [ "$PRECISION" = "fp8" ]; then
  T2V="split_files/diffusion_models/hunyuanvideo1.5_480p_t2v_cfg_distilled_fp8_scaled.safetensors"
  I2V="split_files/diffusion_models/hunyuanvideo1.5_720p_i2v_cfg_distilled_fp8_scaled.safetensors"
  SR="split_files/diffusion_models/hunyuanvideo1.5_720p_sr_distilled_fp8_scaled.safetensors"
else
  T2V="split_files/diffusion_models/hunyuanvideo1.5_720p_t2v_fp16.safetensors"
  I2V="split_files/diffusion_models/hunyuanvideo1.5_720p_i2v_cfg_distilled_fp16.safetensors"
  SR="split_files/diffusion_models/hunyuanvideo1.5_1080p_sr_distilled_fp16.safetensors"
fi

case "$MODE" in
  t2v) fetch "$T2V" "$DM_DIR" ;;
  i2v) fetch "$I2V" "$DM_DIR" ;;
  all) fetch "$T2V" "$DM_DIR"; fetch "$I2V" "$DM_DIR" ;;
  *) echo "未知模式 -m：$MODE（用 t2v / i2v / all）"; exit 1 ;;
esac

if [ "$WITH_SR" = "true" ] || [ "$MODE" = "all" ]; then
  fetch "$SR" "$DM_DIR"
fi

echo
echo "=== 全部完成！==="
echo "下載到："
echo "  $DM_DIR"
echo "  $TE_DIR"
echo "  $VAE_DIR"
echo "接著開 ComfyUI → 載入 Hunyuan Video 模板即可。"
