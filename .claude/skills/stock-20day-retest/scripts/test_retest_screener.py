"""가짜 차트로 스크리너 규칙을 확인하는 테스트: python -m pytest 또는 python test_retest_screener.py"""
import pandas as pd

from retest_screener import analyze


def make(closes, vols=None):
    idx = pd.bdate_range("2026-01-01", periods=len(closes))
    return pd.DataFrame({"Open": closes, "High": [c * 1.01 for c in closes], "Low": [c * 0.99 for c in closes],
                         "Close": closes, "Volume": vols or [1000] * len(closes)}, index=idx)


BASE = [90 + (i % 5) for i in range(40)]  # 박스권: 20일 고가 = 94 * 1.01 = 94.94


def test_buy_signal_after_pullback_and_rebound():
    s = analyze(make(BASE + [100, 98, 96, 97]), "T")
    assert s and s.status.startswith("✅") and s.down_days == 2


def test_candidate_while_still_pulling_back():
    s = analyze(make(BASE + [100, 98, 96]), "T")
    assert s and s.status.startswith("🟢")


def test_waiting_right_after_breakout():
    assert analyze(make(BASE + [100]), "T").status.startswith("🔔")
    assert analyze(make(BASE + [100, 99]), "T").status.startswith("⏳")


def test_failed_retest_excluded():
    assert analyze(make(BASE + [100, 97, 93, 96]), "T") is None


def test_no_breakout():
    assert analyze(make(BASE + [93, 92]), "T") is None


if __name__ == "__main__":
    for k, f in list(globals().items()):
        if k.startswith("test_"):
            f(); print("OK", k)
