from __future__ import annotations

import json
import re
import urllib.request
from html import unescape
from pathlib import Path

PREFERRED_LANGS = ("ko", "ko-orig", "en")
PREFERRED_EXTS = ("vtt", "json3", "srv3", "ttml")


def collect_transcript(video_url: str, output_dir: Path, name: str) -> Path:
    from yt_dlp import YoutubeDL

    with YoutubeDL({"quiet": True, "skip_download": True}) as ydl:
        info = ydl.extract_info(video_url, download=False)

    subtitle = choose_subtitle(info)
    if not subtitle:
        raise RuntimeError(f"No subtitle found: {video_url}")

    output_dir.mkdir(parents=True, exist_ok=True)
    raw = fetch_text(subtitle["url"])
    text = clean_subtitle(raw, subtitle["ext"])
    path = output_dir / f"{name}.txt"
    path.write_text(text, encoding="utf-8")
    return path


def choose_subtitle(info: dict) -> dict | None:
    for source in (info.get("subtitles") or {}, info.get("automatic_captions") or {}):
        for lang in PREFERRED_LANGS:
            options = source.get(lang) or []
            for ext in PREFERRED_EXTS:
                for option in options:
                    if option.get("ext") == ext and option.get("url"):
                        return option
    return None


def fetch_text(url: str) -> str:
    with urllib.request.urlopen(url, timeout=60) as response:
        return response.read().decode("utf-8", errors="replace")


def clean_subtitle(raw: str, ext: str) -> str:
    if ext == "json3":
        data = json.loads(raw)
        lines = []
        for event in data.get("events", []):
            line = "".join(seg.get("utf8", "") for seg in event.get("segs", [])).strip()
            if line:
                lines.append(normalize(line))
        return dedupe(lines)

    lines = []
    for raw_line in raw.splitlines():
        line = raw_line.strip()
        if not line or "-->" in line or line.startswith(("WEBVTT", "Kind:", "Language:", "NOTE")):
            continue
        if re.fullmatch(r"\d+", line):
            continue
        line = normalize(re.sub(r"<[^>]+>", "", line))
        if line:
            lines.append(line)
    return dedupe(lines)


def normalize(line: str) -> str:
    return re.sub(r"\s+", " ", unescape(line)).strip()


def dedupe(lines: list[str]) -> str:
    out = []
    prev = None
    for line in lines:
        if line != prev:
            out.append(line)
        prev = line
    return "\n".join(out) + ("\n" if out else "")
