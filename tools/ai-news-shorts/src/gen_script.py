"""Turn a chosen news item into a 60-second short-video script."""
from __future__ import annotations

import json

import click
from anthropic import Anthropic

from _common import load_env, load_settings, require_env, workspace_dir


def build_prompt(item: dict, target_chars: int) -> str:
    return (
        f"以下是一則 AI 新聞，請寫一支 60 秒短影音的旁白稿。\n\n"
        f"標題：{item['title']}\n"
        f"來源：{item['source']}\n"
        f"連結：{item['url']}\n\n"
        f"要求：\n"
        f"- 總字數約 {target_chars} 字中文（英文術語可保留）\n"
        f"- 結構：3 秒鉤子 → 主題介紹 → 3 個重點 → 行動呼籲\n"
        f"- 口語化，適合配音\n"
        f"- 不要 markdown、不要列點符號、不要舞台指示\n"
        f"- 直接輸出旁白文字\n"
    )


def call_claude(prompt: str, system: str, model: str) -> str:
    client = Anthropic(api_key=require_env("ANTHROPIC_API_KEY"))
    resp = client.messages.create(
        model=model,
        max_tokens=1024,
        system=system,
        messages=[{"role": "user", "content": prompt}],
    )
    parts = [b.text for b in resp.content if getattr(b, "type", None) == "text"]
    return "\n".join(parts).strip()


@click.command()
@click.option("--id", "video_id", default="poc_001", show_default=True)
@click.option("--pick", default=0, show_default=True, help="Index in news.json to use")
def main(video_id: str, pick: int):
    load_env()
    cfg = load_settings()
    ws = workspace_dir(video_id)

    news = json.loads((ws / "news.json").read_text(encoding="utf-8"))
    if not news:
        raise click.ClickException("news.json is empty; run fetch_news first")
    item = news[pick]

    prompt = build_prompt(item, cfg["script"]["target_chars"])
    text = call_claude(prompt, cfg["script"]["system"], cfg["script"]["model"])

    out = ws / "script.txt"
    out.write_text(text, encoding="utf-8")
    click.echo(f"Wrote {len(text)} chars -> {out}")
    click.echo("---")
    click.echo(text)


if __name__ == "__main__":
    main()
