from __future__ import annotations

from dataclasses import dataclass
from datetime import date

ARCHIVE_PART_KEYWORDS = {
    "wall_street_newsletter": ("[월가의 뉴스레터]", "[월가 뉴스레터]", "월가 뉴스레터"),
    "global_interview": ("[글로벌 인터뷰]", "글로벌 인터뷰"),
}


@dataclass(frozen=True)
class VideoCandidate:
    title: str
    url: str
    upload_date: str | None


def list_channel_videos(videos_url: str, limit: int = 30) -> list[VideoCandidate]:
    from yt_dlp import YoutubeDL

    with YoutubeDL({"quiet": True, "extract_flat": True, "playlistend": limit, "skip_download": True}) as ydl:
        data = ydl.extract_info(videos_url, download=False)

    candidates: list[VideoCandidate] = []
    for entry in data.get("entries") or []:
        title = entry.get("title") or ""
        video_id = entry.get("id")
        url = entry.get("webpage_url") or (f"https://www.youtube.com/watch?v={video_id}" if video_id else "")
        if title and url:
            candidates.append(VideoCandidate(title=title, url=url, upload_date=entry.get("upload_date")))
    return candidates


def find_clipped_archives(target_date: date, videos_url: str = "https://www.youtube.com/@3protv/videos") -> dict[str, VideoCandidate]:
    candidates = list_channel_videos(videos_url)
    selected: dict[str, VideoCandidate] = {}
    ymd = target_date.strftime("%Y%m%d")

    for part_name, keywords in ARCHIVE_PART_KEYWORDS.items():
        matches = [
            candidate
            for candidate in candidates
            if candidate.upload_date == ymd and any(keyword in candidate.title for keyword in keywords)
        ]
        if matches:
            selected[part_name] = matches[0]

    missing = sorted(set(ARCHIVE_PART_KEYWORDS) - set(selected))
    if missing:
        missing_text = ", ".join(missing)
        raise RuntimeError(f"Same-day archive video not found yet for {target_date.isoformat()}: {missing_text}")

    return selected
