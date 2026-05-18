"""Shared helpers for the AI News Shorts pipeline."""
from __future__ import annotations

import os
from pathlib import Path

import yaml
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = ROOT / "config" / "settings.yaml"


def load_settings() -> dict:
    with CONFIG_PATH.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_env() -> None:
    load_dotenv(ROOT / ".env")


def workspace_dir(video_id: str) -> Path:
    cfg = load_settings()
    p = ROOT / cfg["pipeline"]["workspace_root"] / video_id
    p.mkdir(parents=True, exist_ok=True)
    return p


def require_env(name: str) -> str:
    val = os.environ.get(name)
    if not val:
        raise RuntimeError(f"Missing environment variable: {name}")
    return val
