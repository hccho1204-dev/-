# 설치 안내 (처음 1번)

## 가장 쉬운 방법
Claude Code 대화창에 이렇게 말한다:

> 영상 자동화 도구 점검하고 없는 것만 다 설치해 줘

→ 클로드가 `scripts/doctor.sh`로 점검 → `scripts/setup.sh`로 설치 → 다시 점검표를 보여 준다.
권한 요청이 뜨면 **"허용"**을 누른다 (외부 프로그램 설치라 정상).

## 준비물

| 항목 | 왜 필요? | 비고 |
|---|---|---|
| Claude Code | 모든 작업을 하는 AI | 영상 렌더는 토큰을 많이 쓴다. 넉넉한 상위 요금제 권장 |
| Node.js 22+ | 리모션·하이퍼프레임 실행 엔진 | nodejs.org → LTS 다운로드 |
| FFmpeg | 영상 자르기·붙이기·변환 | 맥 `brew install ffmpeg` / 윈도우 `winget install Gyan.FFmpeg` |
| Python 3.10+ | 오픈몬테이지·분석 스크립트 | python.org |
| git | 오픈몬테이지 내려받기 | git-scm.com |

## 3대 도구 설치 명령 (직접 할 때)

### 1. Remotion 스킬 — 영상을 코드로
```bash
npx skills add remotion-dev/skills
```
- 새 리모션 프로젝트: `npx create-video@latest` (만들 때 스킬 추가 여부를 물어보면 "예")
- 스킬 위치는 `.agents/skills` 또는 `.claude/skills` (버전마다 다름). `doctor.sh`가 둘 다 찾아 준다.
- 공식 문서: https://www.remotion.dev/docs/ai/skills
- 참고: Remotion은 개인·소규모 팀은 무료, 일정 규모 이상 회사는 유료 라이선스 (remotion.dev/license 확인)

### 2. HyperFrames 스킬 — HTML/CSS를 영상으로
```bash
npx skills add heygen-com/hyperframes --full-depth --yes
```
- `--full-depth`: 최신 버전을 바로 받음 (빼면 몇 시간 늦은 버전이 올 수 있음)
- Node.js 22 이상 + FFmpeg 필요

### 3. OpenMontage — 영상 제작 공장 (파이프라인 12종)
맥·리눅스:
```bash
git clone https://github.com/calesthio/OpenMontage.git
cd OpenMontage
make setup
```
윈도우 PowerShell:
```powershell
git clone https://github.com/calesthio/OpenMontage.git
cd OpenMontage
py -3 -m venv .venv; .\.venv\Scripts\Activate.ps1; python -m pip install -r requirements.txt; cd remotion-composer; npm install; cd ..; python -m pip install piper-tts; Copy-Item .env.example .env
```
- `.env`의 API 키는 **전부 선택**. 없어도 무료 음성(Piper)·무료 스톡으로 돌아간다.
- 쓸 때는 **OpenMontage 폴더를 Claude Code로 열고** 말로 시킨다 (폴더 안 CLAUDE.md가 안내함).
- 라이선스 AGPL-3.0: 만든 영상은 자유롭게 써도 되지만, 코드를 고쳐서 서비스로 배포할 땐 공개 의무가 있다.

## 막힐 때

| 증상 | 해결 |
|---|---|
| `npx: command not found` | Node.js 설치 후 터미널 새로 열기 |
| `ffmpeg not found` | FFmpeg 설치 후 터미널 새로 열기 (윈도우는 재부팅이 확실) |
| 윈도우 `npm install` 에서 `ERR_INVALID_ARG_TYPE` | `npx --yes npm install` 로 다시 |
| 윈도우 `.ps1 cannot be loaded` | PowerShell 관리자: `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` |
| 스킬 설치했는데 클로드가 모름 | Claude Code 재시작 |
| 한글 자막이 네모(□)로 나옴 | 한글 폰트(Pretendard, Noto Sans KR) 설치 후 코드에서 폰트 지정 |
| HyperFrames 렌더 시 `Chrome Headless Shell is required` | `npx hyperframes browser ensure` (setup.sh가 자동 실행) |
| 렌더 실패 `sub_timeline_script_failure ... gsap.min.js` | 외부 CDN이 막힌 환경(회사망·클라우드 세션). `npm i gsap` 후 HTML의 jsdelivr 주소를 로컬 `assets/vendor/gsap.min.js`로 바꾸면 해결 |
| HyperFrames 설치 후 내 `motion-graphics` 스킬이 바뀜 | 이름이 겹친 것. setup.sh가 자동 복구하고 HyperFrames 것은 `hyperframes-motion-graphics`로 둔다 |
| 명령이 바뀐 것 같음 | 기억 말고 각 공식 GitHub README를 읽고 따라 하기 |

## 토큰 아끼는 팁
- 설치 안내 PDF·문서는 **채팅에 첨부하지 말고 작업 폴더에 넣어 두고** "이 폴더 문서 확인해 줘"라고 한다.
- 긴 설명은 **마이크(음성 입력)**로 말해도 된다.
