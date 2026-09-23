#!/usr/bin/env python3
"""20일 신고가 리테스트 스크리너 (캔디스 라우 전략).

규칙
  1) 돌파: 종가가 직전 20거래일 최고가(돌파 기준가 L)를 넘어선 날 = 돌파일
  2) 조정: 돌파 후 하락 마감한 날이 min_pullback일(기본 2일) 이상
  3) 방어: 돌파 이후 모든 종가가 L 이상 (tolerance 만큼 허용)
  4) 매수: 1~3 충족 → 매수 후보, 오늘 반등(종가 상승)까지 나오면 매수 신호

사용 예
  python retest_screener.py --market kr --top 300
  python retest_screener.py --market us
  python retest_screener.py --tickers 005930 000660 NVDA AAPL
  python retest_screener.py --csv-dir ./data     # Date,Open,High,Low,Close,Volume CSV
"""
from __future__ import annotations

import argparse
import datetime as dt
import glob
import os
import sys
from dataclasses import dataclass

import pandas as pd

US_UNIVERSE = (
    "AAPL MSFT NVDA AMZN GOOGL META AVGO TSLA BRK-B LLY JPM V UNH XOM MA JNJ PG HD COST "
    "ABBV MRK ORCL CVX NFLX CRM BAC KO AMD PEP TMO WMT ADBE LIN MCD ACN CSCO ABT DIS WFC "
    "INTU QCOM TXN DHR IBM GE CAT AMAT VZ NOW PM AMGN ISRG UBER PFE NEE GS UNP SPGI RTX "
    "CMCSA LOW HON PGR BKNG T AXP SYK ELV BLK MS LRCX PLD SCHW TJX VRTX C BSX MU ADI PANW "
    "REGN KLAC ANET SNPS CDNS MDT PLTR CRWD SHOP ARM SMCI MRVL COIN DELL APP"
).split()


@dataclass
class Signal:
    ticker: str
    name: str
    status: str
    breakout_date: str
    level: float        # 돌파 기준가 (직전 20일 최고가)
    close: float
    days_after: int
    down_days: int
    dist_pct: float     # 현재가가 기준가보다 몇 % 위
    pullback_pct: float  # 돌파 후 고점 대비 조정폭
    vol_ratio: float    # 돌파일 거래량 / 직전 20일 평균
    stop: float
    target: float
    note: str


def analyze(df: pd.DataFrame, ticker: str, name: str = "", lookback: int = 20,
            max_days_after: int = 7, min_pullback: int = 2, tolerance: float = 0.0,
            stop_buffer: float = 0.03, max_dist: float = 0.10) -> Signal | None:
    """OHLCV DataFrame 하나를 검사해 신호를 돌려준다. 해당 없으면 None."""
    df = df.dropna(subset=["High", "Close"]).sort_index()
    n = len(df)
    if n < lookback + max_days_after + 2:
        return None
    high, close = df["High"].to_numpy(), df["Close"].to_numpy()
    openp = df["Open"].to_numpy() if "Open" in df else close
    vol = df["Volume"].to_numpy() if "Volume" in df else None

    def level_at(i: int) -> float:  # i일 직전 20거래일 최고가
        return float(high[i - lookback:i].max())

    # 최근 max_days_after일 안에서 가장 최근의 '새로운' 돌파일 찾기
    b = None
    for i in range(n - 1, n - 2 - max_days_after, -1):
        if close[i] > level_at(i) and not close[i - 1] > level_at(i - 1):
            b = i
            break
    if b is None:
        return None

    L = level_at(b)
    days_after = n - 1 - b
    after = close[b + 1:]
    if len(after) and after.min() < L * (1 - tolerance):
        return None  # 돌파 가격 이탈 → 실패, 제외

    down_days = int(sum(close[i] < close[i - 1] for i in range(b + 1, n)))
    peak = float(high[b:].max())
    last = float(close[-1])
    dist = last / L - 1
    pullback = 1 - last / peak
    vol_ratio = float(vol[b] / vol[b - lookback:b].mean()) if vol is not None and vol[b - lookback:b].mean() > 0 else float("nan")
    stop = L * (1 - stop_buffer)
    target = last + 2 * (last - stop)
    rebound = close[-1] > close[-2] and close[-1] >= openp[-1]

    notes = []
    if days_after == 0:
        status = "🔔 오늘 돌파(조정 대기)"
    elif down_days < min_pullback:
        status = "⏳ 조정 대기"
    elif rebound:
        status = "✅ 매수 신호(반등 확인)"
    else:
        status = "🟢 매수 후보(방어 중)"
    if dist > max_dist:
        notes.append(f"기준가와 {dist:.0%} 떨어져 손익비 낮음")
    if vol_ratio == vol_ratio and vol_ratio < 1.0:
        notes.append("돌파 거래량 약함")
    if vol_ratio == vol_ratio and vol_ratio >= 2.0:
        notes.append("돌파 거래량 강함")

    return Signal(ticker, name, status, str(df.index[b])[:10], L, last, days_after,
                  down_days, dist * 100, pullback * 100, vol_ratio, stop, target,
                  ", ".join(notes))


# ---------------------------------------------------------------- 데이터 수집
def _start(days: int = 120) -> str:
    return (dt.date.today() - dt.timedelta(days=days)).isoformat()


def kr_universe(top: int) -> list[tuple[str, str]]:
    import FinanceDataReader as fdr
    lst = fdr.StockListing("KRX")
    lst = lst[lst["Market"].isin(["KOSPI", "KOSDAQ", "KOSDAQ GLOBAL"])]
    lst = lst.sort_values("Marcap", ascending=False).head(top)
    return list(zip(lst["Code"], lst["Name"]))


def load_kr(code: str) -> pd.DataFrame:
    try:
        import FinanceDataReader as fdr
        return fdr.DataReader(code, _start())
    except Exception:
        pass
    try:
        from pykrx import stock
        d = stock.get_market_ohlcv(_start().replace("-", ""), dt.date.today().strftime("%Y%m%d"), code)
        return d.rename(columns={"시가": "Open", "고가": "High", "저가": "Low", "종가": "Close", "거래량": "Volume"})
    except Exception:
        pass
    import yfinance as yf
    for sfx in (".KS", ".KQ"):
        d = yf.Ticker(code + sfx).history(start=_start(), auto_adjust=False)
        if len(d):
            return d
    return pd.DataFrame()


def load_us(ticker: str) -> pd.DataFrame:
    import yfinance as yf
    return yf.Ticker(ticker).history(start=_start(), auto_adjust=False)


def load_csv_dir(path: str):
    for f in sorted(glob.glob(os.path.join(path, "*.csv"))):
        d = pd.read_csv(f, parse_dates=["Date"], index_col="Date")
        yield os.path.splitext(os.path.basename(f))[0], d


# ---------------------------------------------------------------- 출력
ORDER = ["✅", "🟢", "⏳", "🔔"]


def fmt_price(x: float) -> str:
    return f"{x:,.0f}" if x >= 1000 else f"{x:,.2f}"


def render(signals: list[Signal], scanned: int) -> str:
    signals.sort(key=lambda s: (ORDER.index(s.status[0]), s.dist_pct))
    out = [f"# 20일 신고가 리테스트 스캔 결과 ({dt.date.today()})",
           f"검사 종목 {scanned}개 → 해당 {len(signals)}개\n"]
    if not signals:
        out.append("조건에 맞는 종목이 없습니다. (--max-days-after 를 늘리거나 --tolerance 를 0.01 정도로 완화해 보세요)")
        return "\n".join(out)
    out.append("| 상태 | 종목 | 돌파일 | 돌파 기준가 | 현재가 | 기준가 대비 | 돌파 후 경과 | 조정일수 | 돌파 거래량 | 손절가 | 1차 목표 | 메모 |")
    out.append("|---|---|---|---|---|---|---|---|---|---|---|---|")
    for s in signals:
        label = f"{s.name}({s.ticker})" if s.name else s.ticker
        vr = f"{s.vol_ratio:.1f}배" if s.vol_ratio == s.vol_ratio else "-"
        out.append(f"| {s.status} | {label} | {s.breakout_date} | {fmt_price(s.level)} | {fmt_price(s.close)} | "
                   f"+{s.dist_pct:.1f}% | {s.days_after}일 | {s.down_days}일 | {vr} | {fmt_price(s.stop)} | "
                   f"{fmt_price(s.target)} | {s.note} |")
    return "\n".join(out)


def main() -> None:
    p = argparse.ArgumentParser(description="20일 신고가 리테스트 스크리너")
    p.add_argument("--market", choices=["kr", "us", "all"], help="kr=한국 시총 상위, us=미국 대형주")
    p.add_argument("--top", type=int, default=300, help="한국 시총 상위 몇 종목 검사 (기본 300)")
    p.add_argument("--tickers", nargs="*", default=[], help="직접 지정 (숫자 6자리=한국, 그 외=미국)")
    p.add_argument("--csv-dir", help="OHLCV CSV 폴더")
    p.add_argument("--lookback", type=int, default=20)
    p.add_argument("--max-days-after", type=int, default=7, help="돌파 후 며칠 이내 종목까지 볼지")
    p.add_argument("--min-pullback", type=int, default=2, help="필요한 조정(하락 마감) 일수")
    p.add_argument("--tolerance", type=float, default=0.0, help="기준가 아래 허용 폭 (0.01=1%%)")
    p.add_argument("--stop-buffer", type=float, default=0.03, help="손절가 = 기준가 x (1-값)")
    p.add_argument("--only-buy", action="store_true", help="매수 신호/후보만 표시")
    a = p.parse_args()

    kw = dict(lookback=a.lookback, max_days_after=a.max_days_after, min_pullback=a.min_pullback,
              tolerance=a.tolerance, stop_buffer=a.stop_buffer)
    jobs = []  # (ticker, name, loader)
    if a.csv_dir:
        for t, d in load_csv_dir(a.csv_dir):
            jobs.append((t, "", lambda d=d: d))
    for t in a.tickers:
        loader = load_kr if t.isdigit() else load_us
        jobs.append((t, "", lambda t=t, f=loader: f(t)))
    if a.market in ("kr", "all"):
        for code, name in kr_universe(a.top):
            jobs.append((code, name, lambda c=code: load_kr(c)))
    if a.market in ("us", "all"):
        for t in US_UNIVERSE:
            jobs.append((t, "", lambda t=t: load_us(t)))
    if not jobs:
        p.error("--market, --tickers, --csv-dir 중 하나는 지정해야 합니다")

    signals, failed = [], []
    for i, (t, name, load) in enumerate(jobs, 1):
        try:
            s = analyze(load(), t, name, **kw)
            if s:
                signals.append(s)
        except Exception as e:  # 네트워크 등 개별 실패는 건너뜀
            failed.append(f"{t}({type(e).__name__})")
        if i % 50 == 0:
            print(f"... {i}/{len(jobs)} 검사", file=sys.stderr)
    if a.only_buy:
        signals = [s for s in signals if s.status[0] in "✅🟢"]
    print(render(signals, len(jobs)))
    if failed:
        print(f"\n데이터 수집 실패 {len(failed)}개: {' '.join(failed[:20])}")


if __name__ == "__main__":
    main()
