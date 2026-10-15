#!/usr/bin/env python3
"""남길 테이크(takes.json) + 단어 시간표(words.json) → 호흡 압축된 컷 목록(cutlist.json).

사용법:
  python3 make_cutlist.py words.json takes.json cutlist.json [--max-gap 0.1] [--pad 0.04] [--line-chars 14] [--min-cut 0.4]

규칙:
  - takes.json 의 각 keep 구간 안에 있는 단어만 쓴다
  - 단어 사이 쉬는 틈이 max-gap 보다 길면 거기서 잘라 붙인다 (호흡 압축)
  - 단어 앞뒤로 pad 만큼 여유를 둬서 말이 잘리지 않게 한다
  - min-cut 보다 짧은 조각은 앞 조각과 합친다 (어색한 초단컷 방지)
  - 자막은 line-chars 글자 안에서 단어를 묶고, 결과 영상 시간 기준으로 만든다
"""
import argparse
import json
from pathlib import Path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("words")
    ap.add_argument("takes")
    ap.add_argument("out")
    ap.add_argument("--max-gap", type=float, default=0.1)
    ap.add_argument("--pad", type=float, default=0.04)
    ap.add_argument("--line-chars", type=int, default=14)
    ap.add_argument("--min-cut", type=float, default=0.4)
    a = ap.parse_args()

    words = json.loads(Path(a.words).read_text(encoding="utf-8"))["words"]
    keeps = json.loads(Path(a.takes).read_text(encoding="utf-8"))["keep"]

    segs = []  # {src_start, src_end, take, words:[...]}
    for ti, k in enumerate(keeps):
        ws = [w for w in words if w["start"] >= k["start"] - 0.05 and w["end"] <= k["end"] + 0.05]
        if not ws:
            continue
        cur = {"take": ti, "words": [ws[0]]}
        for prev, w in zip(ws, ws[1:]):
            if w["start"] - prev["end"] > a.max_gap:
                segs.append(cur)
                cur = {"take": ti, "words": [w]}
            else:
                cur["words"].append(w)
        segs.append(cur)

    for s in segs:
        s["src_start"] = max(0.0, s["words"][0]["start"] - a.pad)
        s["src_end"] = s["words"][-1]["end"] + a.pad

    merged = []
    for s in segs:
        if merged and merged[-1]["take"] == s["take"] and s["src_end"] - s["src_start"] < a.min_cut:
            m = merged[-1]
            m["src_end"] = s["src_end"]
            m["words"] += s["words"]
        else:
            merged.append(s)

    # 결과 영상 타임라인 계산 + 자막 만들기
    t = 0.0
    cuts, subs = [], []
    line, line_start, line_end = "", None, None

    def flush():
        nonlocal line, line_start, line_end
        if line:
            subs.append({"start": round(line_start, 3), "end": round(line_end, 3), "text": line.strip()})
        line, line_start, line_end = "", None, None

    prev_take = None
    for s in merged:
        if prev_take is not None and s["take"] != prev_take:
            flush()  # 테이크가 바뀌면 자막도 새 줄로
        offset = t - s["src_start"]
        for w in s["words"]:
            cand = (line + " " + w["w"]).strip()
            if line and len(cand.replace(" ", "")) > a.line_chars:
                flush()
                cand = w["w"]
            if line_start is None:
                line_start = w["start"] + offset
            line = cand
            line_end = w["end"] + offset
        length = s["src_end"] - s["src_start"]
        cuts.append({"src_start": round(s["src_start"], 3), "src_end": round(s["src_end"], 3),
                     "out_start": round(t, 3), "take": s["take"]})
        t += length
        prev_take = s["take"]
    flush()

    # 자막이 다음 자막과 겹치지 않게, 너무 짧게 깜빡이지 않게 정리
    for cur, nxt in zip(subs, subs[1:]):
        cur["end"] = min(max(cur["end"], cur["start"] + 0.5), nxt["start"])

    data = {"total_sec": round(t, 3), "cuts": cuts, "subtitles": subs}
    Path(a.out).write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    raw = words[-1]["end"] if words else 0
    print(f"컷 {len(cuts)}개 · 자막 {len(subs)}개 · 완성 길이 {t:.1f}초 (원본 말 끝 {raw:.1f}초) → {a.out}")


if __name__ == "__main__":
    main()
