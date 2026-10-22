# HyperFrames 설치·사용 메모

HyperFrames = HeyGen이 공개한 **HTML 기반 영상 제작 도구**. 웹페이지 만들듯 그래픽을 짜면 영상으로 렌더해 준다.
막대 그래프·흐름도·키워드 칩·카드 같은 모션그래픽과 효과음 라이브러리를 쓸 수 있다.

## 설치 (대화창에 한 줄)

> 하이퍼프레임 스킬 설치해 줘

이 저장소에는 **이미 설치돼 있다** (`.claude/skills/hyperframes*`, `media-use`). 새 컴퓨터나 다른 프로젝트에 설치할 때만 아래를 쓴다.

| 방법 | 명령 |
|---|---|
| Claude Code 플러그인 (추천, 자동 업데이트) | `claude plugin marketplace add heygen-com/hyperframes` → `claude plugin install hyperframes@hyperframes` |
| 핵심 스킬만 설치 | `npx hyperframes skills update` |
| 고르면서 설치 | `npx skills add heygen-com/hyperframes` (Core Skills 그룹 선택) |

- 외부 프로그램 설치라서 **권한 검사에서 한 번 막힌다** → 권한 요청에서 **"허용"을 한 번** 눌러 준다.
- 공식 저장소: https://github.com/heygen-com/hyperframes (Apache 2.0)
- 필요한 것: Node.js 22 이상, ffmpeg
- ⚠️ HyperFrames에도 `motion-graphics`라는 스킬이 있다. 이 저장소의 기존 `motion-graphics`(톤카드 하네스)와 이름이 겹치므로 **HyperFrames 쪽 motion-graphics는 설치하지 않는다.**

## 설치된 스킬

| 스킬 | 이 편집 흐름에서 쓰는 곳 |
|---|---|
| `/hyperframes` | 시작점. 영상 작업 요청을 알맞은 스킬로 연결 |
| `/hyperframes-core` | 컷 영상 위에 그래픽을 얹는 합성 구조 |
| `/hyperframes-animation` | 팝 효과·차트 상승·칩 순차 등장 등 움직임 |
| `/hyperframes-keyframes` | 확대(펀치인)·줌·카메라 이동 |
| `/hyperframes-creative` | 색·폰트·스타일 변형 (예: 애플 키노트 느낌) |
| `/hyperframes-registry` | 막대 그래프·카드 등 기성 블록 약 400개 검색·설치 |
| `/hyperframes-audio` | 효과음·배경음 음량 조절, 말소리 위 덕킹 |
| `/media-use` | 효과음·배경음·아이콘 찾기, 받아쓰기·자막 |
| `/hyperframes-cli` | 미리보기·검사·렌더 명령 |
| `/hyperframes-studio` | 스튜디오에서 함께 수정할 때 |

## 사용 순서
1. `STYLE_GUIDE.md`의 "4. 모션그래픽" 기준으로 그래픽 종류·색·주기를 맞춘다.
2. `cut.mp4`의 자막 타이밍(cutlist.json)을 보고 그래픽 등장 시점을 정한다.
3. 그래픽은 HTML로 장면별로 만들고 `cut.mp4` 위에 합성해 렌더한다.
4. 등장 애니메이션 기본값은 **팝(scale 0→1.1→1, 약 0.25초)**.

## 효과음
- HyperFrames 안의 **효과음 라이브러리**를 쓴다 (따로 파일을 모아 둘 필요 없음).
- 그래픽 등장·칩 하나하나·컷 강조 순간에 0.2~0.5초짜리를 짧게.
- 음량은 말소리보다 확실히 작게 (예: -18dB 이하).

## 스타일 변형 (예: 애플 키노트 느낌)
- **컷·자막은 그대로**, 모션그래픽만 바꾼다.
- 애플 키노트 느낌 예: 검정/흰 배경, 얇고 큰 산세리프, 넉넉한 여백, 느린 페이드·부드러운 이동, 그라데이션 숫자.
- 결과는 `final_v2.mp4` 처럼 별도 파일로.
