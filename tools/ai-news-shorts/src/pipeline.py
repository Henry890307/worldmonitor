"""Run the whole pipeline end-to-end for one video id.

Usage:
    python src\\pipeline.py --id poc_001
    python src\\pipeline.py --id poc_001 --skip fetch  # if you already have news.json
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import click

ROOT = Path(__file__).resolve().parent.parent
PY = sys.executable

STAGES = [
    ("fetch",   ["src/fetch_news.py"]),
    ("script",  ["src/gen_script.py", "--pick", "0"]),
    ("voice",   ["src/gen_voice.py"]),
    ("subs",    ["src/gen_subs.py"]),
    ("images",  ["src/gen_images.py"]),
    ("draft",   ["src/build_draft.py"]),
    ("deploy",  ["tools/deploy_draft.py"]),
]


def _run(stage: str, args: list[str], video_id: str) -> None:
    cmd = [PY] + args + ["--id", video_id]
    click.echo(f"\n=== [{stage}] {' '.join(cmd)} ===")
    rc = subprocess.call(cmd, cwd=str(ROOT))
    if rc != 0:
        raise click.ClickException(f"Stage {stage!r} failed (exit {rc})")


@click.command()
@click.option("--id", "video_id", default="poc_001", show_default=True)
@click.option("--skip", multiple=True,
              help="Stage names to skip (e.g. --skip fetch --skip script)")
@click.option("--only", multiple=True,
              help="Run only these stages (overrides --skip)")
def main(video_id: str, skip: tuple[str, ...], only: tuple[str, ...]):
    stages = STAGES
    if only:
        stages = [(n, a) for n, a in stages if n in only]
    else:
        stages = [(n, a) for n, a in stages if n not in skip]
    for name, args in stages:
        _run(name, args, video_id)
    click.echo("\nPipeline complete.")


if __name__ == "__main__":
    main()
