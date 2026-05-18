"""Synthesize voice-over from script.txt using Microsoft Edge-TTS (free)."""
from __future__ import annotations

import asyncio

import click
import edge_tts

from _common import load_settings, workspace_dir


async def _tts(text: str, voice: str, rate: str, volume: str, out_path: str) -> None:
    comm = edge_tts.Communicate(text, voice=voice, rate=rate, volume=volume)
    await comm.save(out_path)


@click.command()
@click.option("--id", "video_id", default="poc_001", show_default=True)
def main(video_id: str):
    cfg = load_settings()["voice"]
    ws = workspace_dir(video_id)

    script_path = ws / "script.txt"
    if not script_path.exists():
        raise click.ClickException("script.txt missing; run gen_script first")
    text = script_path.read_text(encoding="utf-8").strip()
    if not text:
        raise click.ClickException("script.txt is empty")

    out = ws / "voice.mp3"
    asyncio.run(_tts(text, cfg["voice_id"], cfg["rate"], cfg["volume"], str(out)))
    click.echo(f"Wrote {out} ({out.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
