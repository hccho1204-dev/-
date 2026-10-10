---
name: surge-hold-scanner
description: "급등 후 3일 버티기" 규칙으로 미국·한국 주식 중 하루 +20% 급등 뒤 3거래일 동안 상승분의 절반을 지킨 종목을 골라 매일 5개를 추천하고 대시보드로 보여준다. "급등주 스캔", "오늘의 5종목", "버티기 종목", "파브라이 규칙", "급등 버티기 대시보드" 요청에 사용.
---

# surge-hold-scanner — 급등 버티기 레이더

## Trigger

- "오늘의 5종목", "급등 버티기 종목 찾아줘", "급등주 스캔", "한국 주식 5종목", "상한가 버티기"
- "파브라이 규칙", "20% 급등 3일 버티기"
- "급등 대시보드 업데이트"

## 규칙 (한 줄 요약)

| 단계 | 내용 |
|---|---|
| 1. 급등 포착 | 최근 15거래일 안에 **하루 종가 +20% 이상** 오른 날 |
| 2. 3일 버티기 | 다음 3거래일 종가가 모두 **절반선** 위 (절반선 = 급등 전날 종가 + 상승폭÷2) |
| 3. 신호 | 3일째 종가 = 매수 신호. 통과 종목을 점수로 줄 세워 상위 5개 |

## 점수 (100점)

| 항목 | 배점 | 의미 |
|---|---|---|
| 버틴 힘(유지율) | 45 | 3일 중 최저 종가가 상승폭을 얼마나 지켰나 (200%면 만점) |
| 유동성 | 20 | 최근 10일 평균 거래대금 (2천만 달러면 만점) |
| 신선도 | 20 | 신호가 며칠 전인지 (오늘에 가까울수록) |
| 추격 위험 | 15 | 신호 뒤 이미 30% 넘게 올랐으면 감점 |

**경고 붙으면 점수 ×0.4** — 인수가 고정(현금 인수 발표로 주가가 굳음), 1달러 미만 동전주, 거래대금 100만 달러 미만.
경고 없는 종목을 먼저 채우고, 5개가 안 되면 경고 종목으로 채운다(대시보드에 경고 칩 표시).

## 실행 순서

1. **후보 모으기** → `prices.json` 만들기
   - 인터넷이 열린 PC/GitHub Actions: 한국은 `python3 scripts/fetch_kr.py prices.json` (pykrx, 전 종목 자동).
   - Claude 클라우드 세션(금융 사이트 차단됨):
     - WebSearch로 최근 15거래일의 미국 "top gainers / stock soars 20%" 종목 티커를 20~40개 모은다
       (Pluang·Morningstar·StockAnalysis 상승률 상위 요약, 인수합병·FDA·실적 뉴스).
     - 각 티커를 `mcp__PlayMCP__UsStockInfo-get_historical_stock_prices(ticker, period="2mo")`로 받는다.
     - 형식: `{"TICK": {"name": "회사명", "note": "급등 이유(인수면 '현금 인수' 명시)", "bars": [["YYYY-MM-DD", o,h,l,c,v], ...]}}`
     - 레버리지 ETF는 넣지 않는다.
2. **스캔**: `python3 scripts/scan.py prices.json results.json --asof YYYY-MM-DD`
3. **대시보드**: `python3 scripts/build_dashboard.py results.json dashboard.html`
4. **게시**: Artifact 도구로 `dashboard.html`을 게시. 이미 있는 대시보드면 같은 URL로 업데이트(`url` 지정).
5. **보고**: 5종목을 표(티커·회사·급등일/급등률·유지율·신호 후 수익률·경고)로 답하고 대시보드 링크를 준다.

## 한국 주식 모드 (`--market kr`)

| 항목 | 미국 | 한국 |
|---|---|---|
| 동전주 경고 | 1달러 미만 | 1,000원 미만 |
| 거래대금 경고 | 100만 달러 미만 | 10억 원 미만 |
| 유동성 만점 | 2천만 달러 | 300억 원 |
| 후보 찾기 | "top gainers", "stock soars" | "상한가 종목 10월 O일", "EBN 데이터센터 상승 종목", "인포스탁 상한가" |
| 시세 티커 | `AAPL` | 코스피 `005930.KS` / 코스닥 `XXXXXX.KQ` (빈 값이면 다른 쪽 시도) |
| 대시보드 | https://claude.ai/artifact/WyXufmMJ1gaiL9XGfBfajW | https://claude.ai/artifact/5x8Yuwahc4kG3aZoQZ6S2R |
| 데이터 파일 | `data/prices.json`, `data/results.json` | `data/prices_kr.json`, `data/results_kr.json` |

- **날짜 주의**: 한국 종목 시세는 `2026-10-07T15:00:00Z` 처럼 오므로 **+9시간** 해서 날짜를 잡는다 (→ 2026-10-08).
- prices_kr.json 키는 6자리 종목코드, `name`은 한글 회사명, `note`는 급등 이유(테마·공시) 한 줄. 공개매수·인수 발표면 note에 '인수'를 넣는다.
- 상한가는 +30%라 하루 +20% 이상 종목이 자주 나온다. 후보는 최근 15거래일의 상한가·급등 종목 30개 안팎.
- 실행: `python3 scripts/scan.py prices_kr.json results_kr.json --asof YYYY-MM-DD --market kr` → `python3 scripts/build_dashboard.py results_kr.json surge-dashboard-kr.html`

## 반드시 지킬 것

- 사실 확인: 이 규칙을 모니시 파브라이가 말했다는 확인된 출처는 없다(파브라이는 가치투자자). 매번 짧게 밝힌다.
- 매수 권유가 아니라 규칙에 따른 자동 분류임을 밝힌다. 손절 기준(절반선 이탈)을 함께 안내한다.
- 데이터에 없는 숫자를 지어내지 않는다. 받은 일봉 종가만 쓴다.
- 현금 인수 발표 종목(OPCH처럼 인수가 근처에서 멈춘 종목)은 규칙상 통과해도 추천에서 뺀다.

## 파일

| 파일 | 역할 |
|---|---|
| `scripts/scan.py` | 규칙 판정 + 점수 + 상위 5개 선정 |
| `scripts/fetch_kr.py` | 한국 코스피·코스닥 전 종목 시세 수집 (pykrx) |
| `scripts/build_dashboard.py` | results.json → 대시보드 HTML |
| `assets/dashboard_template.html` | 대시보드 디자인 (라이트/다크 지원) |
