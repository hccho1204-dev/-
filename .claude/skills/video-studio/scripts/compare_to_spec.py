#!/usr/bin/env python3
"""완성본을 다시 해부해서 레퍼런스 VIDEO_SPEC.json의 숫자와 비교한다.

사용법: compare_to_spec.py <레퍼런스 VIDEO_SPEC.json> <완성본.mp4> [--tolerance 0.30]
차이가 허용 범위(기본 ±30%)를 넘는 항목은 ❌로 표시하고 종료 코드 1을 돌려준다.
"""
import argparse
import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from decode_reference import decode  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("spec")
    ap.add_argument("video")
    ap.add_argument("--tolerance", type=float, default=0.30)
    a = ap.parse_args()

    with open(a.spec, encoding="utf-8") as f:
        ref = json.load(f)["measured"]
    with tempfile.TemporaryDirectory() as tmp:
        got = decode(a.video, tmp, images=False)["measured"]

    rows, fails = [], 0
    for key, label in [("shot_sec_mean", "평균 컷 길이(초)"), ("cuts_per_min", "분당 컷 수"),
                       ("brightness_mean", "밝기"), ("motion_mean", "움직임")]:
        r, g = ref.get(key), got.get(key)
        if not r or g is None:
            rows.append((label, r, g, "-", "➖"))
            continue
        d = (g - r) / r
        ok = abs(d) <= a.tolerance
        fails += not ok
        rows.append((label, r, g, f"{d:+.0%}", "✅" if ok else "❌"))

    ra, ga = (ref.get("audio") or {}).get("integrated_lufs"), (got.get("audio") or {}).get("integrated_lufs")
    if ra is not None and ga is not None:
        ok = abs(ga - ra) <= 2.0
        fails += not ok
        rows.append(("음량(LUFS)", ra, ga, f"{ga - ra:+.1f}dB", "✅" if ok else "❌"))
    peak = (got.get("audio") or {}).get("true_peak_dbtp")
    if peak is not None:
        ok = peak <= -1.0
        fails += not ok
        rows.append(("피크(dBTP, -1 이하)", "-", peak, "-", "✅" if ok else "❌"))
    if ref.get("aspect") != got.get("aspect"):
        fails += 1
        rows.append(("화면 방향", ref.get("aspect"), got.get("aspect"), "다름", "❌"))

    print("| 항목 | 레퍼런스 | 완성본 | 차이 | 판정 |")
    print("|---|---|---|---|---|")
    for r in rows:
        print("| " + " | ".join(str(x) for x in r) + " |")
    print(f"\n결과: {'통과 ✅' if not fails else f'{fails}개 항목 수정 필요 ❌'} (허용 ±{a.tolerance:.0%}, 음량 ±2dB)")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
