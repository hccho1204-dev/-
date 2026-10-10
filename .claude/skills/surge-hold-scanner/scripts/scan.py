#!/usr/bin/env python3
"""급등 후 버티기(Surge-Hold) 스캐너.

규칙
  1) 하루에 +20% 이상 오른 날(급등일)을 찾는다.
  2) 급등일 다음 3거래일 동안 종가가 '급등분의 절반' 아래로 한 번도 안 내려가면 통과.
     기준선 = 급등 전날 종가 + (급등일 종가 - 급등 전날 종가) / 2
  3) 3일째 종가가 '매수 신호 가격'.

입력: prices.json  {"TICK": {"name":..., "note":..., "bars": [[date,o,h,l,c,v], ...]}}
출력: results.json (추천 5개 + 관찰 + 탈락 사유)

사용법: python3 scan.py prices.json results.json [--asof 2026-10-09] [--market us|kr]
"""
import json
import sys
from datetime import date

SURGE_PCT = 0.20      # 급등 기준 +20%
HOLD_DAYS = 3         # 버티기 확인 기간
LOOKBACK = 15         # 최근 몇 거래일 안의 급등만 볼지
# 시장별 기준: 동전주 가격, 최소 거래대금, 유동성 만점 거래대금
MARKETS = {
    "us": {"label": "미국 주식", "cur": "USD", "min_price": 1.0, "min_vol": 1_000_000, "full_vol": 20_000_000,
           "penny": "1달러 미만 동전주", "thin": "거래대금 100만 달러 미만"},
    "kr": {"label": "한국 주식", "cur": "KRW", "min_price": 1000, "min_vol": 1_000_000_000, "full_vol": 30_000_000_000,
           "penny": "1,000원 미만 동전주", "thin": "거래대금 10억 원 미만"},
}
M = MARKETS["us"]
PIN_RANGE = 0.015     # 급등 후 하루 변동폭이 1.5% 미만으로 굳으면 '인수가 고정' 의심


def analyze(ticker, info):
    bars = sorted(info["bars"], key=lambda b: b[0])
    closes = [b[4] for b in bars]
    n = len(bars)
    events = []
    for i in range(max(1, n - LOOKBACK), n):
        prev, cur = closes[i - 1], closes[i]
        if prev and (cur / prev - 1) >= SURGE_PCT:
            events.append(i)
    if not events:
        return {"ticker": ticker, "status": "no_surge"}

    # 가장 최근 급등 중, 3일 검증이 끝난 것 우선 / 없으면 진행 중인 것
    results = []
    for i in events:
        prev, sc = closes[i - 1], closes[i]
        gain = sc - prev
        line = prev + gain / 2
        after = bars[i + 1:i + 1 + HOLD_DAYS]
        broke = [b for b in after if b[4] < line]
        days_done = len(after)
        r = {
            "ticker": ticker,
            "name": info.get("name", ticker),
            "note": info.get("note", ""),
            "surge_date": bars[i][0],
            "surge_pct": round((sc / prev - 1) * 100, 1),
            "prev_close": round(prev, 4),
            "surge_close": round(sc, 4),
            "half_line": round(line, 4),
            "days_checked": days_done,
            "last_date": bars[-1][0],
            "last_close": round(closes[-1], 4),
            "path": [[b[0], round(b[4], 4)] for b in bars[max(0, i - 5):]],
        }
        if broke:
            r["status"] = "failed"
            r["reason"] = f"{broke[0][0]} 종가가 절반선 아래로 하락"
        elif days_done < HOLD_DAYS:
            r["status"] = "watch"
            r["reason"] = f"검증 {days_done}/{HOLD_DAYS}일차 진행 중"
        else:
            sig = after[-1]
            r["status"] = "pass"
            r["signal_date"] = sig[0]
            r["signal_close"] = round(sig[4], 4)
            r["min_close_3d"] = round(min(b[4] for b in after), 4)
            # 유지율: 3일 중 최저 종가가 급등분을 얼마나 지켰나 (1.0 = 하나도 안 내줌)
            r["retention"] = round((r["min_close_3d"] - prev) / gain, 2)
            r["since_signal_pct"] = round((closes[-1] / sig[4] - 1) * 100, 1)
            if closes[-1] < line:
                r["status"] = "failed"
                r["reason"] = "신호 이후 절반선 아래로 하락 (손절 구간)"
        # 인수합병 가격 고정 의심
        post = bars[i:i + 1 + HOLD_DAYS]
        if len(post) >= 2 and all((b[2] - b[3]) / b[4] < PIN_RANGE for b in post):
            r["pinned"] = True
        recent = bars[-10:]
        r["avg_dollar_vol"] = round(sum(b[4] * b[5] for b in recent) / len(recent))
        results.append(r)

    passes = [r for r in results if r["status"] == "pass"]
    if passes:
        return max(passes, key=lambda r: r["surge_date"])
    watches = [r for r in results if r["status"] == "watch"]
    if watches:
        return max(watches, key=lambda r: r["surge_date"])
    return max(results, key=lambda r: r["surge_date"])


def flags_and_score(r):
    flags = []
    note = r.get("note", "").lower()
    if r.get("pinned") or "인수" in note or any(k in note for k in ("buyout", "acquisition", "acquired by")):
        flags.append("인수가 고정 의심(더 오를 여지 거의 없음)")
    if r["last_close"] < M["min_price"]:
        flags.append(M["penny"])
    if r["avg_dollar_vol"] < M["min_vol"]:
        flags.append(M["thin"])
    if r.get("since_signal_pct", 0) <= -20:
        flags.append("신호 후 20% 넘게 하락")
    r["flags"] = flags
    if r["status"] != "pass":
        r["score"] = 0
        return r
    retention = min(max(r["retention"], 0), 2.0) / 2.0          # 버틴 힘 (0~1)
    chase = r["since_signal_pct"]
    if chase > 30:      # 신호 후 너무 올라 '추격' 위험
        chase_pen = min((chase - 30) / 70, 1)
    elif chase < -10:   # 신호 후 힘이 빠지는 중
        chase_pen = min(-chase / 30, 1)
    else:
        chase_pen = 0
    liq = min(r["avg_dollar_vol"] / M["full_vol"], 1)               # 유동성
    days_since = sum(1 for d, _ in r["path"] if d > r["signal_date"])
    fresh = max(0, 1 - days_since / 8)                           # 신호가 최근일수록 가점
    score = 45 * retention + 20 * liq + 20 * fresh + 15 * (1 - chase_pen)
    if flags:
        score *= 0.4
    r["score"] = round(score, 1)
    r["chase_risk"] = chase > 30
    return r


def main():
    src, dst = sys.argv[1], sys.argv[2]
    global M
    if "--market" in sys.argv:
        M = MARKETS[sys.argv[sys.argv.index("--market") + 1]]
    asof = sys.argv[sys.argv.index("--asof") + 1] if "--asof" in sys.argv else str(date.today())
    data = json.load(open(src, encoding="utf-8"))
    rows = [analyze(t, d) for t, d in data.items() if d.get("bars")]
    rows = [flags_and_score(r) for r in rows if r["status"] != "no_surge"]
    picks = sorted([r for r in rows if r["status"] == "pass" and not r["flags"]],
                   key=lambda r: -r["score"])[:5]
    if len(picks) < 5:  # 깨끗한 종목이 5개 미만이면 경고 붙은 통과 종목으로 채움
        extra = sorted([r for r in rows if r["status"] == "pass" and r["flags"]],
                       key=lambda r: -r["score"])
        picks += extra[:5 - len(picks)]
    out = {
        "asof": asof,
        "market": M["label"],
        "currency": M["cur"],
        "rule": {"surge_pct": SURGE_PCT * 100, "hold_days": HOLD_DAYS, "lookback": LOOKBACK},
        "universe": len(data),
        "picks": picks,
        "watch": sorted([r for r in rows if r["status"] == "watch"], key=lambda r: r["surge_date"], reverse=True),
        "passed_other": [r for r in rows if r["status"] == "pass" and r not in picks],
        "failed": [r for r in rows if r["status"] == "failed"],
    }
    json.dump(out, open(dst, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"후보 {len(data)} | 추천 {len(picks)} | 관찰 {len(out['watch'])} | 탈락 {len(out['failed'])}")
    for i, r in enumerate(picks, 1):
        print(f"{i}. {r['ticker']:6} 점수 {r['score']:5} 급등 {r['surge_date']} +{r['surge_pct']}% "
              f"유지율 {r['retention']} 신호후 {r['since_signal_pct']}% {' / '.join(r['flags'])}")


if __name__ == "__main__":
    main()
