# 3pro Morning Brief

삼프로TV 아침 방송 중 `월스트리트 모닝브리핑` 구간을 자동으로 정리해 텔레그램으로 보내는 개인용 자동화 프로젝트입니다.

## 목표

- 평일 오전 6:00-7:20 KST 구간을 대상으로 처리
- 자막을 우선 사용하고, 이후 화면 캡처/OCR 정보를 보강
- 핵심 요약, 상세 브리핑, 언급 종목 리스트 생성
- OpenAI TTS로 음성 브리핑 생성
- 텔레그램 개인 채팅으로 전송

## 현재 MVP 흐름

1. 삼프로TV 동영상 탭에서 당일 코너별 아카이브를 찾습니다.
2. `[월가 뉴스레터]`, `[글로벌 인터뷰]` 영상을 우선 수집합니다.
3. YouTube 자막 또는 자동 자막을 가져옵니다.
4. OpenAI로 요약과 종목 리스트를 생성합니다.
5. OpenAI TTS로 MP3 브리핑을 만듭니다.
6. 텔레그램으로 결과를 보냅니다.

라이브 DVR 수집은 다음 단계입니다. 라이브에서 6:00-7:20 구간을 얻지 못하면, 같은 날 올라오는 코너별 아카이브로 대체하는 구조입니다.

## 로컬 실행

```powershell
pip install -r requirements.txt
copy .env.example .env
python -m src.sampro_brief.cli --date 2026-06-19 --find-clipped-archives
```

OpenAI 분석과 음성 생성까지 실행하려면 `.env`에 `OPENAI_API_KEY`를 넣고 실행합니다.

```powershell
python -m src.sampro_brief.cli --date 2026-06-19 --collect-archive-transcripts --analyze-openai --create-tts
```

텔레그램 전송까지 하려면 `.env`에 `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`를 넣고 실행합니다.

```powershell
python -m src.sampro_brief.cli --date 2026-06-19 --collect-archive-transcripts --analyze-openai --create-tts --send-telegram
```

## GitHub Actions 설정

Repository Settings > Secrets and variables > Actions 에서 아래 값을 등록합니다.

Secrets:

- `OPENAI_API_KEY`
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`

Variables, 선택:

- `OPENAI_TEXT_MODEL`
- `OPENAI_TTS_MODEL`
- `OPENAI_TTS_VOICE`

처음에는 Actions를 수동 실행으로 테스트한 뒤 스케줄을 켜는 것을 권장합니다.

## 보안 메모

API 키와 텔레그램 토큰은 절대 GitHub에 올리지 않습니다. 이미 대화나 다른 장소에 노출된 키는 운영 전 재발급하는 것이 안전합니다.
