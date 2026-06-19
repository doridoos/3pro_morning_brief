from __future__ import annotations

import json
import mimetypes
import uuid
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


def send_message(bot_token: str, chat_id: str, text: str) -> None:
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    data = urlencode({"chat_id": chat_id, "text": text}).encode("utf-8")
    with urlopen(Request(url, data=data), timeout=30) as response:
        ensure_ok(response.read())


def send_document(bot_token: str, chat_id: str, file_path: Path, caption: str = "") -> None:
    boundary = f"----sampro-{uuid.uuid4().hex}"
    body = build_multipart(boundary, {"chat_id": chat_id, "caption": caption}, "document", file_path)
    request = Request(
        f"https://api.telegram.org/bot{bot_token}/sendDocument",
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
    )
    try:
        with urlopen(request, timeout=60) as response:
            ensure_ok(response.read())
    except HTTPError as exc:
        raise RuntimeError(exc.read().decode("utf-8", errors="replace")) from exc


def build_multipart(boundary: str, fields: dict[str, str], file_field: str, file_path: Path) -> bytes:
    parts: list[bytes] = []
    for name, value in fields.items():
        parts += [f"--{boundary}\r\n".encode(), f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode(), f"{value}\r\n".encode()]
    content_type = mimetypes.guess_type(file_path.name)[0] or "application/octet-stream"
    parts += [
        f"--{boundary}\r\n".encode(),
        f'Content-Disposition: form-data; name="{file_field}"; filename="{file_path.name}"\r\n'.encode(),
        f"Content-Type: {content_type}\r\n\r\n".encode(),
        file_path.read_bytes(),
        b"\r\n",
        f"--{boundary}--\r\n".encode(),
    ]
    return b"".join(parts)


def ensure_ok(raw: bytes) -> None:
    data = json.loads(raw.decode("utf-8"))
    if not data.get("ok"):
        raise RuntimeError(f"Telegram API error: {data}")
