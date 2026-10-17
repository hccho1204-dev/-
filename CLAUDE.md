# CLAUDE.md

이 파일은 이 저장소에서 작업하는 AI 어시스턴트(Claude Code 등)를 위한 안내서입니다.
This repository is a **content & Claude Code skills repository** for a Korean insurance sales
organization — not a traditional software codebase.

---

## 1. 저장소 개요 (What this repo is)

**블레스본부(BLESS INSIGHT)** — 인카금융서비스 VIP총괄, 본부장 **조홍철** — 의 마케팅·채용·
고객관리 콘텐츠를 자동 생성하기 위한 저장소입니다. 저장소는 두 축으로 구성됩니다:

1. **`.claude/skills/`** — 콘텐츠를 생성하는 재사용 가능한 Claude Code **스킬(SKILL)** 정의.
2. **`posts/`** — 스킬로 생성된 실제 산출물(블로그 포스트 등)이 저장되는 곳.

빌드 시스템·패키지 매니저·테스트 러너가 없습니다. 유일한 실행 코드는 하나의 Python
스크립트(PDF 생성기)뿐입니다. 대부분의 "코드"는 Markdown 지침과 Markdown 산출물입니다.

### 대상 독자·시장 (Target audience)
- 손해보험/생명보험 경력직 설계사
- 경력단절 여성
- 간호사 / 간호조무사 / 요양보호사
- (채용) 위 그룹을 블레스본부로 스카우트하려는 리크루팅 대상자

---

## 2. 디렉터리 구조 (Directory layout)

```
/
├── CLAUDE.md                       # 이 파일
├── TEST_COVERAGE_ANALYSIS.md       # 테스트 전략 참고 문서(코드 없음 상태 기준)
├── posts/                          # 생성된 블로그 포스트 산출물 (.md)
│   └── YYMMDD-키워드.md
└── .claude/
    └── skills/                     # Claude Code 스킬 정의
        ├── tistory-aeo-post/       # 티스토리 AEO 블로그 포스트 생성
        │   ├── SKILL.md
        │   └── references/brand-voice.md      ← 전 스킬 공통 브랜드 규칙
        ├── coverage-analysis-report/          # 고객 보장분석 PDF 리포트 생성
        │   ├── SKILL.md
        │   ├── references/report-style.md
        │   └── scripts/generate_report.py     ← 유일한 실행 코드 (reportlab)
        ├── recruit-proposal/                  # 설계사 모집 제안서 PDF 생성
        │   ├── SKILL.md
        │   └── references/proposal-template.md
        └── sns-content-creator/               # 인스타 릴스/피드/카드뉴스/캘린더 생성
            ├── SKILL.md
            └── references/
                ├── content-calendar-template.md
                └── hashtag-sets.md
```

### 각 스킬의 표준 구성
- **`SKILL.md`** — 스킬의 핵심. `Trigger`(트리거 키워드) → 프로세스 단계 → 출력 형식 →
  필수 규칙 → 검증 체크리스트 순으로 구성.
- **`references/`** — 스킬이 참조하는 톤·템플릿·데이터(해시태그 세트 등).
- **`scripts/`** — (있는 경우) 실제 실행 코드.

---

## 3. 스킬 카탈로그 (Skills)

| 스킬 | 목적 | 주요 트리거 키워드 | 출력 |
|------|------|--------------------|------|
| `tistory-aeo-post` | AEO 최적화 블로그 포스트 | "블로그 글 써줘", "티스토리 포스트", "AEO 글" | `.md` → `posts/` |
| `coverage-analysis-report` | 고객 7대 보장영역 분석 리포트 | "보장분석", "보험 진단", "보험 점검" | PDF + JSON |
| `recruit-proposal` | 대상자 유형별 모집 제안서 | "모집 제안서", "이직 제안", "채용 제안서" | PDF |
| `sns-content-creator` | 릴스/피드/카드뉴스/30일 캘린더 | "릴스 스크립트", "카드뉴스", "콘텐츠 캘린더" | `.md` |

새 콘텐츠 요청을 받으면 먼저 위 스킬 중 해당하는 것이 있는지 확인하고, 있다면 그
**`SKILL.md`의 프로세스 단계와 검증 체크리스트를 그대로 따르세요.**

---

## 4. 브랜드 규칙 — 모든 작업의 최우선 (Brand rules — highest priority)

`.claude/skills/tistory-aeo-post/references/brand-voice.md`가 **전 스킬 공통 기준**입니다.
다른 스킬들도 이 파일을 참조하도록 작성되어 있습니다. 콘텐츠를 만들거나 수정하기 전에
반드시 이 규칙을 지키세요.

### 고정 브랜딩 문구 (정확히 이 표기 사용)
- 소속: **블레스본부 | 인카금융서비스 VIP총괄 | 본부장 조홍철**
- 모토: **"우리가 가면, 길이 됩니다"**
- 2026 테마: **"Always like the first time! I CAN DO IT"**
- 메인 컬러(블레스 오렌지): **`#FF6B35`**
- 강조 박스 배경: `#FFF5F0`
- 채용 페이지: `bless-insight-recruit.netlify.app`
- 상담 채널: 카카오 오픈채팅

### 금지 표현 (절대 사용 금지)
"무조건", "반드시 성공", "100%", "돈 벌기 쉬운", "누구나 할 수 있는",
"월 OOO만 원 보장", "실패 없는", "확실한 수입", 그리고 타사 비하 표현.

### 수입 언급 규칙
1. 구체적 금액은 반드시 **"예시"**임을 명시.
2. "개인 역량과 활동량에 따라 차이가 있습니다" 문구 병기.
3. 단일 값이 아니라 **범위**로 표현 (예: "월 200~400만 원 수준(예시)").

### 보장분석 리포트 특별 규칙
- 특정 보험사·상품 **직접 권유 금지** (영역·방향만 제시).
- 기존 보험 **해지 적극 권유 금지** → "전문 설계사와 상담 후 결정" 으로 안내.
- 면책 문구를 반드시 포함.

### 톤
현실적이고 솔직한 어조, 공감형 스토리텔링, 선배가 후배에게 조언하듯 따뜻하지만 솔직하게.

---

## 5. 산출물 규칙 (Output conventions)

### 파일명 (Filenames)
- 블로그 포스트: `YYMMDD-키워드.md` (예: `260316-간호사-보험설계사-이직.md`)
- 보장분석 리포트: `보장분석_고객명_YYMMDD.pdf` (+ 동일명 `.json` 중간 데이터)
- 모집 제안서: `제안서_대상자명_YYMMDD.pdf`
- SNS 콘텐츠: `YYMMDD-유형-키워드.md` (예: `260315-릴스-보험설계사수입.md`)
- 날짜는 **YYMMDD** 형식 (년 2자리). 언어는 한국어, 하이픈으로 단어 구분.

### 블로그 포스트 필수 구조 (AEO)
1. 질문형 타이틀 (`# ...`)
2. **핵심 답변 블록** — 타이틀 바로 아래, `> ` 인용 블록, 2~3문장 (AI 검색엔진 인용 대상)
3. 소주제 3개 (현실 공감 → 실질 정보 → 실천 방법)
4. "블레스본부는 이렇게 지원합니다" 섹션
5. FAQ 3~5개
6. CTA (카카오 오픈채팅 + 채용 페이지 링크)
- 본문 길이 1,500~3,000자, 태그 10개 이상.

---

## 6. 유일한 실행 코드 (The only executable code)

`.claude/skills/coverage-analysis-report/scripts/generate_report.py`
- **의존성**: `reportlab` (PDF 생성). 실행 전 설치 필요: `pip install reportlab`
- **실행**:
  ```bash
  python .claude/skills/coverage-analysis-report/scripts/generate_report.py \
      --input data.json --output 보장분석_홍길동_260315.pdf
  ```
- 입력은 `SKILL.md` 1단계에 정의된 고객/보험 JSON 스키마를 따릅니다.

자동화된 테스트는 없습니다. `TEST_COVERAGE_ANALYSIS.md`는 향후 코드가 추가될 때를 대비한
테스트 전략 참고 문서이며, 현재 저장소 상태(코드 거의 없음)를 기준으로 작성되었습니다.

---

## 7. 개발 워크플로 (Working in this repo)

### 콘텐츠를 생성/수정할 때
1. 요청에 해당하는 스킬을 `.claude/skills/`에서 찾는다.
2. 그 `SKILL.md`의 **프로세스 단계**를 순서대로 수행한다.
3. `brand-voice.md`의 톤·금지 표현·수입 규칙을 준수한다.
4. `SKILL.md` 하단의 **검증 체크리스트** 모든 항목을 통과시킨다.
5. 산출물은 위 파일명 규칙에 맞춰 올바른 위치(`posts/` 등)에 저장한다.

### 스킬 자체를 수정/추가할 때
- 기존 스킬의 구조(Trigger → 프로세스 → 출력 형식 → 필수 규칙 → 검증 체크리스트)를 따른다.
- 공통 브랜드 규칙은 새로 쓰지 말고 `brand-voice.md`를 참조하도록 한다.
- 브랜딩 문구·컬러·CTA는 4장의 고정 값을 사용한다.

### Git
- 작업 브랜치: **`claude/claude-md-docs-xd9tvl`** (지정된 경우 이 브랜치에서 작업·푸시).
- 커밋 메시지는 기존 관례를 따른다: `feat:` / `refactor:` 접두어 + **한국어** 설명
  (예: `feat: AEO 최적화 블로그 포스트 10개 추가`).
- 요청받지 않는 한 PR을 만들지 않는다.

---

## 8. 빠른 참조 (Quick reference)

- **브랜드 규칙의 단일 소스**: `.claude/skills/tistory-aeo-post/references/brand-voice.md`
- **언어**: 모든 콘텐츠·커밋 메시지는 한국어.
- **하지 말 것**: 과장/보장성 수입 표현, 특정 상품 직접 권유, 타사 비하, 면책 문구 누락.
- **항상 포함**: 정확한 브랜딩 문구, 예시임을 명시한 수입 언급, CTA(카카오 오픈채팅 + 채용 링크).
</content>
</invoke>
