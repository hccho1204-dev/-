# VIDEO_SPEC.json 형식

레퍼런스 영상을 **클로드가 읽을 수 있는 언어**로 바꾼 설계도. 이후 모든 제작은 이 파일만 기준으로 한다.
**빠짐없이** 적을수록 결과에 반영된다. 빠진 레이어는 클로드도 빠뜨린다.

예시 전체: `../templates/VIDEO_SPEC.example.json`

## 구조

| 칸 | 누가 채움 | 내용 |
|---|---|---|
| `measured` | 스크립트 (`decode_reference.py`) | 길이·해상도·fps·방향, 장면 수, 컷 길이(평균·중앙값·편차), 분당 컷, 밝기, 움직임, 대표색, 음량 |
| `style.tone_keywords` | 클로드 | 3~5개 단어. 예: `["흑백", "미니멀", "굵은 산세리프", "빠른 팝"]` |
| `style.typography` | 클로드 | 폰트 느낌, 굵기, 크기(화면 높이 대비 %), 위치, 색, 외곽선/그림자, 한 줄 최대 글자 수, 등장 방식 |
| `style.motion_language` | 클로드 | 기본 등장(팝/슬라이드/페이드/타이핑/마스크), easing(예: `cubic-bezier(.2,.9,.3,1.2)`), 속도감 |
| `style.transitions` | 클로드 | 기본 전환(바로 컷/이어지기/화이트 플래시…), 연결 방식(요소가 다음 장면으로 넘어가는지) |
| `style.graphics_inventory` | 클로드 | 쓰인 그래픽 종류 목록 + 몇 초마다 나오는지 |
| `style.sound` | 클로드 | 배경음악 분위기, 효과음 종류·위치 |
| `scenes[]` | 스크립트 + 클로드 | 장면별 시간·밝기·움직임·색(스크립트) + `layers`·`transition_out`·`notes`(클로드) |

## `scenes[].layers` 적는 법 (가장 중요)

화면을 **아래에서 위로** 쌓인 순서대로, 레이어 하나당 한 줄.

```json
{
  "z": 3,
  "type": "text",
  "content": "챕터 1",
  "role": "chapter_label",
  "box": {"x_pct": 8, "y_pct": 40, "w_pct": 84, "h_pct": 8},
  "style": {"font": "굵은 산세리프", "size_pct_of_height": 6.5, "color": "#FFFFFF", "stroke": "없음"},
  "in":  {"at": 0.20, "anim": "pop", "dur": 0.25, "easing": "overshoot"},
  "hold": 1.4,
  "out": {"at": 1.85, "anim": "slide-left", "dur": 0.2},
  "sfx": "pop"
}
```

| 필드 | 값 예 |
|---|---|
| `type` | `background` / `video` / `image` / `text` / `shape` / `chart` / `icon` / `logo` / `particle` / `mask` |
| `role` | `title` / `subtitle` / `caption` / `chapter_label` / `cta` / `number_highlight` / `keyword_chip` / `lower_third` … |
| `box` | 화면 대비 % (해상도 바뀌어도 그대로 쓰도록) |
| `in` / `out` | 장면 시작 기준 초, 애니메이션 이름, 길이, easing |
| `sfx` | 그 순간 효과음 (없으면 생략) |

## 채울 때 체크
1. `sheet.jpg`로 전체 흐름 → `scene_XX.jpg`로 장면마다 레이어 받아 적기
2. 움직임은 캡처만으로 모르면, 해당 구간을 0.1초 간격으로 더 뽑아 본다:
   `ffmpeg -ss <시작> -t 1 -i ref.mp4 -vf fps=10,scale=360:-2 work/refs/ref1/zoom_%02d.jpg`
3. 글자 크기는 **화면 높이 대비 %**로 (휴대폰에서 읽히려면 세로 영상 기준 3% 이상)
4. 레퍼런스의 **실제 문구·로고**는 그대로 베끼지 말고 `role`만 적는다 (스타일만 학습)
