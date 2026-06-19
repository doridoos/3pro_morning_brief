from __future__ import annotations

import json
from pathlib import Path


def analyze_with_openai(transcript_text: str, output_dir: Path, model: str) -> dict:
    from openai import OpenAI

    client = OpenAI()
    trimmed = transcript_text[:60000]
    prompt = f"""
아래는 삼프로TV 아침 방송 자막입니다. 한국어로 투자 브리핑을 작성하세요.

반드시 JSON만 반환하세요.
형식:
{{
  "core_summary": ["5줄 이내 핵심 요약"],
  "detailed_briefing": "상세 정리본",
  "tts_script": "5분 이내 음성 브리핑 원고",
  "stocks": {{
    "korea": [{{"name": "종목명", "context": "언급 맥락", "source": "speech"}}],
    "us": [{{"name": "종목명", "context": "언급 맥락", "source": "speech"}}],
    "review": [{{"name": "분류 애매한 이름", "context": "맥락", "source": "speech"}}]
  }}
}}

자막:
{trimmed}
"""
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
    )
    data = json.loads(response.choices[0].message.content or "{}")
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "openai_analysis.json").write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return data


def render_markdown(data: dict, output_path: Path) -> None:
    lines = ["# 삼프로 아침 브리핑", "", "## 핵심 요약"]
    for item in data.get("core_summary", []):
        lines.append(f"- {item}")
    lines += ["", "## 상세 정리", data.get("detailed_briefing", ""), "", "## 언급 종목"]
    stocks = data.get("stocks", {})
    for label, key in (("국내", "korea"), ("미국", "us"), ("검토", "review")):
        lines += ["", f"### {label}"]
        for item in stocks.get(key, []):
            lines.append(f"- {item.get('name')}: {item.get('context')} ({item.get('source', 'speech')})")
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
