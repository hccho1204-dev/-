---
name: design-md
description: GETDESIGN.md(VoltAgent/awesome-design-md) 84개 유명 브랜드 디자인 시스템(Apple·Stripe·Notion·Airbnb·Tesla·Nike·Spotify·Claude 등)을 레퍼런스로 골라 PPT·HTML 슬라이드·랜딩페이지·블로그 썸네일·카드뉴스·웹페이지에 색·글꼴·여백·버튼 규칙을 그대로 적용하는 스킬. "OO 브랜드 느낌으로", "애플 스타일로", "스트라이프처럼", "디자인 레퍼런스 적용", "DESIGN.md", "getdesign", "브랜드 레이아웃", "PPT 디자인 예쁘게" 요청에 사용.
---

# design-md — 브랜드 디자인 레퍼런스 적용

레퍼런스 없이 만들면 AI는 늘 비슷한 평범한 디자인을 낸다.
이 스킬은 **유명 브랜드의 디자인 규칙서(DESIGN.md)** 를 하나 골라, 그 규칙대로 결과물을 만든다.

- 원본: https://getdesign.md · https://github.com/VoltAgent/awesome-design-md (MIT 라이선스, `LICENSE`)
- 파일 위치: `brands/<브랜드>.md` (84개, 오프라인으로 바로 읽힘)
- 주의: 각 회사의 공식 디자인 시스템이 아니라 **공개 사이트를 분석해 만든 해석본**이다. 로고·상표는 쓰지 않는다.

## 작업 순서

1. **브랜드 고르기**
   - 사용자가 브랜드를 말했으면 그 파일을 쓴다.
   - 말하지 않았으면 아래 "분위기별 추천표"에서 용도에 맞는 1개를 골라 쓰고, 왜 골랐는지 한 줄로 알린다. (묻지 말고 먼저 만든다)
2. **규칙서 읽기** — `brands/<브랜드>.md`를 끝까지 읽는다.
   - 맨 위 `---` 사이(머리말): 색(`colors`), 글꼴(`typography`), 둥글기(`rounded`), 여백(`spacing`), 부품(`components`) 값
   - 본문: Overview(분위기) · Colors · Typography · Layout · Elevation · Shapes · Components · **Do's and Don'ts** · Responsive · Iteration Guide
3. **적용** — 결과물의 모든 색·글꼴 크기·굵기·자간·여백·모서리 값을 규칙서 값에서 가져온다. 임의 값 금지.
   - HTML/CSS: 머리말 값을 `:root { --color-primary: ... }` 같은 CSS 변수로 옮긴 뒤 그 변수만 쓴다.
   - PPT(pptx): 색은 HEX 그대로, 글꼴 크기는 px × 0.75 = pt 로 환산.
4. **한글 글꼴 대체** — 규칙서의 영문 전용 글꼴(Sohne, SF Pro 등)은 한글이 없다. 분위기를 맞춰 대체한다.

   | 규칙서 글꼴 성격 | 한글 대체 |
   |---|---|
   | 산세리프(고딕) 일반 | Pretendard |
   | 얇고 세련된 산세리프(300 이하) | Pretendard Light / SUIT Light |
   | 세리프(명조)·잡지풍 | Noto Serif KR / 나눔명조 |
   | 코드·고정폭 | D2Coding / JetBrains Mono |
   | 둥글고 친근한 | Gmarket Sans / 나눔스퀘어라운드 |

   자간(letterSpacing)이 크게 음수면 한글에서는 절반 정도만 적용한다(한글은 글자가 빽빽해서 겹쳐 보인다).
5. **검수** — 규칙서의 `Do's and Don'ts`를 체크리스트로 삼아 하나씩 확인하고, 어긋난 곳을 고친 뒤 넘긴다.

## 분위기별 추천표

| 용도·분위기 | 추천 브랜드 파일 |
|---|---|
| 깔끔·고급·사진 중심 (제품 소개, 프리미엄) | `apple`, `dji`, `tesla`, `bugatti` |
| 신뢰감·금융·보험·컨설팅 | `stripe`, `wise`, `mercury`, `coinbase`, `nerdwallet`, `ibm` |
| 따뜻·친근·생활밀착 (카페, 소상공인, 고객용) | `airbnb`, `starbucks`, `claude`, `oura`, `intercom` |
| 문서·업무·교육 자료 | `notion`, `airtable`, `miro`, `cal`, `mintlify` |
| 강렬·스포츠·에너지 | `nike`, `ferrari`, `lamborghini`, `bmw-m`, `spotify` |
| 잡지·뉴스·칼럼 | `wired`, `theverge`, `aljazeera`, `elevenlabs` |
| 다크·테크·개발자 | `linear.app`, `vercel`, `cursor`, `raycast`, `warp`, `x.ai`, `nvidia`, `supabase` |
| 알록달록·재미·크리에이티브 | `figma`, `clay`, `zapier`, `mistral.ai`, `framer`, `webflow` |
| 레트로 감성 | `dell-1996`, `nintendo-2001` |

전체 목록: `ls brands/` (파일 이름 = 브랜드 이름)

## 요청 예시

- "보험 상품 소개 PPT 10장, **stripe** 스타일로 만들어줘"
- "카페 이벤트 랜딩페이지 **airbnb** 느낌으로"
- "블로그 썸네일을 **apple** 레이아웃으로"
- "브랜드 말 안 할게, 신뢰감 있게 만들어줘" → 추천표에서 골라 적용

## 다른 스킬과 함께 쓰기

- PPT 파일: `anthropic-skills:pptx` / HTML 슬라이드: `anthropic-skills:bless-html-slides` — 이 스킬로 고른 브랜드 값을 그 스킬의 디자인 값으로 넘긴다.
- 랜딩페이지: `taste-skill` 과 함께 쓰되, 색·글꼴·여백은 이 규칙서가 우선한다.

## 최신본으로 갱신하기

```bash
git clone --depth 1 https://github.com/VoltAgent/awesome-design-md.git /tmp/adm
for d in /tmp/adm/design-md/*/; do cp "$d/DESIGN.md" ".claude/skills/design-md/brands/$(basename "$d").md"; done
```
