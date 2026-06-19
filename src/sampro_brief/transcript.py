from __future__ import annotations

import json
import re
import urllib.request
from html import unescape
from pathlib import Path
from urllib.parse import parse_qs, urlparse

PREFERRED_LANGS = ("ko", "ko-orig", "en")
PREFERRED_EXTS = ("vtt", "json3", "srv3", "ttml")


def collect_transcript(video_url: str, output_dir: Path, name: str) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"{name}.txt"

    text = fetch_with_transcript_api(video_url)
    if not text:
        text = fetch_with_ytdlp(video_url)

    if not text.strip():
        raise RuntimeError(f"No subtitle found: {video_url}")

    path.write_text(text, encoding="utf-8")
    return path


def video_id_from_url(video_url: str) -> str:
    parsed = urlparse(video_url)
    if parsed.netloc.endswith("youtu.be"):
        return parsed.path.strip("/")
    query_id = parse_qs(parsed.query).get("v")
    if query_id:
        return query_id[0]
    if "/watch/" in parsed.path:
        return parsed.path.rsplit("/", 1)[-1]
    return parsed.path.strip("/").rsplit("/", 1)[-1]


def fetch_with_transcript_api(video_url: str) -> str:
    video_id = video_id_from_url(video_url)
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
    except ImportError:
        return ""

    api = YouTubeTranscriptApi()
    for languages in (("ko",), ("ko-orig",), ("ko", "ko-orig"), ("en",), PREFERRED_LANGS):
        try:
            return transcript_items_to_text(api.fetch(video_id, languages=languages))
        except Exception:
            continue
    return ""


def transcript_items_to_text(items) -> str:
    lines: list[str] = []
    for item in items:
        text = ""
        if isinstance(item, dict):
            text = item.get("text", "")
        else:
            text = getattr(item, "text", "")
        text = normalize(text)
        if text:
            lines.append(text)
    return dedupe(lines)


def fetch_with_ytdlp(video_url: str) -> str:
    try:
        from yt_dlp import YoutubeDL

        with YoutubeDL({"quiet": True, "skip_download": True}) as ydl:
            info = ydl.extract_info(video_url, download=False)

        subtitle = choose_subtitle(info)
        if not subtitle:
            return ""

        raw = fetch_text(subtitle["url"])
        return clean_subtitle(raw, subtitle["ext"])
    except Exception:
        return ""


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
    return re.sub(r"\s+", " ", unescape(line).replace("\n", " ")).strip()


def dedupe(lines: list[str]) -> str:
    out = []
    prev = None
    for line in lines:
        if line != prev:
            out.append(line)
        prev = line
    return "\n".join(out) + ("\n" if out else "")
