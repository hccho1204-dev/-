#!/usr/bin/env python3
"""한국 시장(코스피+코스닥) 전 종목 시세를 받아 scan.py 입력(prices.json)을 만든다.

인터넷이 되는 PC나 GitHub Actions에서 실행:
  pip install pykrx
  python3 fetch_kr.py prices_kr.json
"""
import json
import sys
from datetime import date, timedelta

from pykrx import stock

DAYS = 25  # 최근 25거래일

end = date.today()
days = []
d = end
while len(days) < DAYS and (end - d).days < 60:
    ds = d.strftime("%Y%m%d")
    df = stock.get_market_ohlcv_by_ticker(ds, market="ALL")
    if not df.empty and df["거래량"].sum() > 0:
        days.append((d.isoformat(), df))
    d -= timedelta(days=1)
days.reverse()

out = {}
for iso, df in days:
    for tk, row in df.iterrows():
        if row["종가"] <= 0:
            continue
        e = out.setdefault(tk, {"name": "", "note": "", "bars": []})
        e["bars"].append([iso, float(row["시가"]), float(row["고가"]), float(row["저가"]),
                          float(row["종가"]), float(row["거래량"])])

# 최근 급등 이력이 있는 종목만 남기고 이름 채우기
keep = {}
for tk, e in out.items():
    c = [b[4] for b in e["bars"]]
    if any(c[i - 1] and c[i] / c[i - 1] >= 1.2 for i in range(1, len(c))):
        e["name"] = stock.get_market_ticker_name(tk)
        keep[tk] = e

json.dump(keep, open(sys.argv[1], "w", encoding="utf-8"), ensure_ascii=False)
print(f"{len(keep)}개 급등 이력 종목 저장 → {sys.argv[1]}")
