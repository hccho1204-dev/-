# plan.md 형식

```markdown
# 카드뉴스 기획안: {주제}

- 세트: {set_id}
- 카테고리: {category} / 후킹 유형: {hook_type}
- 사진 톤(9장 공통): {visual_style}

| 장 | 구분 | 라벨/헤드라인 | 본문/CTA | 사진 장면 |
|---|---|---|---|---|
| 1 | 표지 | [라벨] {label}<br>**{headline}** | {body} | {image_scene} |
| 2 | 공감 | **{headline}** | {body} | {image_scene} |
| ... | | | | |
| 9 | 마무리 | **{headline}** | {cta}<br><small>{disclaimer}</small> | {image_scene} |

## 대안 표지
- B안: ...
- C안: ...

## 체크
- [ ] 글자수 OK (check_set.py)
- [ ] 금지 표현 0개
- [ ] 채택
```

# plan.json 예시

```json
{
  "set_id": "2026-09-24_경력단절-설계사-현실",
  "date": "2026-09-24",
  "topic": "40대 경력단절 여성이 보험설계사 시작할 때 현실",
  "category": "커리어/이직",
  "hook_type": "question",
  "visual_style": "따뜻한 오전 자연광, 베이지·크림 톤, 차분한 한국 40대 여성 일상, 필름 질감 약하게",
  "pages": [
    {"no": 1, "type": "cover", "label": "본부장 노트 #7", "headline": "10년 쉬었는데\n다시 될까요?", "body": "경력단절 후 설계사, 현실만 말합니다", "image_scene": "창가 식탁에 앉아 노트북을 여는 40대 여성의 옆모습"},
    {"no": 2, "type": "body", "headline": "아이 다 키우고 나니\n제 자리가 없더라고요", "body": "이력서 빈칸 10년.\n면접 보러 갈 곳도 마땅치 않고.\n많은 분들이 여기서 멈춥니다.", "image_scene": "빈 이력서 옆에 놓인 커피잔 클로즈업"},
    {"no": 9, "type": "ending", "headline": "혼자 고민하지\n마세요", "cta": "프로필 링크에서 상담 신청", "disclaimer": "", "image_scene": "환하게 웃으며 동료와 대화하는 여성, 밝은 사무실"}
  ]
}
```
(실제 파일에는 1~9장이 모두 있어야 한다.)
