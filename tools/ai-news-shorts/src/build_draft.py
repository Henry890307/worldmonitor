"""Build a CapCut draft folder by patching a known-good template.

Strategy: rather than synthesizing draft_content.json from scratch (CapCut's schema
is undocumented and changes between versions), we load a hand-crafted template that
the user previously saved from CapCut UI, and rewrite only the parts we need:

  - audio material paths (replace template voice + BGM)
  - video material paths (replace template's 3 image clips)
  - text segments (replace with subtitle text from SRT)
  - durations (extend or shrink to match real voice.mp3 length)

The template MUST be captured first; see README section "CRITICAL ONE-TIME STEP".
"""
from __future__ import annotations

import json
import shutil
import subprocess
import uuid
from pathlib import Path

import click
import pysrt

from _common import ROOT, load_settings, workspace_dir


def _us(seconds: float) -> int:
    """Convert seconds to microseconds (CapCut's internal unit)."""
    return int(round(seconds * 1_000_000))


def _probe_duration_sec(media_path: Path) -> float:
    """Use ffprobe to get exact duration. Falls back to settings default if missing."""
    try:
        out = subprocess.check_output([
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", str(media_path),
        ], stderr=subprocess.STDOUT, timeout=10)
        return float(out.strip())
    except (FileNotFoundError, subprocess.CalledProcessError, ValueError):
        return 0.0


def _parse_srt_segments(srt_path: Path) -> list[tuple[int, int, str]]:
    """Return list of (start_us, end_us, text)."""
    subs = pysrt.open(str(srt_path), encoding="utf-8")
    out = []
    for s in subs:
        start = (s.start.hours * 3600 + s.start.minutes * 60 + s.start.seconds) * 1_000_000 + s.start.milliseconds * 1000
        end = (s.end.hours * 3600 + s.end.minutes * 60 + s.end.seconds) * 1_000_000 + s.end.milliseconds * 1000
        out.append((start, end, s.text.replace("\n", " ").strip()))
    return out


def _patch_audio_materials(draft: dict, voice_path: Path, bgm_path: Path | None,
                            voice_duration_us: int) -> None:
    """Rewrite audio material entries: first = voice, second (if exists) = BGM."""
    audios = draft.get("materials", {}).get("audios", [])
    if not audios:
        raise RuntimeError("Template has no audio materials; cannot place voice")
    # First audio = voice
    audios[0]["path"] = str(voice_path)
    audios[0]["name"] = voice_path.name
    audios[0]["duration"] = voice_duration_us
    # Second audio (BGM) if template has it and we have one
    if len(audios) >= 2 and bgm_path and bgm_path.exists():
        audios[1]["path"] = str(bgm_path)
        audios[1]["name"] = bgm_path.name


def _patch_video_materials(draft: dict, image_paths: list[Path]) -> None:
    """Replace template image/video materials with our generated images."""
    videos = draft.get("materials", {}).get("videos", [])
    if not videos:
        raise RuntimeError("Template has no video materials")
    # CapCut may store both images and videos in `videos`; patch in order.
    for i, img in enumerate(image_paths):
        if i >= len(videos):
            break
        videos[i]["path"] = str(img)
        videos[i]["name"] = img.name
        # Image type: leave width/height since they may be referenced by canvas


def _patch_text_segments(draft: dict, srt_segments: list[tuple[int, int, str]]) -> None:
    """Rewrite the text material entries and the corresponding track segments.

    We expect the template to have N text materials and one text track with N
    segments. If our SRT has more lines than the template, we duplicate the last
    text material's style and append; if fewer, we trim.
    """
    materials = draft.setdefault("materials", {})
    texts = materials.setdefault("texts", [])
    tracks = draft.setdefault("tracks", [])

    text_track = None
    for t in tracks:
        if t.get("type") == "text":
            text_track = t
            break
    if text_track is None or not texts:
        click.echo("WARNING: template has no text track; skipping subtitle patch.")
        click.echo("         Add a subtitle in CapCut UI and re-export the template.")
        return

    template_text = texts[0]
    template_seg = text_track["segments"][0] if text_track["segments"] else None
    if template_seg is None:
        click.echo("WARNING: text track has no segment template; skipping.")
        return

    new_texts = []
    new_segments = []
    for idx, (start_us, end_us, line) in enumerate(srt_segments):
        # Clone template text material
        mat = json.loads(json.dumps(template_text))
        mat["id"] = str(uuid.uuid4())
        # CapCut stores text content inside a "content" JSON string; if missing fall back
        if "content" in mat and isinstance(mat["content"], str):
            try:
                inner = json.loads(mat["content"])
                inner["text"] = line
                mat["content"] = json.dumps(inner, ensure_ascii=False)
            except json.JSONDecodeError:
                mat["content"] = line
        else:
            mat["text"] = line
        new_texts.append(mat)

        seg = json.loads(json.dumps(template_seg))
        seg["id"] = str(uuid.uuid4())
        seg["material_id"] = mat["id"]
        seg["target_timerange"] = {
            "start": start_us,
            "duration": max(end_us - start_us, 200_000),  # min 0.2s
        }
        new_segments.append(seg)

    materials["texts"] = new_texts
    text_track["segments"] = new_segments


def _patch_main_track_segments(draft: dict, image_paths: list[Path],
                                total_us: int) -> None:
    """Resize each image segment so 3 images cover the full voice duration evenly."""
    tracks = draft.get("tracks", [])
    main_track = None
    for t in tracks:
        if t.get("type") == "video":
            main_track = t
            break
    if main_track is None:
        click.echo("WARNING: no main video track found; skipping image timing patch.")
        return

    segments = main_track.get("segments", [])
    n = min(len(segments), len(image_paths))
    if n == 0:
        return
    per_seg = total_us // n
    for i in range(n):
        segments[i]["target_timerange"] = {
            "start": i * per_seg,
            "duration": per_seg if i < n - 1 else total_us - per_seg * (n - 1),
        }
    # Drop any extra template segments beyond our image count
    main_track["segments"] = segments[:n]


def _patch_audio_segments(draft: dict, voice_duration_us: int) -> None:
    """Stretch voice + BGM track segments to match the actual voice duration."""
    for track in draft.get("tracks", []):
        if track.get("type") != "audio":
            continue
        for seg in track.get("segments", []):
            seg.setdefault("target_timerange", {})
            seg["target_timerange"]["start"] = 0
            seg["target_timerange"]["duration"] = voice_duration_us
            # Also expand source_timerange if present
            if "source_timerange" in seg:
                seg["source_timerange"]["duration"] = voice_duration_us


def _patch_top_level_duration(draft: dict, duration_us: int) -> None:
    draft["duration"] = duration_us


def _write_meta_info(draft_dir: Path, video_id: str) -> None:
    """Write a minimal draft_meta_info.json so CapCut shows the project in its list."""
    meta = {
        "draft_id": str(uuid.uuid4()),
        "draft_name": video_id,
        "draft_fold_path": str(draft_dir).replace("/", "\\"),
        "draft_timeline_materials_size_": 0,
        "tm_draft_create": 0,
        "tm_draft_modified": 0,
    }
    (draft_dir / "draft_meta_info.json").write_text(
        json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8"
    )


def build(video_id: str) -> Path:
    cfg = load_settings()
    ws = workspace_dir(video_id)

    template_path = ROOT / cfg["pipeline"]["template_path"]
    if not template_path.exists():
        raise click.ClickException(
            f"Template not found: {template_path}\n"
            "Capture it from CapCut UI first (see README step 5)."
        )

    voice_path = ws / "voice.mp3"
    if not voice_path.exists():
        raise click.ClickException("voice.mp3 missing; run gen_voice first")

    images_dir = ws / "images"
    image_paths = sorted(images_dir.glob("*.jpg")) + sorted(images_dir.glob("*.png"))
    if len(image_paths) < cfg["video"]["image_count"]:
        raise click.ClickException(
            f"Need {cfg['video']['image_count']} images in {images_dir}, "
            f"found {len(image_paths)}"
        )
    image_paths = image_paths[:cfg["video"]["image_count"]]

    srt_path = ws / "subs.srt"
    srt_segments = _parse_srt_segments(srt_path) if srt_path.exists() else []

    bgm_path = ROOT / cfg["pipeline"]["bgm_path"]

    voice_duration_sec = _probe_duration_sec(voice_path) or float(cfg["video"]["duration_sec"])
    voice_duration_us = _us(voice_duration_sec)
    click.echo(f"Voice duration: {voice_duration_sec:.2f}s")

    draft = json.loads(template_path.read_text(encoding="utf-8"))

    _patch_audio_materials(draft, voice_path, bgm_path if bgm_path.exists() else None,
                            voice_duration_us)
    _patch_video_materials(draft, image_paths)
    _patch_text_segments(draft, srt_segments)
    _patch_main_track_segments(draft, image_paths, voice_duration_us)
    _patch_audio_segments(draft, voice_duration_us)
    _patch_top_level_duration(draft, voice_duration_us)

    draft_dir = ws / "draft"
    if draft_dir.exists():
        shutil.rmtree(draft_dir)
    draft_dir.mkdir(parents=True)
    (draft_dir / "draft_content.json").write_text(
        json.dumps(draft, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )
    _write_meta_info(draft_dir, video_id)
    click.echo(f"Built draft -> {draft_dir}")
    return draft_dir


@click.command()
@click.option("--id", "video_id", default="poc_001", show_default=True)
def main(video_id: str):
    build(video_id)


if __name__ == "__main__":
    main()
