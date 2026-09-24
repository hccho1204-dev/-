---
name: cardnews-plan
description: 인스타 카드뉴스 자동화 1단계-A(기획). 주제 하나를 받아 표지 카피·장별 헤드라인·본문·이미지 장면·인스타 캡션까지 9장 기획안을 만들고 세트 폴더(cardnews-automation/sets/날짜_주제/)에 plan.md·plan.json·caption.md로 저장한다. 사용자가 "카드뉴스 기획", "오늘 카드뉴스 주제", "카드뉴스 주제 추천", "기획안 짜줘", "/cardnews-plan", "채택" 등을 말하면 사용한다. 이미지 생성(cardnews-images)이나 미리캔버스 작업(cardnews-miricanvas)은 하지 않는다 — 세션 분리가 퀄리티의 핵심.
---

# cardnews-plan — 1단계-A: 기획 (머리 담당)

회사로 치면 **기획팀**이다. 글만 만든다. 이미지·디자인은 다른 세션이 한다.

## 시작 전에 반드시 읽을 파일
1. `cardnews-automation/config/brand.md` — 타깃, 톤, 금지어, 요일별 카테고리
2. `cardnews-automation/config/design-spec.md` — 장당 최대 글자수 (넘으면 디자인이 깨진다)
3. `cardnews-automation/memory/approved.md` — 내가 채택한 기획안들 (이 스타일을 따라간다)
4. `cardnews-automation/memory/topics-used.md` — 이미 다룬 주제 (겹치지 않게)

## 모드

### A. 주제가 없을 때 ("주제 추천해줘")
- 오늘 요일의 카테고리(brand.md 3번) 기준으로 주제 3개 제안.
- 각 주제: 제목 / 왜 지금 먹히는지 한 줄 / 표지 카피 예시.
- 사용자가 고르면 B로.
- 사용자가 "알아서"라고 하면 1번으로 바로 진행.

### B. 주제가 있을 때 → 기획안 작성
1. 세트 폴더 생성:
   ```
   python3 cardnews-automation/scripts/new_set.py "<주제>"
   ```
2. 아래 **9장 구조**로 기획. 자세한 공식은 `references/copy-formulas.md`.

| 장 | type | 역할 | 채울 칸 |
|---|---|---|---|
| 1 | cover | 0.5초 안에 멈추게 | label(상단 작은 라벨), headline(메인 카피), body(서브 카피) |
| 2 | body | 공감 — "나도 그래" | headline, body |
| 3~7 | body | 핵심 내용 1장 1메시지 | headline, body |
| 8 | body | 정리 / 반전 / 한 줄 요약 | headline, body |
| 9 | ending | 저장·팔로우·상담 CTA | headline, cta, disclaimer(보험 상품 다룰 때) |

   모든 장에 `image_scene`(이 장에 어울리는 사진 장면, 한국어 1문장)도 쓴다 → 이미지 세션이 사용.

3. **글자수 규칙 (design-spec 기준, 절대 초과 금지)**
   - 표지 headline: 한 줄 10자 × 최대 2줄 / body 24자 / label 12자
   - 본문 headline: 한 줄 14자 × 2줄 / body 한 줄 22자 × 3줄
   - 마지막 headline 16자 × 2줄 / cta 20자
   - 줄바꿈은 `\n`으로 **의미 단위**에서 끊는다. 조사만 다음 줄로 넘기지 않는다.

4. 저장 (3개 파일 모두):
   - `plan.json` — `new_set.py`가 만든 틀을 그대로 채운다 (키 이름 바꾸지 말 것). `category`, `hook_type`, `visual_style`(9장 공통 사진 톤 한 줄)도 채운다.
   - `plan.md` — 사람이 읽기 좋은 표 형태 (`references/plan-template.md` 형식)
   - `caption.md` — 인스타 본문 (첫 줄 후킹 → 3~5줄 요약 → 저장/팔로우 유도 → 해시태그 15~20개)

5. 점검:
   ```
   python3 cardnews-automation/scripts/check_set.py <세트폴더>
   ```
   이 단계에선 이미지가 아직 없으니 "images/0N.png 없음"만 남으면 정상. 글자수·금지어 문제는 직접 고친다.

6. 사용자에게 보여줄 것: `plan.md` 내용 표 + "어색한 문장 있으면 말씀하세요. 괜찮으면 '채택'".

### C. "채택" (또는 수정 후 채택)
1. `memory/approved.md` **맨 위**에 추가: 날짜 | 주제 / 표지 카피 / 좋았던 점 / 수정 메모(사용자가 고친 문장이 있으면 원래→수정, 이유 추정).
2. `memory/topics-used.md` 표에 한 줄 추가.
3. 다음 단계 안내 (복사해서 쓰도록 코드블록으로):
   ```
   /cardnews-images cardnews-automation/sets/<세트폴더명>
   ```
   "⚠️ 이미지 작업은 **새 대화창**에서 하세요."

## 품질 기준
- 한 장 = 메시지 1개. 본문에 설명을 욱여넣지 않는다.
- 숫자·구체 사례 > 추상적 조언. ("노후 준비 중요" ✕ → "65세에 필요한 생활비, 월 250만 원(예시)" ○)
- 표지 카피 후보를 3개 만들어 속으로 비교하고 가장 강한 것 1개만 쓴다. plan.md 하단에 나머지 2개를 "대안 표지"로 남긴다.
- brand.md 금지 표현 0개. 수입·금액은 "(예시)" 표기.
- `approved.md`에 쌓인 수정 메모 패턴은 **무조건 반영** (예: "~해요체 싫음" → 이후 전부 합니다체).
