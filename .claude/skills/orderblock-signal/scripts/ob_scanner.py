#!/usr/bin/env python3
"""
오더블록(지지·저항 구간) 신호 스캐너 — 표준 라이브러리만 사용.

규칙
  1) 급등 직전 마지막 음봉  → 지지 구간(수요 구간)
  2) 급락 직전 마지막 양봉  → 저항 구간(공급 구간)
  3) 주가가 지지 구간으로 되돌아온 뒤, 종가가 직전 N개(기본 3) 캔들 고가를 모두 넘기면 → 매수
  4) 저항 구간에 닿은 뒤, 종가가 직전 N개 캔들 저가를 모두 깨면 → 매도
  5) 보유 중 종가가 지지 구간 하단을 깨면 → 손절

사용 예
  python3 ob_scanner.py scan 005930 000660 --days 400
  python3 ob_scanner.py scan --csv 삼성전자.csv
  python3 ob_scanner.py backtest 005930 --days 1500
  python3 ob_scanner.py optimize 005930 006400 --days 1500
  python3 ob_scanner.py demo            # 인터넷 없이 가상 데이터로 동작 확인

CSV 형식: date,open,high,low,close[,volume]  (헤더 필수, 날짜 오름차순)
"""
import argparse
import csv
import itertools
import json
import math
import random
import sys
import urllib.request
from dataclasses import dataclass, asdict, field

# ── 국장 기본값 (미장보다 변동폭·가격제한폭(±30%)을 고려해 조정) ──────────────
DEFAULTS = dict(
    surge_pct=10.0,   # 급등 판정: surge_bars 동안 누적 상승률(%)
    drop_pct=8.0,     # 급락 판정: surge_bars 동안 누적 하락률(%)
    surge_bars=3,     # 급등/급락을 몇 개 캔들로 볼지
    break_n=3,        # 돌파/이탈 확인용 직전 캔들 수
    zone_life=250,    # 구간 최대 유효기간(캔들 수, 약 1년). 그 전에 뚫리면 즉시 폐기
    touch_window=5,   # 구간 터치 후 몇 캔들 안에 돌파가 나와야 인정할지
)


@dataclass
class Bar:
    date: str
    open: float
    high: float
    low: float
    close: float
    volume: float = 0.0


@dataclass
class Zone:
    kind: str          # "support" | "resistance"
    idx: int           # 기준 캔들 위치
    date: str
    low: float
    high: float
    touched_at: int = -1
    used: bool = False
    broken: bool = False   # 지지 하단 이탈 / 저항 상단 돌파 시 구간 무효


@dataclass
class Signal:
    idx: int
    date: str
    side: str          # BUY | SELL | STOP
    price: float
    zone: dict = field(default_factory=dict)


# ── 데이터 불러오기 ────────────────────────────────────────────────────────
def load_csv(path):
    bars = []
    with open(path, newline="", encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            r = {k.strip().lower(): v for k, v in r.items()}
            bars.append(Bar(r.get("date") or r.get("날짜"),
                            float(r.get("open") or r["시가"]),
                            float(r.get("high") or r["고가"]),
                            float(r.get("low") or r["저가"]),
                            float(r.get("close") or r["종가"]),
                            float(r.get("volume") or r.get("거래량") or 0)))
    return bars


def fetch_yahoo(code, days):
    """6자리 종목코드 → 야후 파이낸스 일봉. 코스피(.KS) 먼저, 없으면 코스닥(.KQ)."""
    import datetime as dt
    rng = "10y" if days > 1800 else "5y" if days > 700 else "2y"
    symbols = [code] if "." in code else [f"{code}.KS", f"{code}.KQ"]
    last_err = None
    for sym in symbols:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}?range={rng}&interval=1d"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            data = json.load(urllib.request.urlopen(req, timeout=20))
            res = data["chart"]["result"][0]
            q = res["indicators"]["quote"][0]
            bars = []
            for i, ts in enumerate(res["timestamp"]):
                o, h, l, c = q["open"][i], q["high"][i], q["low"][i], q["close"][i]
                if None in (o, h, l, c):
                    continue
                d = dt.datetime.utcfromtimestamp(ts + 9 * 3600).strftime("%Y-%m-%d")
                bars.append(Bar(d, o, h, l, c, q["volume"][i] or 0))
            if bars:
                return bars[-days:], sym
        except Exception as e:  # noqa: BLE001
            last_err = e
    raise RuntimeError(f"{code} 데이터를 가져오지 못했습니다: {last_err}")


def demo_bars(n=600, seed=7):
    """인터넷 없이 테스트할 수 있는 가상 주가 (급등·급락 구간 포함)."""
    rnd = random.Random(seed)
    bars, p = [], 50000.0
    for i in range(n):
        drift = 0.0
        if i % 90 in range(40, 44):
            drift = 0.045        # 급등 구간
        elif i % 90 in range(70, 73):
            drift = -0.04        # 급락 구간
        o = p
        c = max(1000, o * (1 + drift + rnd.gauss(0, 0.015)))
        h = max(o, c) * (1 + abs(rnd.gauss(0, 0.006)))
        l = min(o, c) * (1 - abs(rnd.gauss(0, 0.006)))
        bars.append(Bar(f"D{i:04d}", round(o), round(h), round(l), round(c), 0))
        p = c
    return bars


# ── 핵심 로직 ──────────────────────────────────────────────────────────────
def find_zones(bars, p):
    """급등 직전 마지막 음봉 = 지지, 급락 직전 마지막 양봉 = 저항."""
    zones, k = [], p["surge_bars"]
    for i in range(1, len(bars) - k):
        base = bars[i - 1].close
        move = (bars[i + k - 1].close - base) / base * 100
        if move >= p["surge_pct"]:
            for j in range(i - 1, max(-1, i - 11), -1):   # 직전 10개 안에서 마지막 음봉
                if bars[j].close < bars[j].open:
                    zones.append(Zone("support", j, bars[j].date, bars[j].low, bars[j].high))
                    break
        elif move <= -p["drop_pct"]:
            for j in range(i - 1, max(-1, i - 11), -1):   # 직전 10개 안에서 마지막 양봉
                if bars[j].close > bars[j].open:
                    zones.append(Zone("resistance", j, bars[j].date, bars[j].low, bars[j].high))
                    break
    # 같은 캔들이 중복으로 잡히는 것 제거
    uniq = {}
    for z in zones:
        uniq[(z.kind, z.idx)] = z
    return sorted(uniq.values(), key=lambda z: z.idx)


def run(bars, p):
    """구간 탐지 → 매수/매도/손절 신호를 시간순으로 생성 (미래 데이터 사용 안 함)."""
    zones = find_zones(bars, p)
    n, k = p["break_n"], p["surge_bars"]
    signals, pos = [], None     # pos = 매수 때 쓴 지지 구간
    for i in range(n, len(bars)):
        b = bars[i]
        # 구간은 급등/급락이 '확인된 뒤'부터만 사용 (기준 캔들 + 급등 캔들 수)
        live = [z for z in zones if z.idx + k + 1 <= i and i - z.idx <= p["zone_life"] + k
                and not z.used and not z.broken]
        prev = bars[i - n:i]
        for z in live:
            if b.low <= z.high and b.high >= z.low:
                z.touched_at = i
        if pos is None:
            for z in (z for z in live if z.kind == "support"):
                recent_touch = z.touched_at >= 0 and i - z.touched_at <= p["touch_window"]
                if recent_touch and b.close > max(x.high for x in prev) and b.close >= z.low:
                    signals.append(Signal(i, b.date, "BUY", b.close, asdict(z)))
                    z.used, pos = True, z
                    break
        else:
            if b.close < pos.low:
                signals.append(Signal(i, b.date, "STOP", b.close, asdict(pos)))
                pos = None
                continue
            for z in (z for z in live if z.kind == "resistance" and z.low > pos.high):
                recent_touch = z.touched_at >= 0 and i - z.touched_at <= p["touch_window"]
                if recent_touch and b.close < min(x.low for x in prev):
                    signals.append(Signal(i, b.date, "SELL", b.close, asdict(z)))
                    z.used, pos = True, None
                    break
        for z in live:   # 종가로 구간이 뚫리면 이후엔 쓰지 않음
            if (z.kind == "support" and b.close < z.low) or (z.kind == "resistance" and b.close > z.high):
                z.broken = True
    return zones, signals


FEE = 0.25  # 왕복 수수료+세금 가정(%)


def backtest(bars, p):
    _, sigs = run(bars, p)
    trades, entry = [], None
    for s in sigs:
        if s.side == "BUY":
            entry = s
        elif entry:
            ret = (s.price - entry.price) / entry.price * 100 - FEE
            trades.append(dict(buy=entry.date, buy_px=entry.price, sell=s.date,
                               sell_px=s.price, exit=s.side, ret=round(ret, 2),
                               hold=s.idx - entry.idx))
            entry = None
    eq, peak, mdd = 1.0, 1.0, 0.0
    for t in trades:
        eq *= 1 + t["ret"] / 100
        peak = max(peak, eq)
        mdd = min(mdd, (eq - peak) / peak * 100)
    wins = [t for t in trades if t["ret"] > 0]
    bh = (bars[-1].close - bars[0].close) / bars[0].close * 100 if bars else 0
    return dict(trades=len(trades), win_rate=round(len(wins) / len(trades) * 100, 1) if trades else 0,
                total_ret=round((eq - 1) * 100, 1), mdd=round(mdd, 1),
                avg_ret=round(sum(t["ret"] for t in trades) / len(trades), 2) if trades else 0,
                buy_hold=round(bh, 1), open_position=bool(entry),
                open_entry=asdict(entry) if entry else None, detail=trades)


GRID = dict(surge_pct=[6, 8, 10, 12, 15], drop_pct=[5, 7, 9, 12],
            surge_bars=[2, 3, 5], break_n=[2, 3, 4])


def optimize(series, base):
    """앞 70%로 값을 고르고 뒤 30%로 검증 → 과최적화 여부 확인."""
    rows = []
    for combo in itertools.product(*GRID.values()):
        p = dict(base, **dict(zip(GRID.keys(), combo)))
        tr_ret, te_ret, tr_n, te_n = 0.0, 0.0, 0, 0
        for bars in series:
            cut = int(len(bars) * 0.7)
            a, b = backtest(bars[:cut], p), backtest(bars[cut:], p)
            tr_ret += a["total_ret"]; te_ret += b["total_ret"]
            tr_n += a["trades"]; te_n += b["trades"]
        if tr_n >= 3 * len(series) // 2 + 1:          # 거래 너무 적은 조합 제외
            rows.append(dict(params={k: p[k] for k in GRID}, train_ret=round(tr_ret / len(series), 1),
                             test_ret=round(te_ret / len(series), 1), train_trades=tr_n, test_trades=te_n))
    rows.sort(key=lambda r: r["train_ret"], reverse=True)
    return rows[:10]


# ── 출력 ──────────────────────────────────────────────────────────────────
def current_state(bars, p):
    zones, sigs = run(bars, p)
    last = bars[-1]
    live = [z for z in zones if len(bars) - 1 - z.idx <= p["zone_life"] + p["surge_bars"] and not z.broken]
    sup = [z for z in live if z.kind == "support" and z.high <= last.close * 1.02]
    res = [z for z in live if z.kind == "resistance" and z.low >= last.close * 0.98]
    near_sup = max(sup, key=lambda z: z.high, default=None)
    near_res = min(res, key=lambda z: z.low, default=None)
    last_sig = sigs[-1] if sigs else None
    fresh = last_sig and last_sig.idx >= len(bars) - 3
    holding = bool(last_sig and last_sig.side == "BUY")
    if fresh:
        status = f"🔔 {last_sig.side} 신호 ({last_sig.date}, {last_sig.price:,.0f})"
    elif holding:
        status = f"보유 구간 (매수 {last_sig.date} @ {last_sig.price:,.0f})"
    elif near_sup and last.low <= near_sup.high * 1.03:
        status = "👀 지지 구간 근접 — 3캔들 돌파 대기"
    else:
        status = "관망"
    return dict(date=last.date, close=last.close, status=status,
                support=asdict(near_sup) if near_sup else None,
                resistance=asdict(near_res) if near_res else None,
                last_signal=asdict(last_sig) if last_sig else None)


def fmt_zone(z):
    return f"{z['low']:,.0f} ~ {z['high']:,.0f} ({z['date']})" if z else "-"


def get_series(args):
    if args.csv:
        return [(args.csv, load_csv(args.csv))]
    if getattr(args, "cmd", "") == "demo":
        return [("DEMO", demo_bars())]
    out = []
    for code in args.codes:
        try:
            bars, sym = fetch_yahoo(code, args.days)
            out.append((sym, bars))
        except RuntimeError as e:
            print(f"⚠️  {e}", file=sys.stderr)
    return out


def main():
    ap = argparse.ArgumentParser(description="오더블록 지지·저항 신호 스캐너")
    ap.add_argument("cmd", choices=["scan", "backtest", "optimize", "demo"])
    ap.add_argument("codes", nargs="*", help="6자리 종목코드 (예: 005930)")
    ap.add_argument("--csv", help="CSV 파일 경로")
    ap.add_argument("--days", type=int, default=500)
    ap.add_argument("--json", action="store_true", help="JSON으로 출력")
    for k, v in DEFAULTS.items():
        ap.add_argument(f"--{k.replace('_', '-')}", type=type(v), default=v)
    args = ap.parse_args()
    p = {k: getattr(args, k) for k in DEFAULTS}
    series = get_series(args)
    if not series:
        sys.exit("데이터가 없습니다. 종목코드 또는 --csv 를 넣어주세요.")

    if args.cmd == "optimize":
        res = optimize([b for _, b in series], p)
        if args.json:
            print(json.dumps(res, ensure_ascii=False, indent=1)); return
        print("순위 | 급등% 급락% 캔들 돌파N | 학습구간 수익% | 검증구간 수익% | 거래(학습/검증)")
        for i, r in enumerate(res, 1):
            q = r["params"]
            print(f"{i:>2}  | {q['surge_pct']:>4} {q['drop_pct']:>4} {q['surge_bars']:>4} {q['break_n']:>4}  |"
                  f" {r['train_ret']:>10} | {r['test_ret']:>10} | {r['train_trades']}/{r['test_trades']}")
        return

    out = []
    for name, bars in series:
        row = dict(name=name, **current_state(bars, p))
        if args.cmd in ("backtest", "demo"):
            row["backtest"] = backtest(bars, p)
        out.append(row)
    if args.json:
        print(json.dumps(out, ensure_ascii=False, indent=1)); return
    for r in out:
        print(f"\n■ {r['name']}  {r['date']} 종가 {r['close']:,.0f}")
        print(f"  상태      : {r['status']}")
        print(f"  지지 구간 : {fmt_zone(r['support'])}")
        print(f"  저항 구간 : {fmt_zone(r['resistance'])}")
        bt = r.get("backtest")
        if bt:
            print(f"  백테스트  : 거래 {bt['trades']}회 | 승률 {bt['win_rate']}% | 누적 {bt['total_ret']}% "
                  f"| 평균 {bt['avg_ret']}% | 최대낙폭 {bt['mdd']}% | 단순보유 {bt['buy_hold']}%")
            for t in bt["detail"][-5:]:
                print(f"    {t['buy']} {t['buy_px']:,.0f} → {t['sell']} {t['sell_px']:,.0f} "
                      f"[{t['exit']}] {t['ret']:+.2f}% ({t['hold']}일)")


if __name__ == "__main__":
    main()
