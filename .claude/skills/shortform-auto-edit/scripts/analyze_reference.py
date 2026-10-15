#!/usr/bin/env python3
"""레퍼런스 완성본을 숫자로 분석한다 (A단계).

사용법: python3 analyze_reference.py <ref.mp4> <ref.words.json> <출력폴더>

하는 일:
  1) 화면을 1초 간격으로 캡처 → <출력폴더>/frames/
  2) 말과 말 사이 빈틈, 말 속도(초당 글자), 컷 길이, 영상 길이 → <출력폴더>/stats.json
캡처 이미지는 AI가 직접 보고 자막·확대·모션그래픽 스타일을 적는 데 쓴다.
"""
import json
import re
import statistics as st
import subprocess
import sys
from pathlib import Path


def probe(path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0",
         "-show_entries", "stream=width,height:format=duration", "-of", "json", path],
        capture_output=True, text=True, check=True,
    ).stdout
    j = json.loads(out)
    s = j["streams"][0]
    return float(j["format"]["duration"]), s["width"], s["height"]


def scene_cuts(path, thr=0.3):
    r = subprocess.run(
        ["ffmpeg", "-hide_banner", "-i", path, "-vf", f"select='gt(scene,{thr})',showinfo", "-an", "-f", "null", "-"],
        capture_output=True, text=True,
    )
    return [float(t) for t in re.findall(r"pts_time:([0-9.]+)", r.stderr)]


def summary(xs):
    if not xs:
        return None
    xs = sorted(xs)
    return {
        "count": len(xs),
        "avg": round(st.mean(xs), 3),
        "median": round(st.median(xs), 3),
        "p90": round(xs[int(len(xs) * 0.9) - 1 if len(xs) > 1 else 0], 3),
        "max": round(xs[-1], 3),
    }


def main():
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    src, words_path, outdir = sys.argv[1:]
    out = Path(outdir)
    (out / "frames").mkdir(parents=True, exist_ok=True)

    dur, w, h = probe(src)
    subprocess.run(
        ["ffmpeg", "-v", "error", "-y", "-i", src, "-vf", "fps=1,scale=540:-2", str(out / "frames" / "f_%04d.jpg")],
        check=True,
    )

    words = json.loads(Path(words_path).read_text(encoding="utf-8"))["words"]
    gaps = [max(0.0, b["start"] - a["end"]) for a, b in zip(words, words[1:])]
    chars = sum(len(x["w"].replace(" ", "")) for x in words)
    speech = sum(x["end"] - x["start"] for x in words) + sum(gaps)

    cuts = scene_cuts(src)
    bounds = [0.0] + cuts + [dur]
    cut_lens = [b - a for a, b in zip(bounds, bounds[1:]) if b - a > 0.05]

    stats = {
        "source": src,
        "duration_sec": round(dur, 2),
        "resolution": f"{w}x{h}",
        "word_gap_sec": summary(gaps),
        "chars_per_sec": round(chars / speech, 2) if speech else None,
        "cut_count": len(cut_lens),
        "cut_len_sec": summary(cut_lens),
        "cut_times": [round(c, 2) for c in cuts],
        "frames_dir": str(out / "frames"),
    }
    (out / "stats.json").write_text(json.dumps(stats, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(stats, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
