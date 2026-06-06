# HunyuanVideo × ComfyUI 安裝整合準備指南

> 事前整理（2026-06 更新）。回到電腦後，照著「第 6 節 安裝清單」一步步做即可；需要我代為安裝時，把這份檔案指給我看。
>
> 來源專案：<https://github.com/Tencent-Hunyuan/HunyuanVideo>

---

## 0. 重要結論（先看這段）

- **建議直接用 HunyuanVideo 1.5（2025 年底發布的新版）**，而不是原始的 HunyuanVideo。
  - 原始版本 720p 需要 **45–60GB+ VRAM**，一般顯卡跑不動。
  - **1.5 版只要 8–24GB VRAM** 就能跑 720p / 1080p，且品質、速度都更好。
- ComfyUI **原生支援（native support）**，不一定要裝 Kijai 的 wrapper，更新 ComfyUI 到最新版即可。
- 模型用 **Comfy-Org 重新打包（repackaged）** 的 `.safetensors` 版本，下載直接丟資料夾就能用。
- VRAM 不夠（8–12GB）就用 **GGUF 量化版**（社群 city96 / 官方插件）。

---

## 1. 硬體與環境需求

| 項目 | 最低 | 建議 |
|------|------|------|
| GPU VRAM（HunyuanVideo 1.5 + GGUF/fp8） | 8 GB | 12–16 GB |
| GPU VRAM（1.5 fp16 720p） | 12 GB | 16–24 GB |
| GPU VRAM（1.5 1080p / 原始 HunyuanVideo） | 24 GB | 48 GB+ |
| 系統記憶體 RAM | 32 GB | 64 GB |
| 硬碟空間 | 60 GB 以上（模型本身就 30–40GB） | 100 GB SSD |
| 作業系統 | Windows / Linux（NVIDIA） | — |

> Mac（Apple Silicon）可跑 ComfyUI，但影片模型效能差、且部分節點不支援，**強烈建議用 NVIDIA 顯卡**。

軟體需求（用 ComfyUI 內建/桌面版的話多半已內含）：

- Python 3.10+（建議 3.10/3.11）
- 最新版 PyTorch（CUDA 12.x 版）
- NVIDIA 驅動 + CUDA 12.4 以上
- （原始版才需要）Flash Attention 2

---

## 2. ComfyUI 本體（先確保是最新版）

二選一：

### A. ComfyUI Desktop（最省事，推薦新手）

- 下載：<https://www.comfy.org/download>
- 安裝後開啟 → 右下角 / 選單檢查更新到最新版。

### B. ComfyUI 可攜版 / Git 版（進階、彈性高）

```bash
# 取得或更新
git clone https://github.com/comfyanonymous/ComfyUI.git
cd ComfyUI
git pull                      # 已存在就更新到最新
pip install -r requirements.txt
```

同時更新 **ComfyUI Manager**（用來一鍵裝缺的節點）：
<https://github.com/Comfy-Org/ComfyUI-Manager>

> ⚠️ HunyuanVideo 1.5 的原生節點需要「夠新」的 ComfyUI。回去第一件事就是**更新到最新版**，不然 workflow 會出現紅色缺節點。

---

## 3. 需要下載的模型（HunyuanVideo 1.5，推薦）

來源（Comfy-Org 官方重打包）：
<https://huggingface.co/Comfy-Org/HunyuanVideo_1.5_repackaged/tree/main/split_files>

下載後依下表放進 `ComfyUI/models/` 對應子資料夾：

### 3.1 Diffusion 模型 → `ComfyUI/models/diffusion_models/`

| 用途 | 檔名 | 備註 |
|------|------|------|
| 文生影片 720p | `hunyuanvideo1.5_720p_t2v_fp16.safetensors` | T2V 主模型 |
| 圖生影片 720p | `hunyuanvideo1.5_720p_i2v_cfg_distilled_fp16.safetensors` | I2V，distilled 較快 |
| 1080p 超解析放大 | `hunyuanvideo1.5_1080p_sr_distilled_fp16.safetensors` | 配合 720p 先生成再放大 |

> 還有 480p、以及 `fp8_scaled`（更省 VRAM）的變體，VRAM 小的話選 fp8 版本。
> 想做哪種就先抓哪種：**只玩文生影片** → 只抓 t2v；**要圖生影片** → 抓 i2v；**要 1080p** → 再加 sr 那顆。

### 3.2 文字編碼器 → `ComfyUI/models/text_encoders/`

| 檔名 | 用途 |
|------|------|
| `qwen_2.5_vl_7b_fp8_scaled.safetensors` | 主文字/視覺編碼器 |
| `byt5_small_glyphxl_fp16.safetensors` | 文字/字形編碼（畫面文字用） |

### 3.3 VAE → `ComfyUI/models/vae/`

| 檔名 |
|------|
| `hunyuanvideo15_vae_fp16.safetensors` |

### 3.4 fp8 省顯存變體（12–16GB 用）

精度選 `fp8_scaled` 的對應檔名（diffusion_models/）：

| 用途 | 檔名 |
|------|------|
| 文生影片 480p | `hunyuanvideo1.5_480p_t2v_cfg_distilled_fp8_scaled.safetensors` |
| 圖生影片 720p | `hunyuanvideo1.5_720p_i2v_cfg_distilled_fp8_scaled.safetensors` |
| 超解析 720p | `hunyuanvideo1.5_720p_sr_distilled_fp8_scaled.safetensors` |

### 3.5 低 VRAM（8–12GB）：改用 GGUF 量化版

- 需安裝節點：**ComfyUI-GGUF**（city96）→ <https://github.com/city96/ComfyUI-GGUF>
- 或官方 1.5 插件：<https://github.com/yuanyuan-spec/comfyui_hunyuanvideo_1.5_plugin>
- GGUF 模型（Q8 / Q6 / Q4）丟到 `ComfyUI/models/unet/` 或 `diffusion_models/`，依插件說明。
- 原則：VRAM 越小選越低的 Q（Q4 最省但品質略降）。

### 3.6 ✅ 一鍵下載腳本（推薦，免手動逐檔抓）

我已準備好下載腳本：**`scripts/download_hunyuanvideo_models.sh`**（會自動抓文字編碼器 + VAE + 你選的 diffusion 模型，放進正確資料夾）。

先裝 HuggingFace CLI：

```bash
pip install -U "huggingface_hub[cli]"
```

執行（依你的顯卡挑參數）：

```bash
# 8-12GB 顯卡、只玩文生影片（省顯存 fp8）
./scripts/download_hunyuanvideo_models.sh -d /path/to/ComfyUI -m t2v -p fp8

# 16-24GB、要圖生影片 + 1080p 放大（fp16）
./scripts/download_hunyuanvideo_models.sh -d /path/to/ComfyUI -m i2v -p fp16 -s

# 全都要（t2v + i2v + sr）
./scripts/download_hunyuanvideo_models.sh -d /path/to/ComfyUI -m all -p fp16
```

參數說明：

| 參數 | 意義 | 可填 |
|------|------|------|
| `-d` | ComfyUI 根目錄（內含 `models/`） | 路徑 |
| `-m` | 模式 | `t2v` / `i2v` / `all` |
| `-p` | 精度 | `fp16` / `fp8` |
| `-s` | 加抓超解析(sr)放大模型 | （加上即啟用） |

> Windows 使用者：用 **Git Bash** 或 **WSL** 執行 `.sh`；或直接用下方 **PowerShell 版**。
> 腳本特性：已下載的檔會自動略過、可重複執行續傳。

#### Windows PowerShell 版：`scripts/download_hunyuanvideo_models.ps1`

功能與 `.sh` 完全相同，原生在 PowerShell 跑（免裝 Git Bash/WSL）：

```powershell
# 8-12GB 顯卡、只玩文生影片（省顯存 fp8）
.\scripts\download_hunyuanvideo_models.ps1 -ComfyuiDir "C:\ComfyUI" -Mode t2v -Precision fp8

# 16-24GB、要圖生影片 + 1080p 放大
.\scripts\download_hunyuanvideo_models.ps1 -ComfyuiDir "C:\ComfyUI" -Mode i2v -Precision fp16 -WithSr

# 全都要
.\scripts\download_hunyuanvideo_models.ps1 -ComfyuiDir "C:\ComfyUI" -Mode all -Precision fp16
```

> 若 PowerShell 擋執行原則，先跑：`Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`

---

## 4. （備選）原始 HunyuanVideo / Kijai Wrapper

只有在你**特別需要原始版功能**（例如某些 V2V / IP2V）時才需要：

- 模型：<https://huggingface.co/tencent/HunyuanVideo>
- Kijai Wrapper 節點：<https://github.com/kijai/ComfyUI-HunyuanVideoWrapper>
  - 在 ComfyUI Manager 搜 `HunyuanVideoWrapper` 安裝，或 `git clone` 到 `ComfyUI/custom_nodes/`。
- 原生版範例模型（舊版 t2v）：
  - `clip_l.safetensors`、`llava_llama3_fp8_scaled.safetensors` → `text_encoders/`
  - `llava_llama3_vision.safetensors` → `clip_vision/`
  - `hunyuan_video_vae_bf16.safetensors` → `vae/`
  - `hunyuan_video_t2v_720p_bf16.safetensors` → `diffusion_models/`

> 一般情況**不用裝這段**，1.5 原生支援就夠用了。

---

## 5. 取得 Workflow（工作流）

ComfyUI 內建模板最穩：

1. 開 ComfyUI → 選單 **Workflow → Browse Templates / Template**。
2. 找 **Hunyuan Video** 類別，選 T2V 或 I2V 模板。
3. 載入後若有紅色節點 → 用 **ComfyUI Manager → Install Missing Custom Nodes** 一鍵補齊。
4. 載入後若提示缺模型 → 多半會給下載連結，或對照第 3 節手動放好。

官方範例與教學頁（回去可參考）：

- 官方文件：<https://docs.comfy.org/tutorials/video/hunyuan/hunyuan-video>
- 官方範例：<https://comfyanonymous.github.io/ComfyUI_examples/hunyuan_video/>
- 1.5 原生支援說明：<https://comfyui.org/en/hunyuanvideo-15-native-support>

---

## 6. 回到電腦後的安裝清單（給我看著做）

> 想讓我幫你裝時，告訴我：① 你的 GPU 型號與 VRAM、② ComfyUI 裝在哪個路徑、③ 要 T2V 還是 I2V、④ 目標解析度（720p / 1080p）。

- [ ] 1. 確認 GPU / VRAM（決定走 fp16 還是 fp8 / GGUF）
- [ ] 2. 安裝或**更新 ComfyUI 到最新版**
- [ ] 3. 安裝 / 更新 **ComfyUI Manager**
- [ ] 4. 安裝 HF CLI：`pip install -U "huggingface_hub[cli]"`
- [ ] 5. 跑一鍵下載腳本：`scripts/download_hunyuanvideo_models.sh -d <ComfyUI路徑> -m <t2v/i2v/all> -p <fp16/fp8>`（見 3.6 節）
- [ ] 6.（VRAM 8–12GB 才需要）裝 **ComfyUI-GGUF** 並改用 GGUF 模型
- [ ] 7. 載入內建 Hunyuan Video 模板（T2V / I2V）
- [ ] 8. Manager → Install Missing Custom Nodes 補齊紅色節點
- [ ] 9. 重啟 ComfyUI → 跑一次低張數（例如 480p、49 frames）測試
- [ ] 10. 確認能出圖後再拉高解析度 / frame 數

---

## 7. 常見問題

- **跑到一半 OOM（爆顯存）**：改用 fp8 或 GGUF 模型、降低解析度與 frame 數、開啟 tiled VAE / 低顯存模式。
- **節點是紅色的**：ComfyUI 沒更新到夠新版本，或缺自訂節點 → 更新 + Manager 補齁。
- **下載很慢**：HuggingFace 可用 `hf download`（huggingface-cli）或開鏡像；模型很大請預留時間與空間。
- **只想出單張圖**：把 video length / frames 設成 1 即可當圖片模型用。

---

## 參考來源

- HunyuanVideo（官方 repo）：<https://github.com/Tencent-Hunyuan/HunyuanVideo>
- Comfy-Org 1.5 重打包模型：<https://huggingface.co/Comfy-Org/HunyuanVideo_1.5_repackaged>
- ComfyUI 官方 Hunyuan 文件：<https://docs.comfy.org/tutorials/video/hunyuan/hunyuan-video>
- 官方範例：<https://comfyanonymous.github.io/ComfyUI_examples/hunyuan_video/>
- 1.5 原生支援：<https://comfyui.org/en/hunyuanvideo-15-native-support>
- Kijai Wrapper：<https://github.com/kijai/ComfyUI-HunyuanVideoWrapper>
- ComfyUI-GGUF（低顯存）：<https://github.com/city96/ComfyUI-GGUF>
- 1.5 官方插件：<https://github.com/yuanyuan-spec/comfyui_hunyuanvideo_1.5_plugin>
