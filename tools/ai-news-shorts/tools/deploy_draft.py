"""Copy a built draft folder into CapCut's Projects directory.

Resolves %LocalAppData%-style paths and creates the destination if missing.
After running, the project appears in CapCut's project list automatically
(may need to close + reopen CapCut once).
"""
from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

import click

# Allow `import _common` from src/
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from _common import ROOT, load_settings, workspace_dir  # noqa: E402


def _expand(p: str) -> Path:
    return Path(os.path.expandvars(os.path.expanduser(p)))


@click.command()
@click.option("--id", "video_id", default="poc_001", show_default=True)
@click.option("--dest-name", default=None,
              help="Override destination folder name (default: video id)")
@click.option("--dry-run", is_flag=True)
def main(video_id: str, dest_name: str | None, dry_run: bool):
    cfg = load_settings()
    projects_dir = _expand(cfg["capcut"]["projects_dir"])

    if not projects_dir.parent.exists():
        raise click.ClickException(
            f"CapCut projects parent does not exist: {projects_dir.parent}\n"
            "Is CapCut installed? Edit config\\settings.yaml -> capcut.projects_dir"
        )
    projects_dir.mkdir(parents=True, exist_ok=True)

    src_draft = workspace_dir(video_id) / "draft"
    if not src_draft.exists():
        raise click.ClickException(f"Built draft not found: {src_draft}; run build_draft first")

    dest = projects_dir / (dest_name or video_id)
    click.echo(f"Source: {src_draft}")
    click.echo(f"Dest:   {dest}")

    if dry_run:
        click.echo("[dry-run] not copying")
        return

    if dest.exists():
        backup = dest.with_name(dest.name + ".bak")
        if backup.exists():
            shutil.rmtree(backup)
        click.echo(f"Existing project moved to: {backup}")
        dest.rename(backup)

    shutil.copytree(src_draft, dest)
    click.echo("Done. Open CapCut; if the project does not appear, restart CapCut.")


if __name__ == "__main__":
    main()
