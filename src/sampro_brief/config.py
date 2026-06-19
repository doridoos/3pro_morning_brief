from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover
    load_dotenv = None


@dataclass(frozen=True)
class Settings:
    openai_api_key: str | None
    openai_text_model: str
    openai_tts_model: str
    openai_tts_voice: str
    telegram_bot_token: str | None
    telegram_chat_id: str | None
    output_root: Path


def load_settings() -> Settings:
    if load_dotenv:
        load_dotenv()
    return Settings(
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        openai_text_model=os.getenv("OPENAI_TEXT_MODEL", "gpt-4.1-mini"),
        openai_tts_model=os.getenv("OPENAI_TTS_MODEL", "gpt-4o-mini-tts"),
        openai_tts_voice=os.getenv("OPENAI_TTS_VOICE", "alloy"),
        telegram_bot_token=os.getenv("TELEGRAM_BOT_TOKEN"),
        telegram_chat_id=os.getenv("TELEGRAM_CHAT_ID"),
        output_root=Path(os.getenv("OUTPUT_ROOT", "briefings")),
    )
