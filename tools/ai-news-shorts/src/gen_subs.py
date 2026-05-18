"""Transcribe voice.mp3 to SRT subtitles with faster-whisper (runs locally)."""
from __future__ import annotations

from datetime import timedelta

import click
from faster_whisper import WhisperModel

from _common import load_settings, workspace_dir


def _fmt_ts(seconds: float) -> str:
    td = timedelta(seconds=seconds)
    total_ms = int(td.total_seconds() * 1000)
    h, rem = divmod(total_ms, 3600_000)
    m, rem = divmod(rem, 60_000)
    s, ms = divmod(rem, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def transcribe(mp3_path: str, model_name: str, device: str, compute_type: str,
               language: str | None) -> list[tuple[float, float, str]]:
    model = WhisperModel(model_name, device=device, compute_type=compute_type)
    segments, _info = model.transcribe(
        mp3_path,
        language=language,
        vad_filter=True,
        word_timestamps=False,
    )
    return [(seg.start, seg.end, seg.text.strip()) for seg in segments]


def to_srt(segments: list[tuple[float, float, str]]) -> str:
    lines = []
    for i, (start, end, text) in enumerate(segments, 1):
        lines.append(str(i))
        lines.append(f"{_fmt_ts(start)} --> {_fmt_ts(end)}")
        lines.append(text)
        lines.append("")
    return "\n".join(lines)


@click.command()
@click.option("--id", "video_id", default="poc_001", show_default=True)
def main(video_id: str):
    cfg = load_settings()["whisper"]
    ws = workspace_dir(video_id)

    mp3 = ws / "voice.mp3"
    if not mp3.exists():
        raise click.ClickException("voice.mp3 missing; run gen_voice first")

    click.echo(f"Transcribing {mp3} with model={cfg['model']} device={cfg['device']}...")
    segs = transcribe(
        str(mp3),
        cfg["model"],
        cfg["device"],
        cfg["compute_type"],
        cfg["language"],
    )
    srt = to_srt(segs)
    out = ws / "subs.srt"
    out.write_text(srt, encoding="utf-8")
    click.echo(f"Wrote {len(segs)} segments -> {out}")


if __name__ == "__main__":
    main()
