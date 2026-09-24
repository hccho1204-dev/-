---
name: cardnews-images
description: 인스타 카드뉴스 자동화 1단계-B(이미지). 세트 폴더의 plan.json(기획안)을 읽어 9장 모두 톤앤매너가 통일된 이미지 프롬프트를 만들고(image-prompts.md), 연결된 이미지 생성 도구가 있으면 순서대로 9장을 생성해 images/01.png~09.png로 저장한다. 사용자가 "카드뉴스 이미지", "이미지 9장", "이미지 프롬프트 뽑아줘", "/cardnews-images", 또는 기획안을 붙여넣고 사진을 만들어 달라고 하면 사용한다. 기획 세션과 분리된 새 대화에서 쓰는 것이 원칙.
---

# cardnews-images — 1단계-B: 이미지 9장 (톤 통일이 생명)

카드뉴스는 톤이 한 장만 삐끗해도 "없어 보인다". 그래서 **9장을 한 세트로, 한 세션에서, 같은 스타일 블록으로** 뽑는다.

## 입력
- 세트 폴더 경로 (예: `cardnews-automation/sets/2026-09-24_주제`) → `plan.json` 읽기
- 또는 사용자가 기획안 텍스트를 통째로 붙여넣은 경우 → 거기서 장별 `image_scene`만 추출
- 함께 읽기: `cardnews-automation/config/brand.md` 6번(비주얼 톤)

## 절차

### 1) 공통 스타일 블록(STYLE LOCK) 1개 만들기
9장 모든 프롬프트 **앞에 똑같이** 붙는 문단. `plan.json`의 `visual_style` + brand.md 6번을 합쳐 영어로 작성.
반드시 포함: 조명, 색감(팔레트 3색), 카메라/렌즈, 질감, 인물 조건, 금지 요소, 비율.
템플릿은 `references/style-lock.md`.

### 2) 장별 장면 프롬프트 9개
- `STYLE LOCK` + `SCENE {n}: {image_scene을 영어로 구체화}` + `COMPOSITION: {레이아웃 조건}`
- 레이아웃 조건 (design-spec 기준 — 글자 들어갈 자리 비우기):
  - 1장(표지)·9장(마무리): 사진이 배경 전체 → **하단 40%는 단순한 배경(여백)**, 피사체는 상단/중앙
  - 2~8장(본문): 사진은 상단 60% 영역에 들어감 → **피사체를 중앙~상단에**, 하단은 잘려도 되게
- 모든 프롬프트 끝: `no text, no letters, no logos, no watermark`
- 같은 인물이 여러 장에 나오면 인물 묘사(나이·헤어·옷)를 **토씨 하나 안 바꾸고** 반복.

### 3) `image-prompts.md` 저장
형식:
```markdown
# 이미지 프롬프트 — {set_id}
## STYLE LOCK
...
## 01 (표지)
<전체 프롬프트 — 그대로 복사해서 쓸 수 있게 코드블록>
...
## 09 (마무리)
...
```

### 4) 이미지 생성 — 둘 중 하나
**A. 이미지 생성 도구가 연결돼 있을 때** (예: Higgsfield `generate_image`, Canva `generate-image`, Adobe Firefly 등)
- ToolSearch로 `generate image` 도구를 찾는다.
- **01번부터 09번까지 순서대로** 생성 (배치 도구가 있으면 한 번에, 결과는 번호 순으로 매칭).
- 비율 4:5 (1080×1350) 지정. 1번 결과를 확인하고 톤이 괜찮으면 같은 설정·같은 모델·같은 seed(가능하면)로 나머지 진행.
- 받은 파일을 `images/01.png` ~ `images/09.png`로 저장.

**B. 도구가 없을 때** (ChatGPT / Gemini / Midjourney에 붙여넣기)
사용자에게 아래를 그대로 안내:
1. ChatGPT(또는 Gemini) **새 대화 1개**를 연다.
2. 첫 메시지: "지금부터 9장을 같은 스타일로 만들 거야. 매번 4:5 세로, 글자 없이." + STYLE LOCK 붙여넣기
3. 01 프롬프트부터 09까지 **순서대로 하나씩** 붙여넣고 생성 → 각각 다운로드.
4. 다 받으면:
   ```
   python3 cardnews-automation/scripts/rename_images.py cardnews-automation/sets/<세트폴더명> ~/Downloads --dry-run
   ```
   순서 확인 후 `--dry-run` 빼고 다시 실행.

### 5) 톤 검수 (이미지가 폴더에 들어온 뒤)
- 9장을 모두 열어 보고 체크: 색온도 / 밝기 / 인물 동일성 / 글자·워터마크 유무 / 손가락·얼굴 왜곡.
- 튀는 장이 있으면 **그 장만** 같은 세션에서 재생성 (프롬프트에 "match the color grading of image 01" 추가).
- 마지막에:
  ```
  python3 cardnews-automation/scripts/check_set.py cardnews-automation/sets/<세트폴더명>
  ```
  `READY`가 나오면 다음 단계 안내:
  ```
  /cardnews-miricanvas cardnews-automation/sets/<세트폴더명> 폴더 보고 작업 시작해
  ```
  "⚠️ 이 명령은 **Claude Cowork**(내 PC 크롬을 조작할 수 있는 곳)에서 실행하세요."
