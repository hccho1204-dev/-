#!/usr/bin/env python3
"""AEO 최적화 블로그 포스트 자동 생성 스크립트.

Claude API 모드(기본) 또는 템플릿 모드(폴백)로 동작.
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
TOPICS_PATH = PROJECT_ROOT / "config" / "topics.json"
POSTS_DIR = PROJECT_ROOT / "posts"

SYSTEM_PROMPT = """당신은 블레스본부 Tistory 블로그 "보험설계사 현실 연구소 - BLESS INSIGHT"의 전문 블로그 작성자입니다.

## 브랜드 보이스
- 현실적이고 솔직한 어조
- 과장 없이 있는 그대로의 현실을 전달
- 타겟 독자의 고민에 공감형 스토리텔링으로 접근
- 선배 설계사가 후배에게 조언하듯 따뜻하지만 솔직하게

## 금지 표현 (절대 사용 금지)
- "무조건", "반드시 성공", "100%", "돈 벌기 쉬운"
- "누구나 할 수 있는", "월 OOO만 원 보장", "실패 없는", "확실한 수입"

## 수입 언급 규칙
- 구체적 금액 언급 시 "예시"임을 반드시 명시
- "개인 역량과 활동량에 따라 차이가 있습니다" 문구 병기
- 평균값보다는 범위로 표현

## 블레스본부 차별점 (본문에 자연스럽게 포함)
- 매일 DB 제공: 메디컬DB, 리워드DB, 보장분석DB, 피싱·해킹보험DB, 법인DB
- 투명한 수수료: 숨김 없는 수수료 구조
- 1:1 멘토링: 전담 멘토의 밀착 지원
- AI 자동화: 업무 효율을 높이는 AI 도구 활용

## 출력 구조 (반드시 준수)
```
# [질문형 타이틀]

> **[핵심 답변 블록]**
> 2~3문장으로 질문에 대한 직접적인 답변을 제공합니다.

## 소주제 1: [구체적 현실 이야기]

## 소주제 2: [실질적 정보 제공]

## 소주제 3: [실천 가능한 방법]

## 블레스본부는 이렇게 지원합니다

## 자주 묻는 질문 (FAQ)
**Q1. [질문]**
A. [답변]
(3~5개)

## 지금 시작하세요
[CTA]

---

**보험설계사로의 새로운 시작, 블레스본부와 함께하세요.**

📌 카카오 오픈채팅으로 상담하기
📌 블레스본부 채용 안내: [bless-insight-recruit.netlify.app](https://bless-insight-recruit.netlify.app)
```

## 검증 기준
- 핵심 답변 블록이 타이틀 바로 아래에 배치
- FAQ 3개 이상
- 본문 길이 1,500~3,000자
- 금지 표현 미사용
- CTA 포함
"""


def get_today_topic() -> dict:
    with open(TOPICS_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    topics = data["topics"]
    today = datetime.now()
    index = (today.year * 1000 + today.timetuple().tm_yday) % len(topics)
    return topics[index]


def generate_with_claude(topic: dict) -> str:
    try:
        import anthropic
    except ImportError:
        print("anthropic 패키지가 설치되지 않았습니다. 템플릿 모드로 전환합니다.")
        return generate_with_template(topic)

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("ANTHROPIC_API_KEY가 설정되지 않았습니다. 템플릿 모드로 전환합니다.")
        return generate_with_template(topic)

    client = anthropic.Anthropic(api_key=api_key)

    user_prompt = f"""다음 주제로 AEO 최적화 블로그 포스트를 작성해주세요.

- 타겟 독자: {topic['target']}
- 키워드: {topic['keyword']}
- 핵심 질문: {topic['question']}

마크다운 형식으로 본문만 출력해주세요. 메타데이터나 설명 없이 바로 본문을 시작하세요.
마지막에 태그를 아래 형식으로 추가해주세요:

---
tags: [태그1, 태그2, ...] (10개 이상)
"""

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
    )

    return message.content[0].text


def generate_with_template(topic: dict) -> str:
    keyword = topic["keyword"].replace("-", " ")
    question = topic["question"]
    target = topic["target"]

    target_descriptions = {
        "경력단절여성": "경력단절 후 새로운 시작을 고민하는 여성",
        "간호사": "병원 근무에서 새로운 커리어를 모색하는 간호사",
        "간호조무사": "의료 현장 경험을 새로운 분야에 활용하고 싶은 간호조무사",
        "요양보호사": "돌봄 경험을 바탕으로 새로운 도전을 꿈꾸는 요양보호사",
        "손보경력직": "더 나은 환경에서 역량을 펼치고 싶은 손보 경력직 설계사",
    }

    target_desc = target_descriptions.get(target, "보험설계사를 고민하는 분")

    post = f"""# {question}

> **결론부터 말씀드리면, 충분히 가능합니다.** 다만 현실적인 준비와 올바른 환경 선택이 중요합니다. {target_desc}분들이 블레스본부에서 안정적으로 정착하고 있는 이유를 솔직하게 말씀드리겠습니다.

## 현실적으로 어떤 고민을 하고 계신가요?

많은 {target}분들이 "{keyword}"에 대해 검색하시는 이유를 잘 알고 있습니다. 새로운 시작은 누구에게나 두려운 일입니다.

실제로 많은 분들이 겪는 고민입니다:
- "정말 나도 할 수 있을까?"
- "수입이 안정적이지 않으면 어쩌지?"
- "아는 사람한테 보험 팔아야 하는 건 아닐까?"

현실적으로 말씀드리면, 과거의 '지인 영업' 시대는 이미 지났습니다. 지금은 체계적인 DB 영업 시스템을 갖춘 조직에서 시작하는 것이 핵심입니다.

## 성공적인 전환을 위해 알아야 할 것들

{target} 경력이 보험영업에서 강점이 되는 이유가 있습니다:
- 사람을 대하는 경험과 공감 능력
- 성실함과 책임감
- 고객의 상황을 이해하는 눈

수입의 경우, 블레스본부 소속 설계사의 경우 활동 초기 월 200~400만 원 수준의 수입을 기대할 수 있습니다(예시이며, 개인 역량과 활동량에 따라 차이가 있습니다).

## 어떻게 시작하면 좋을까요?

쉽지 않지만, 방법은 있습니다. 다음 순서로 준비하시면 됩니다:

1. **정보 수집**: 다양한 GA(법인대리점)의 조건을 비교해보세요
2. **멘토 확인**: 1:1 전담 멘토가 있는 조직인지 확인하세요
3. **DB 시스템**: 매일 안정적으로 DB를 제공하는지 확인하세요
4. **교육 프로그램**: 초기 정착을 위한 교육이 체계적인지 살펴보세요

## 블레스본부는 이렇게 지원합니다

블레스본부에서는 이렇게 지원하고 있습니다:

- **매일 DB 제공**: 메디컬DB, 리워드DB, 보장분석DB, 피싱·해킹보험DB, 법인DB를 매일 제공합니다
- **투명한 수수료**: 숨김 없는 수수료 구조로 신뢰를 드립니다
- **1:1 멘토링**: 전담 멘토가 밀착 지원하여 초기 정착을 돕습니다
- **AI 자동화**: 업무 효율을 높이는 AI 도구를 활용할 수 있습니다

## 자주 묻는 질문 (FAQ)

**Q1. 보험 경험이 전혀 없어도 시작할 수 있나요?**
A. 네, 가능합니다. 블레스본부에서는 보험 경험이 없는 분들을 위한 체계적인 교육 프로그램과 1:1 멘토링을 제공하고 있습니다. 실제로 많은 {target} 출신 설계사분들이 성공적으로 정착하고 계십니다.

**Q2. 초기 수입이 불안정하지 않을까요?**
A. 현실적으로 말씀드리면, 초기 1~2개월은 적응 기간이 필요합니다. 하지만 매일 DB가 제공되는 환경에서는 활동량에 비례하여 안정적인 수입 기반을 만들 수 있습니다(개인 역량과 활동량에 따라 차이가 있습니다).

**Q3. 지인 영업을 해야 하나요?**
A. 아닙니다. 블레스본부는 매일 다양한 DB(메디컬DB, 리워드DB, 보장분석DB 등)를 제공하므로 지인 영업 없이 체계적인 DB 영업이 가능합니다.

**Q4. 블레스본부만의 차별점은 무엇인가요?**
A. 매일 DB 제공, 투명한 수수료 구조, 1:1 전담 멘토링, AI 자동화 도구 지원이 핵심 차별점입니다. 특히 초기 정착에 집중하는 멘토링 시스템이 많은 분들의 안정적인 시작을 돕고 있습니다.

## 지금 시작하세요

새로운 시작이 두려우신 건 당연합니다. 하지만 올바른 환경에서 시작한다면, 그 두려움은 곧 자신감으로 바뀔 수 있습니다.

블레스본부는 "우리가 가면, 길이 됩니다"라는 마음으로, 함께 성장할 동료를 찾고 있습니다.

---

**보험설계사로의 새로운 시작, 블레스본부와 함께하세요.**

📌 카카오 오픈채팅으로 상담하기
📌 블레스본부 채용 안내: [bless-insight-recruit.netlify.app](https://bless-insight-recruit.netlify.app)

---
tags: [{keyword}, 보험설계사, {target}, 블레스본부, 보험설계사 현실, 보험영업, GA, 인카금융서비스, DB영업, 보험설계사 시작, 보험설계사 수입, 1:1 멘토링]
"""
    return post


def validate_post(content: str) -> list[str]:
    errors = []
    forbidden = ["무조건", "반드시 성공", "100%", "돈 벌기 쉬운", "누구나 할 수 있는", "월 OOO만 원 보장", "실패 없는", "확실한 수입"]
    for word in forbidden:
        if word in content:
            errors.append(f"금지 표현 발견: '{word}'")

    if "> **" not in content[:500]:
        errors.append("핵심 답변 블록이 상단에 없습니다")

    faq_count = content.count("**Q")
    if faq_count < 3:
        errors.append(f"FAQ가 {faq_count}개 (최소 3개 필요)")

    if "카카오 오픈채팅" not in content or "bless-insight-recruit" not in content:
        errors.append("CTA가 누락되었습니다")

    return errors


def main():
    POSTS_DIR.mkdir(exist_ok=True)

    topic = get_today_topic()
    print(f"오늘의 주제: {topic['question']}")
    print(f"타겟: {topic['target']}")
    print(f"키워드: {topic['keyword']}")

    content = generate_with_claude(topic)

    errors = validate_post(content)
    if errors:
        print("⚠️  검증 경고:")
        for e in errors:
            print(f"  - {e}")

    today_str = datetime.now().strftime("%y%m%d")
    filename = f"{today_str}-{topic['keyword']}.md"
    filepath = POSTS_DIR / filename

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"✅ 포스트 생성 완료: {filepath}")

    result = {"file": str(filepath), "topic": topic["question"], "errors": errors}
    result_path = PROJECT_ROOT / "posts" / ".last_result.json"
    with open(result_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
