# AI News Shorts — CapCut PoC

A semi-automated pipeline for producing 1-minute IG Reels (9:16) about AI news/tools.
Generates news → script → voice → subtitles → images → CapCut draft, then opens in CapCut
for manual polish and export.

## Target environment

- **Windows 10/11**
- Python 3.11+
- CapCut International (recommended) or 剪映専業版 4.x
- ~5 GB free for Whisper models

## Quick start on Windows

```powershell
# 1. Clone or copy this folder to D:\projects\ai-news-shorts\
cd D:\projects\ai-news-shorts

# 2. Create venv and install deps
py -3.11 -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt

# 3. Copy .env.example to .env and fill ANTHROPIC_API_KEY, UNSPLASH_KEY
copy .env.example .env
notepad .env

# 4. Edit config\settings.yaml: confirm CAPCUT_PROJECTS_DIR points to your install
#    Default: %LocalAppData%\CapCut\User Data\Projects\com.lveditor.draft

# 5. CRITICAL ONE-TIME STEP: capture a known-good draft template
#    a. Open CapCut, create a new 1080x1920 project named "template_seed"
#    b. Add: 3 image clips (20s each), 1 audio track (voice), 1 audio track (BGM at -15dB),
#       1 subtitle layer with Chinese text using your preferred font
#    c. Save and close CapCut
#    d. Copy the project's draft_content.json to assets\templates\known_good_draft.json
#    Path: %LocalAppData%\CapCut\User Data\Projects\com.lveditor.draft\template_seed\draft_content.json

# 6. Run the pipeline
python src\pipeline.py --id poc_001
```

After step 6, a new CapCut project named `poc_001` appears in CapCut's project list.
Open it, do manual polish (timing tweaks, emphasize key words, add stickers), then
export 1080x1920 H.264.

## Pipeline stages

| # | Stage | Script | Output |
|---|-------|--------|--------|
| 1 | Fetch news | `src\fetch_news.py` | `workspace\<id>\news.json` |
| 2 | Generate script | `src\gen_script.py` | `workspace\<id>\script.txt` |
| 3 | Generate voice | `src\gen_voice.py` | `workspace\<id>\voice.mp3` |
| 4 | Generate subs | `src\gen_subs.py` | `workspace\<id>\subs.srt` |
| 5 | Prepare images | `src\gen_images.py` | `workspace\<id>\images\*.jpg` |
| 6 | Build draft | `src\build_draft.py` | `workspace\<id>\draft\` |
| 7 | Deploy to CapCut | `tools\deploy_draft.py` | CapCut Projects dir |

## Why this architecture

CapCut has no public API. Community has reverse-engineered the on-disk draft format
(`draft_content.json`). We use a **template-based** approach:

1. You manually build one "perfect" 1-minute project in CapCut UI.
2. We save that as a known-good template.
3. The pipeline loads the template JSON and patches only: media file paths,
   subtitle text segments, segment durations.

This is more robust than generating draft JSON from scratch (CapCut's schema changes
between versions and undocumented fields can break playback).

## Risks / known issues

- **CapCut version drift**: each CapCut update can change schema. If draft fails to open,
  re-capture `known_good_draft.json` from your current CapCut version.
- **Chinese font missing**: CapCut references fonts by ID, not name. Always capture
  the font choice in the template — do not try to set fonts programmatically.
- **Whisper mis-transcribes English in Chinese text**: pass `language=None` to faster-whisper
  for auto-detect.

## License / dependencies

Free-tier only:
- HN Algolia API (no key required)
- Unsplash API (free with key)
- Edge-TTS (Microsoft Neural TTS, free)
- faster-whisper (Apache 2.0, runs locally)
- Claude API (small cost for script generation; optional — can hand-write scripts)
