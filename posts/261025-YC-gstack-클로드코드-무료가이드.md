# YC 대표의 클로드 코드 팀(gstack) — 무료 가이드

> 댓글에 "YC" 남긴 분께 드리는 자료입니다.
> 원본: https://github.com/garrytan/gstack (깃허브 별 13만7천 개, 2026.10 기준)

---

## 0. 이게 뭐예요?

Y 콤비네이터 대표 개리 탄이 직접 쓰는 클로드 코드 세팅입니다.
클로드 한 명을 '회사 하나'로 바꿔 줍니다.
기획자, 대표, 개발 팀장, 테스트 담당, 보안 담당이 각각 따로 있어요.
본인 말로는 YC 일을 하면서 60일 동안 서비스 3개를 냈다고 합니다.

---

## 1. 설치 문장 (복사해서 클로드 코드에 그대로 붙여넣기)

클로드 코드 창에 아래 문장을 **통째로** 붙여넣고 엔터만 누르세요.

```
Install gstack: run git clone --single-branch --depth 1 https://github.com/garrytan/gstack.git ~/.claude/skills/gstack && cd ~/.claude/skills/gstack && ./setup then add a "gstack" section to CLAUDE.md that says to use the /browse skill from gstack for all web browsing, never use mcp__claude-in-chrome__* tools. Then ask the user if they also want to add gstack to the current project so teammates get it.
```

| 준비물 | 설명 |
|---|---|
| 클로드 코드 | 이미 쓰고 있으면 OK |
| Git | 파일 내려받는 도구. 없으면 클로드가 설치하라고 알려줌 |
| Bun | 실행 도구. 없으면 클로드에게 "Bun 설치해줘"라고 말하면 됨 |
| Node.js | 윈도우만 필요 |

막히면 클로드에게 그대로 말하세요. "설치하다 에러 났어. 고쳐줘."

---

## 2. 딱 5개만 기억하세요

| 순서 | 명령어 | 역할 | 한 줄 설명 | 코딩 몰라도? |
|---|---|---|---|---|
| 1 | `/office-hours` | YC 파트너 | 내 아이디어를 6가지 질문으로 꼬치꼬치 따져 묻고, 기획서를 써 줌 | ✅ 바로 사용 |
| 2 | `/plan-ceo-review` | 대표(CEO) | 기획을 대표 눈으로 다시 봄. "더 크게 갈까, 줄일까" 4가지 방향 제시 | ✅ 사용 가능 |
| 3 | `/review` | 개발 팀장 | 테스트는 통과했는데 실제로 터질 숨은 버그를 찾고 쉬운 건 바로 고침 | ⚠️ 코드가 있어야 함 |
| 4 | `/qa` | 테스트 담당 | 진짜 브라우저를 열고 사람처럼 눌러 보며 오류를 찾고 고침 | ⚠️ 만든 사이트가 있어야 함 |
| 5 | `/cso` | 보안 책임자 | 해킹당할 구멍을 찾아 보고서로 정리 | ⚠️ 코드가 있어야 함 |

---

## 3. 따라하기 (이 순서대로 쓰세요)

1. **아이디어만 있을 때** → `/office-hours` 입력
   - 예: `/office-hours 동네 카페 단골 적립 앱을 만들고 싶어`
   - 질문이 오면 솔직하게 답하세요. 끝나면 기획서가 나옵니다.
2. **기획서가 나왔을 때** → `/plan-ceo-review` 입력
   - "이 기획 대표 눈으로 봐줘"까지 붙이면 더 좋습니다.
3. **클로드가 만들어 준 뒤** → `/review` 입력
   - 숨은 버그를 찾아 고칩니다.
4. **화면이 있는 서비스면** → `/qa` 입력
   - 예: `/qa 내 사이트 로그인부터 결제까지 눌러봐`
5. **세상에 공개하기 전** → `/cso` 입력
   - 보안 점검 한 번은 꼭 돌리세요.

---

## 4. 코딩 모르는 분께

`/office-hours` 하나만 써도 본전입니다.
사업 아이디어, 신상품, 블로그 기획까지 다 됩니다.
"이거 될까?" 싶을 때 친구 대신 물어보세요.
쓴소리를 해 줍니다.
