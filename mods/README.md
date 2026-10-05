# 클로드 코드 모드(Mod) 3종

클로드 코드 화면에 **나만의 표시창과 자동 동작**을 붙이는 "모드" 모음입니다.
영상에서 소개된 기능(토큰 웨더, 블라스트 레디어스, 학습 노트, 캐시 워치)을 바로 쓸 수 있게 만들었습니다.

| 모드 | 하는 일 | 화면 위치 | 영상 속 이름 |
| --- | --- | --- | --- |
| `cache-watch` | 캐시 남은 시간 · 컨텍스트 사용량(날씨로 표시) · 이번 세션 비용 | 입력창 바로 위 한 줄 | 캐시 워치 + 토큰 웨더 |
| `safe-guard` | 파일 삭제·강제 푸시 같은 위험 명령을 실행 직전에 멈추고 "정말 할까요?" 확인 | 확인 창 + 알림 | 블라스트 레디어스 |
| `study-notes` | AI가 파일을 고칠 때마다 "무엇을·왜 바꿨는지 + 오늘의 개념"을 쉬운 말로 정리 | 오른쪽 패널 (`/study-notes`) | 학습 노트 |

## 화면 예시

```
⏱ 캐시 58분 · 🧠 컨텍스트 42% ⛅ 구름 · 💰 $1.23  [ 숨기기 ]
> 여기에 프롬프트 입력
```

- 컨텍스트 날씨: 0~39% ☀️ 맑음 → 40~59% ⛅ 구름 → 60~79% 🌧️ 소나기 → 80% 이상 ⛈️ 폭풍
- 캐시: 마지막 응답 뒤 60분에서 1분씩 줄어듭니다. "만료"가 빨갛게 뜨면 다음 질문부터 비용이 더 듭니다.

## 설치 방법 (내 컴퓨터)

1. 이 저장소를 내 컴퓨터에 받습니다.
   ```bash
   git clone https://github.com/hccho1204-dev/-.git claude-mods
   ```
2. 한 번만 써 보려면, 그 폴더에서 이렇게 실행합니다.
   ```bash
   cd claude-mods
   claude --plugin-dir ./mods/cache-watch --plugin-dir ./mods/safe-guard --plugin-dir ./mods/study-notes
   ```
3. 항상 켜 두려면 `~/.claude/settings.json`에 아래를 추가합니다. (경로는 내 컴퓨터의 실제 위치로 바꾸세요. 맥/리눅스는 `:`로, 윈도우는 `;`로 구분)
   ```json
   {
     "env": {
       "CLAUDE_CODE_PLUGIN_DIRS": "~/claude-mods/mods/cache-watch:~/claude-mods/mods/safe-guard:~/claude-mods/mods/study-notes"
     }
   }
   ```
4. 클로드 코드를 다시 켜면 입력창 위에 캐시 줄이 보입니다. 학습 노트는 `/study-notes`로 엽니다.

## 참고

- `study-notes`는 노트를 쓸 때 AI를 한 번 더 부릅니다(대화 캐시를 재사용해 비용은 작은 편). 비용이 신경 쓰이면 이 모드만 빼고 쓰세요.
- `safe-guard`가 막는 명령 목록은 `mods/safe-guard/hooks/register.ts` 맨 위 `RISKY`에 있습니다. 원하는 명령을 추가할 수 있습니다.
- 각 모드 폴더에서 `claude plugin validate <폴더>`(검사), `claude plugin test <폴더>`(테스트)를 실행할 수 있습니다.
