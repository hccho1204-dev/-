---
name: motion-graphics
description: Claude만으로 모션그래픽 영상(MP4)을 만드는 스킬. motion-studio/ 프로젝트의 엔진(engine/motion.js)과 렌더러(render.js)로 HTML 모션그래픽을 만들고 MP4로 렌더링한다. 사용자가 "모션그래픽", "모션 그래픽 만들어줘", "영상 만들어줘", "광고 영상", "쇼츠/릴스 영상", "대사에 맞춰 화면", "나레이션 영상", "음악에 맞춰 영상", "레퍼런스 영상처럼", "웹사이트로 광고 영상", "세로 버전으로" 등을 언급하면 반드시 활성화한다.
---

# motion-graphics

`motion-studio/` 프로젝트로 모션그래픽 영상을 기획 → 제작 → MP4 렌더링 → 자체 검수까지 끝낸다.

## 6가지 제작 방식 (요청 유형 판별)
| 유형 | 입력 | 핵심 |
|---|---|---|
| ① 대사+시간 | 대본 + 총 길이(초) | 텍스트 없이 도형·아이콘으로 대사 의미 표현, 문장 단위로 장면 전환 |
| ② 레퍼런스 | 레퍼런스 영상 + 바꿀 주제 | 먼저 레퍼런스를 프레임 단위로 분석(ffmpeg로 0.5초 간격 캡처) → 장면표 작성 → 주제 대입 |
| ③ 음악 싱크 | 음악 파일 + 가사 | BPM 분석, 비트마다 펀치(스케일/플래시), 가사 단어 뜻대로 동작(spin=회전, zoom=확대) |
| ④ 나레이션+이미지 | 음성 + 이미지 N장 | 문장 타임스탬프에 이미지 배치, 스타일(페이퍼컷/복스 레트로 등) 적용 |
| ⑤ 광고 | 서비스 설명 + 나레이션 | 문제 제기 → 공감 → 해결 3가지 → 브랜드 + CTA. 가로·세로 둘 다 렌더 |
| ⑥ 웹사이트 광고 | URL + 컨셉 | 사이트에서 핵심 메시지 3개·브랜드 컬러 추출 후 제작 |

복붙용 프롬프트 원본: `motion-studio/prompts/README.md`

## 제작 절차
1. **타임라인 표 먼저**: 시간(초) | 대사/가사 | 화면 연출 | 이징 — 표로 정리해 사용자에게 보여주고 바로 제작 진행 (질문으로 멈추지 않는다).
2. **파일 생성**: `motion-studio/projects/<번호-이름>/index.html`. 기존 예제 `01-ppt-evolution`, `02-bless-ad` 구조를 그대로 따른다.
   - `<div id="stage">` 안에 모든 요소, `<script src="../../engine/motion.js">` 로드
   - `Motion.start({ width, height, duration, setup(M), render(t, M) })`
3. **엔진 규칙 (필수)**
   - 모든 움직임은 `render(t)` 안에서 t로만 계산. CSS animation/transition, setTimeout, Math.random 금지 (렌더 시 프레임이 어긋남) → 난수는 `M.rand(seed)`
   - 도구: `M.prog(t, 시작, 끝, M.ease.outBack)` 0→1 진행률, `M.key(t, [[시간,값,'이징'],...])` 키프레임, `M.set(el, {x,y,s,r,o, ...css})`
   - 크기는 가로/세로 겸용: `--u: calc(min(var(--W), var(--H)) * 1px / 1080)` 단위 사용, `.portrait` 클래스·`M.portrait`로 배치 분기
   - 한글 폰트: Pretendard CDN + `'Noto Sans KR','Apple SD Gothic Neo','Malgun Gothic','WenQuanYi Zen Hei'` 폴백
4. **렌더링**: `cd motion-studio && node render.js projects/<폴더>/index.html [--vertical] [--audio 파일]`
   - 전역 playwright만 있는 환경이면 `NODE_PATH=$(npm root -g)` 붙여 실행
5. **자체 검수 (생략 금지)**: 장면 전환 시점 프레임을 타일로 캡처해 직접 눈으로 확인
   ```bash
   ffmpeg -i output/x.mp4 -vf "select='not(mod(n\,30))',scale=480:-1,tile=4x3" -frames:v 1 sheet.png
   ```
   겹침·잘림·빈 화면·글자 넘침이 있으면 고치고 다시 렌더링.
6. **전달**: MP4 경로, 장면별 타임라인 표, 수정 요청 예시 3개를 함께 안내.

## 퀄리티 기준
- 장면당 최소 2단계 모션(등장 → 유지 중 미세 움직임 → 퇴장). 정지 화면 0.5초 이상 금지
- 등장은 `outBack`/`outExpo`, 장면 전환은 `inOutExpo` 위주로 탄력 있게
- 요소는 0.1~0.3초 간격 순차 등장(stagger)
- 색은 3~4색 팔레트로 제한, 배경에 은은한 움직임(그리드 흐름·빛 숨쉬기)
- 보험·금융 광고는 수익 보장, 과장 수치 등 단정 표현을 쓰지 않는다
