"""Fetch trending AI news from HN Algolia and tech RSS feeds, then score."""
from __future__ import annotations

import json
import math
import time
from datetime import datetime, timezone

import click
import feedparser
import requests

from _common import load_settings, workspace_dir

HN_URL = "https://hn.algolia.com/api/v1/search"
RSS_FEEDS = [
    "https://techcrunch.com/category/artificial-intelligence/feed/",
    "https://www.producthunt.com/feed?category=artificial-intelligence",
    "https://feeds.arstechnica.com/arstechnica/index",
]


def fetch_hn(keywords: list[str]) -> list[dict]:
    """Pull recent HN front-page stories matching any keyword."""
    out = []
    for kw in keywords:
        resp = requests.get(
            HN_URL,
            params={"query": kw, "tags": "story", "hitsPerPage": 30},
            timeout=15,
        )
        resp.raise_for_status()
        for hit in resp.json().get("hits", []):
            out.append({
                "source": "hn",
                "title": hit.get("title") or "",
                "url": hit.get("url") or f"https://news.ycombinator.com/item?id={hit.get('objectID')}",
                "points": hit.get("points") or 0,
                "comments": hit.get("num_comments") or 0,
                "created_at": hit.get("created_at"),
                "keyword": kw,
            })
    # dedupe by URL
    seen = set()
    deduped = []
    for item in out:
        if item["url"] in seen:
            continue
        seen.add(item["url"])
        deduped.append(item)
    return deduped


def fetch_rss(feeds: list[str], keywords: list[str]) -> list[dict]:
    out = []
    lowered = [k.lower() for k in keywords]
    for url in feeds:
        try:
            feed = feedparser.parse(url)
        except Exception:
            continue
        for entry in feed.entries[:30]:
            title = entry.get("title", "")
            if not any(k in title.lower() for k in lowered):
                continue
            out.append({
                "source": "rss",
                "title": title,
                "url": entry.get("link", ""),
                "points": 0,
                "comments": 0,
                "created_at": entry.get("published") or entry.get("updated") or "",
                "keyword": "",
            })
    return out


def _age_hours(created_at: str) -> float:
    if not created_at:
        return 1e6
    for fmt in ("%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%dT%H:%M:%SZ", "%a, %d %b %Y %H:%M:%S %z"):
        try:
            dt = datetime.strptime(created_at, fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return (datetime.now(timezone.utc) - dt).total_seconds() / 3600
        except ValueError:
            continue
    return 1e6


def score(item: dict, cfg: dict) -> float:
    s = cfg["scoring"]
    age = _age_hours(item.get("created_at", ""))
    velocity = item["points"] / max(age, 1)
    age_decay = math.exp(-age / 48)
    return (
        item["points"] * s["upvote_weight"]
        + item["comments"] * s["comment_weight"]
        + velocity * 10 * s["velocity_weight"]
        + age_decay * 100 * s["age_decay_weight"]
    )


def top_n(items: list[dict], cfg: dict, n: int = 10) -> list[dict]:
    s = cfg["scoring"]
    filtered = []
    for it in items:
        if it["source"] == "hn":
            if it["points"] < s["min_score"] or it["comments"] < s["min_comments"]:
                continue
        it["score"] = score(it, cfg)
        filtered.append(it)
    filtered.sort(key=lambda x: x["score"], reverse=True)
    return filtered[:n]


@click.command()
@click.option("--id", "video_id", default="poc_001", show_default=True)
@click.option("--n", default=10, show_default=True, help="Top N candidates to save")
def main(video_id: str, n: int):
    cfg = load_settings()
    keywords = cfg["scoring"]["keywords"]
    click.echo(f"Fetching HN for {len(keywords)} keywords...")
    hn = fetch_hn(keywords)
    click.echo(f"Fetching RSS feeds...")
    rss = fetch_rss(RSS_FEEDS, keywords)
    all_items = hn + rss
    click.echo(f"Got {len(all_items)} raw items; scoring...")
    picks = top_n(all_items, cfg, n=n)

    out_path = workspace_dir(video_id) / "news.json"
    out_path.write_text(
        json.dumps(picks, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    click.echo(f"Wrote {len(picks)} candidates -> {out_path}")
    for i, p in enumerate(picks[:5]):
        click.echo(f"  [{i}] score={p['score']:.1f} | {p['title'][:80]}")


if __name__ == "__main__":
    main()
