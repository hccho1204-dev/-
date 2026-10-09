"""measure_video.sh 결과 요약 + 톤 목표 비교 (직접 실행하지 않음)"""
import json, os, re, sys

tmp, dur, tone = sys.argv[1], float(sys.argv[2]), sys.argv[3]

def read(name):
    p = os.path.join(tmp, name)
    return open(p, encoding="utf-8", errors="ignore").read() if os.path.exists(p) else ""

def avg(vals):
    return sum(vals) / len(vals) if vals else None

yavg = [float(x) for x in re.findall(r"lavfi\.signalstats\.YAVG=([\d.]+)", read("stats.txt"))]
diff = [float(x) for x in re.findall(r"lavfi\.signalstats\.YAVG=([\d.]+)", read("diff.txt"))]
cuts = len(re.findall(r"lavfi\.scene_score=", read("scene.txt")))

freezes = [float(x) for x in re.findall(r"freeze_duration:\s*([\d.]+)", read("freeze.txt"))]
loud = read("loud.txt")
summary = loud.split("Summary:")[-1] if "Summary:" in loud else ""
lufs = re.search(r"I:\s*(-?[\d.]+)\s*LUFS", summary)
peak = re.search(r"Peak:\s*(-?[\d.]+)\s*dBFS", summary)

r = {
    "duration": round(dur, 2),
    "brightness": round(avg(yavg) / 255, 3) if yavg else None,
    "shot_sec": round(dur / (cuts + 1), 2),
    "cuts": cuts,
    "motion": round(avg(diff) / 255 * 100, 2) if diff else None,
    "loudness": float(lufs.group(1)) if lufs else None,
    "true_peak": float(peak.group(1)) if peak else None,
    "freeze_max": round(max(freezes), 2) if freezes else 0.0,
}

print(json.dumps(r, ensure_ascii=False, indent=2))

# 톤 목표 비교 (tone-cards.md의 '목표 숫자' 줄을 읽는다)
if tone:
    cards = open(os.path.join(os.path.dirname(__file__), "..", "references", "tone-cards.md"), encoding="utf-8").read()
    m = re.search(rf"## {re.escape(tone)} .*?목표 숫자:([^\n]+)", cards, re.S)
    if not m:
        sys.exit(f"\n톤 코드 {tone}의 목표 숫자를 찾지 못했습니다.")
    line = m.group(1)
    print(f"\n[톤 {tone} 목표 비교]")
    fails = 0
    def rng(key):
        mm = re.search(rf"{key}\s+(-?[\d.]+)(?:~(-?[\d.]+)|±([\d.]+))?", line)
        if not mm: return None
        a = float(mm.group(1))
        if mm.group(2): return a, float(mm.group(2))
        if mm.group(3): return a - float(mm.group(3)), a + float(mm.group(3))
        return a, a
    for key in ("brightness", "motion", "loudness"):
        t, v = rng(key), r[key]
        if t is None or v is None: continue
        ok = t[0] <= v <= t[1]; fails += not ok
        print(f"  {key:11s} {v:>8} 목표 {t[0]}~{t[1]}  {'✅' if ok else '❌ 톤 이탈'}")
    t = rng("shot_sec")
    if t:
        lo, hi = t[0] * 0.7, t[0] * 1.3
        ok = lo <= r["shot_sec"] <= hi; fails += not ok
        print(f"  {'shot_sec':11s} {r['shot_sec']:>8} 목표 {t[0]} (±30%: {lo:.2f}~{hi:.2f})  {'✅' if ok else '❌ 장면 속도 이탈'}")
    if r["true_peak"] is not None and r["true_peak"] > -1:
        print(f"  {'true_peak':11s} {r['true_peak']:>8} 기준 -1 이하  ❌"); fails += 1
    if r["freeze_max"] > 1:
        print(f"  {'freeze_max':11s} {r['freeze_max']:>8} 1초 초과 멈춘 화면  ⚠️ 경고")
    print(f"\n판정: {'통과' if fails == 0 else f'{fails}개 항목 이탈 — 수정 필요'}")
