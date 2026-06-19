from __future__ import annotations

import argparse
import json
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from .config import load_settings
from .openai_analyzer import analyze_with_openai, render_markdown
from .telegram import send_document, send_message
from .transcript import collect_transcript
from .tts import create_openai_tts
from .youtube_resolver import find_clipped_archives

KST = timezone(timedelta(hours=9))


def parse_date(value: str) -> date:
    if value == "today":
        return datetime.now(KST).date()
    return date.fromisoformat(value)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", default="today")
    parser.add_argument("--find-clipped-archives", action="store_true")
    parser.add_argument("--collect-archive-transcripts", action="store_true")
    parser.add_argument("--analyze-openai", action="store_true")
    parser.add_argument("--create-tts", action="store_true")
    parser.add_argument("--send-telegram", action="store_true")
    args = parser.parse_args()

    settings = load_settings()
    target_date = parse_date(args.date)
    output_dir = settings.output_root / target_date.isoformat()
    transcript_dir = output_dir / "transcripts"
    analysis_dir = output_dir / "analysis"
    output_dir.mkdir(parents=True, exist_ok=True)

    archives = find_clipped_archives(target_date)
    (output_dir / "archives.json").write_text(
        json.dumps({k: v.__dict__ for k, v in archives.items()}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    if args.find_clipped_archives:
        for name, video in archives.items():
            print(f"{name}: {video.title} - {video.url}")

    transcript_paths: list[Path] = []
    if args.collect_archive_transcripts:
        for name, video in archives.items():
            path = collect_transcript(video.url, transcript_dir, name)
            transcript_paths.append(path)
            print(f"saved transcript: {path}")

    combined_path = transcript_dir / "combined.txt"
    if transcript_paths:
        combined = []
        for path in transcript_paths:
            combined.append(f"## {path.stem}\n" + path.read_text(encoding="utf-8"))
        combined_path.write_text("\n\n".join(combined), encoding="utf-8")

    analysis = None
    if args.analyze_openai:
        if not settings.openai_api_key:
            raise RuntimeError("OPENAI_API_KEY is required")
        transcript_text = combined_path.read_text(encoding="utf-8")
        analysis = analyze_with_openai(transcript_text, analysis_dir, settings.openai_text_model)
        render_markdown(analysis, analysis_dir / "openai_briefing.md")
        print(f"saved analysis: {analysis_dir / 'openai_briefing.md'}")

    audio_path = analysis_dir / "openai_briefing.mp3"
    if args.create_tts:
        if analysis is None:
            analysis_path = analysis_dir / "openai_analysis.json"
            analysis = json.loads(analysis_path.read_text(encoding="utf-8"))
        script = analysis.get("tts_script") or analysis.get("detailed_briefing") or ""
        create_openai_tts(script, audio_path, settings.openai_tts_model, settings.openai_tts_voice)
        print(f"saved audio: {audio_path}")

    if args.send_telegram:
        if not settings.telegram_bot_token or not settings.telegram_chat_id:
            raise RuntimeError("Telegram settings are required")
        briefing_path = analysis_dir / "openai_briefing.md"
        text = f"삼프로 아침 브리핑 {target_date.isoformat()}\n"
        if briefing_path.exists():
            text += briefing_path.read_text(encoding="utf-8")[:2500]
        send_message(settings.telegram_bot_token, settings.telegram_chat_id, text)
        if briefing_path.exists():
            send_document(settings.telegram_bot_token, settings.telegram_chat_id, briefing_path, "상세 브리핑")
        if audio_path.exists():
            send_document(settings.telegram_bot_token, settings.telegram_chat_id, audio_path, "음성 브리핑")


if __name__ == "__main__":
    main()
