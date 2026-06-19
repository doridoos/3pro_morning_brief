from __future__ import annotations

from pathlib import Path


def create_openai_tts(text: str, output_path: Path, model: str, voice: str) -> None:
    from openai import OpenAI

    output_path.parent.mkdir(parents=True, exist_ok=True)
    client = OpenAI()
    response = client.audio.speech.create(model=model, voice=voice, input=text)
    response.write_to_file(output_path)
