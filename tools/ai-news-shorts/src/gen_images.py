"""Fetch 3 portrait images from Unsplash for the video.

For PoC simplicity, this queries Unsplash with keywords derived from the news title.
For higher quality, replace returned files with manual screenshots from the AI tool's
website (just save 01.jpg, 02.jpg, 03.jpg into workspace/<id>/images/ before running
build_draft.py).
"""
from __future__ import annotations

import json

import click
import requests

from _common import load_env, require_env, workspace_dir

UNSPLASH_URL = "https://api.unsplash.com/search/photos"


def unsplash_search(query: str, per_page: int = 3) -> list[str]:
    key = require_env("UNSPLASH_ACCESS_KEY")
    resp = requests.get(
        UNSPLASH_URL,
        params={
            "query": query,
            "per_page": per_page,
            "orientation": "portrait",
            "content_filter": "high",
        },
        headers={"Authorization": f"Client-ID {key}"},
        timeout=15,
    )
    resp.raise_for_status()
    return [r["urls"]["regular"] for r in resp.json().get("results", [])]


def download(url: str, dest: str) -> None:
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    with open(dest, "wb") as f:
        f.write(r.content)


@click.command()
@click.option("--id", "video_id", default="poc_001", show_default=True)
@click.option("--query", default=None, help="Override Unsplash query; defaults to news title")
@click.option("--count", default=3, show_default=True)
def main(video_id: str, query: str | None, count: int):
    load_env()
    ws = workspace_dir(video_id)
    images_dir = ws / "images"
    images_dir.mkdir(exist_ok=True)

    if query is None:
        news = json.loads((ws / "news.json").read_text(encoding="utf-8"))
        if not news:
            raise click.ClickException("Need --query or a populated news.json")
        query = news[0]["title"]
        # Trim to keyword-ish phrase
        query = " ".join(query.split()[:6])

    click.echo(f"Searching Unsplash: {query!r}")
    urls = unsplash_search(query, per_page=count)
    if len(urls) < count:
        click.echo(f"WARNING: Unsplash returned only {len(urls)} images; "
                   "consider replacing with manual screenshots")

    for i, url in enumerate(urls, 1):
        dest = images_dir / f"{i:02d}.jpg"
        download(url, str(dest))
        click.echo(f"  -> {dest}")

    click.echo(f"Done. Replace any image with your own at {images_dir}\\NN.jpg")


if __name__ == "__main__":
    main()
