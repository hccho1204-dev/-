# 🎬 Motion Studio — Claude로 만드는 모션그래픽 영상

영상 생성 AI 없이, **Claude가 코드(HTML)로 모션그래픽을 만들고 → MP4 영상으로 저장**하는 프로젝트입니다.
Claude 구독만 있으면 추가 비용이 없습니다. (나레이션·이미지는 무료 AI 도구 활용)

## 📁 폴더 구성
| 폴더/파일 | 역할 (쉽게 말하면) |
|---|---|
| `engine/motion.js` | 애니메이션 엔진 — "몇 초에 무엇이 어디 있는지" 계산하는 두뇌 |
| `render.js` | 녹화기 — HTML을 한 프레임씩 찍어서 MP4로 저장 |
| `projects/` | 영상 하나당 폴더 하나 (`index.html` = 영상 설계도) |
| `prompts/README.md` | **Claude에게 복붙할 프롬프트 6종** (영상에서 소개한 방법 전부) |
| `output/` | 완성된 MP4 영상 |

## 🎞 들어있는 예제
| 예제 | 방법 | 결과 |
|---|---|---|
| `01-ppt-evolution` | ① 대사+시간만 주기 (텍스트 없는 모션, 11초) | `output/01-ppt-evolution.mp4` |
| `02-bless-ad` | ⑤ 광고 만들기 (15초, 가로+세로) | `output/02-bless-ad.mp4`, `output/02-bless-ad-vertical.mp4` |

## ▶ 사용법

### 1. 미리보기 (설치 필요 없음)
`projects/01-ppt-evolution/index.html` 파일을 **크롬으로 더블클릭** → 바로 재생됩니다.
- 스페이스바: 재생/정지 · ←/→: 0.5초 이동 · 하단 바: 원하는 시간으로 이동
- 세로로 보기: 주소 끝에 `?w=1080&h=1920` 붙이기

### 2. MP4로 저장 (처음 한 번만 설치)
1. [Node.js](https://nodejs.org) 설치 (LTS 버전)
2. [ffmpeg](https://ffmpeg.org/download.html) 설치 (맥: `brew install ffmpeg` / 윈도우: `winget install ffmpeg`)
3. 터미널에서 이 폴더로 이동 후:
```bash
npm install
npx playwright install chromium
```
4. 렌더링:
```bash
node render.js projects/01-ppt-evolution/index.html                 # 가로 MP4
node render.js projects/02-bless-ad/index.html --vertical            # 세로(릴스/쇼츠) MP4
node render.js projects/02-bless-ad/index.html --audio voice.mp3     # 나레이션 합치기
node render.js projects/02-bless-ad/index.html --from 6 --to 11      # 일부 구간만 빠르게 확인
```

### 3. 새 영상 만들기 (Claude에게 시키기)
1. `prompts/README.md`에서 원하는 방법(①~⑥) 프롬프트 복사
2. 내용만 바꿔서 Claude Code에 붙여넣기 (Opus 5.5 · 사고 수준 높음 이상)
3. Claude가 `projects/새폴더/index.html` 만들고 MP4까지 렌더링해줌
4. 마음에 안 드는 부분은 "5~8초 구간을 더 빠르게" 식으로 수정 요청

## 💡 퀄리티를 올리는 4가지 원칙 (영상 핵심 요약)
1. **좋은 레퍼런스 영상을 첨부하라** — 글보다 영상 1개가 10배 효과적
2. **시간(초)을 알려줘라** — 대사·나레이션·가사에 타임스탬프를 붙이면 싱크가 정확해짐
3. **사고 수준은 높음 이상** — 낮으면 모션이 단조로워짐
4. **화면으로 보여줄 수 있는 단어를 써라** — "회전·확대·분할·찢어짐" 같은 동작 단어
