# AI 회사 시스템 — Claude Code 안내

사용자는 **비개발자 CEO**다. 명령어를 안내할 때는 어디를 열고, 무엇을 입력하고, 왜 하는지까지 쉽게 설명한다. 한국어로 답한다.

## 구조
- 실행: `node server.js` (Node 18+, 외부 패키지 없음) → http://localhost:8787
- `lib/workflow.js`: 업무 단계 엔진. triage → debate → assign → execute → review → (rejected ↔ rework) → strategy → final → publish_wait/ceo_wait → publishing → done
- `lib/llm.js`: 클로드(비서실장=models.chief, 직원=models.staff), GPT(전략실장=models.strategist). 키 없으면 `lib/mock.js` 체험 모드
- `lib/threads.js`: Threads Graph API (OAuth 코드 교환, 장기 토큰, 게시, 인사이트)
- `lib/report.js`: 최종 보고서를 `standards/templates/ceo-report.html` 고정 양식에 채움
- `config/company.json`, `config/agents.json`: 회사·직원 정의
- `standards/*.md`: 완료 기준. `- [ ]` 줄이 비서실장 검수 체크리스트가 된다
- `memory/`: 회사 기억, 성공·실패 교훈 (자동 누적)
- `data/`(업무 기록·secrets·토큰), `workspace/`(작업 문서)는 git 제외

## 규칙
- 모든 작업 문서 첫 줄은 `> 한줄요약: ...` (과거 문서 탐색 시 이 줄만 읽어 토큰 절약)
- `data/secrets.json`, `data/threads.json` 내용은 절대 출력·커밋하지 않는다
- 전략실장은 승인권이 없다 (의견만). 최종 판단은 비서실장, 중요 업무 최종 승인은 CEO
