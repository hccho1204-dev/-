# 야간 모드 — 자기 전에 걸어 두고 아침에 확인

## 준비 (처음 1번)

| # | 할 일 | 왜 |
|---|---|---|
| 1 | `doctor.sh` 전부 ✅ 확인 | 밤중에 설치 문제로 멈추지 않게 |
| 2 | 컴퓨터 **절전 끄기** (맥은 스크립트가 `caffeinate`로 자동 처리, 윈도우는 설정 → 전원 → 절전 "안 함") | 잠들면 작업도 멈춤 |
| 3 | 자주 쓰는 명령 **미리 허용** (`/permissions` 또는 `.claude/settings.json`에 `npx remotion`, `ffmpeg`, `python3` 등) | 혼자 도는 동안 권한 묻다가 멈추지 않게 |
| 4 | 노트북이면 충전기 연결 | |

## 매일 밤

1. 작업 파일 쓰기 — `templates/night-job.md`를 복사해 `night/jobs/01-xxx.md`, `02-xxx.md`…
   (말로 "오늘 밤 이 작업 3개 걸어 둬"라고 하면 클로드가 대신 써 준다)
2. 실행:
   ```bash
   bash .claude/skills/video-studio/scripts/night_queue.sh night/jobs 90
   ```
   - 두 번째 숫자 = 작업당 최대 시간(분). 넘으면 끊고 다음 작업으로.
   - 파일 이름 순서대로 실행 → 번호(01, 02…)로 순서를 정한다.
3. 아침: `night/report.md` 확인 → 성공한 작업은 `night/done/`으로 옮겨져 있다. 실패 작업은 `night/jobs/`에 남아 있으니 로그 보고 다시 걸면 된다.

## 예약 실행 (선택)
- 맥·리눅스: `crontab -e` → `0 1 * * * cd /작업폴더 && bash .claude/skills/video-studio/scripts/night_queue.sh night/jobs`
- 윈도우: 작업 스케줄러 → 새 작업 → 동작에 `bash ...night_queue.sh` (Git Bash 또는 WSL)
- Claude Code 클라우드 세션이면 "예약 작업"으로 매일 새벽 실행을 걸 수 있다.

## 안전 규칙
- 혼자 도는 동안 **공개 업로드는 기본 금지**. 작업 파일에 `upload: public`이 있을 때만.
- 기본값은 `out/upload/`에 파일·제목·설명·태그를 준비해 두기까지.
- 원본 파일은 절대 덮어쓰지 않는다 (결과는 항상 `work/`, `out/`에).
