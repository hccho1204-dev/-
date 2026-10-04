# 프롬프트 템플릿 (클로드가 채워서 코덱스에 전달)

`{ }` 부분을 클로드가 원본 분석 결과로 채운다. 사용자에게 직접 쓰게 하지 않는다.

---

## 공통 머리말 (모든 컨셉 앞에 붙임)

```
Create a presentation-ready illustration for a Korean business meeting deck.
Subject: {주제 한 줄 — 예: semiconductor package layer structure from patent figure 3}
Components (keep every one, use these exact reference numbers as small leader-line labels):
{번호: 구성요소 — 예: 101: substrate, 102: die attach, 103: silicon die, 104: mold compound}
Process / order (if any): {순서 — 예: 1 substrate → 2 die attach → 3 wire bond → 4 mold}
Canvas: 16:9, 1920x1080, generous margins, subject centered, empty space at top-left for a title.
Text in image: only reference numbers and arrows. No paragraphs, no fake text, no watermark.
Accuracy over decoration: do not invent parts that are not in the source.
```

---

## A. 클레이 3D

```
Style: soft clay / plasticine 3D miniature, rounded edges, matte surface,
pastel palette ({메인색}, cream, sky blue, mint), soft studio light from top-left,
subtle contact shadows, light warm-gray seamless background.
Each component is a distinct clay color; same color for the same material.
Mood: friendly, easy to understand for non-experts.
Avoid: photorealism, harsh shadows, clutter, dark background.
```

## B. 글래스 다크

```
Style: dark glassmorphism 3D render, deep navy-to-black gradient background,
frosted translucent glass layers with thin glowing edges ({포인트색} accent, cyan, violet),
subtle reflections and depth of field, premium executive-report feel.
Layers slightly separated vertically so the internal structure is visible through the glass.
Avoid: neon overload, busy particles, lens flare, cartoon look.
```

## C. 아이소메트릭 분해도

```
Style: clean isometric (30°) exploded-view technical illustration,
each layer lifted upward in assembly order with dashed alignment lines,
numbered step arrows showing the build sequence 1 → {N},
flat colors with soft gradients, one color per material, white background,
thin dark outlines, optional thickness callouts ({단위 — 예: Å, mm}) on the side.
Avoid: perspective distortion, decorative backgrounds, shadows heavier than needed.
```

---

## 추가 컨셉 (요청 시)

| 이름 | 스타일 줄 |
|---|---|
| 보고서 문법 | `Monochrome corporate diagram, navy and gray only, flat 2.5D blocks, grid-aligned, report-ready` |
| 블루프린트 | `Blueprint style, white line art on deep blue grid paper, technical annotations as numbers only` |
| 미니멀 라인 | `Minimal line icon illustration, single stroke weight, one accent color, lots of white space` |
| 썸네일 에셋 | `Single isolated object on plain {배경색} background, centered, no text, consistent lighting for compositing` |

---

## 배치 생성 지시 (서브 에이전트용)

```
컨셉: {A/B/C}
장수: {n}장, 각 장은 카메라 각도·색 배치만 조금씩 다르게 (구성요소·번호는 동일)
저장: outputs/{프로젝트명}/{컨셉}/{01..n}.png
완료 후: 파일 경로 목록만 반환
```

---

## 수정 지시 (고른 1장만)

```
outputs/{프로젝트명}/{컨셉}/{번호}.png 를 기준으로,
변경: {예: 윗부분 몰드 층을 주황색(#F28C28)으로}
유지: 구도, 조명, 나머지 색, 번호 라벨 전부 그대로
```
