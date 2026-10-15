#!/usr/bin/env python3
"""cutlist.json 대로 원본을 잘라 붙이고, 테이크마다 확대를 번갈아 주고, 자막을 입힌다.

사용법:
  python3 render_cut.py 원본.mp4 cutlist.json cut.mp4
      [--zooms 1.2,1.4] [--font "Noto Sans CJK KR"] [--font-size 80] [--y 0.55]
      [--width 1080 --height 1920] [--speed 1.0] [--no-subs]

  --zooms     테이크가 바뀔 때마다 이 배율을 차례로 번갈아 쓴다 (전환 효과 없이 바로 컷)
  --font-size 1080 너비 기준 px
  --y         자막 세로 위치 (화면 높이 비율, 0.55 = 55% 지점)
  --speed     배속 (사용자가 OK했을 때만. 예: 1.08)
"""
import argparse
import json
import subprocess
import tempfile
from pathlib import Path


def ass_time(t):
    t = max(0.0, t)
    h, r = divmod(t, 3600)
    m, s = divmod(r, 60)
    return f"{int(h)}:{int(m):02d}:{s:05.2f}"


def write_ass(subs, path, w, h, font, size, y_ratio, speed):
    margin_v = int(h * (1 - y_ratio))  # 아래 기준 여백 → 글자 아랫선이 y 지점
    head = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {w}
PlayResY: {h}
WrapStyle: 2

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Main,{font},{size},&H00FFFFFF,&H00FFFFFF,&H64000000,&H78000000,1,0,0,0,100,100,0,0,1,2,4,2,40,40,{margin_v},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    pop = r"{\fscx70\fscy70\t(0,90,\fscx112\fscy112)\t(90,180,\fscx100\fscy100)\blur3}"  # 팝(뽀잉) 등장
    lines = [
        f"Dialogue: 0,{ass_time(s['start'] / speed)},{ass_time(s['end'] / speed)},Main,,0,0,0,,{pop}{s['text']}"
        for s in subs
    ]
    Path(path).write_text(head + "\n".join(lines) + "\n", encoding="utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("cutlist")
    ap.add_argument("out")
    ap.add_argument("--zooms", default="1.2,1.4")
    ap.add_argument("--font", default="Noto Sans CJK KR")
    ap.add_argument("--font-size", type=int, default=80)
    ap.add_argument("--y", type=float, default=0.55)
    ap.add_argument("--width", type=int, default=1080)
    ap.add_argument("--height", type=int, default=1920)
    ap.add_argument("--speed", type=float, default=1.0)
    ap.add_argument("--no-subs", action="store_true")
    a = ap.parse_args()

    data = json.loads(Path(a.cutlist).read_text(encoding="utf-8"))
    zooms = [float(z) for z in a.zooms.split(",")]
    W, H = a.width, a.height

    parts, labels = [], []
    zi, prev_take = 0, None
    for i, c in enumerate(data["cuts"]):
        if prev_take is not None and c["take"] != prev_take:
            zi = (zi + 1) % len(zooms)
        prev_take = c["take"]
        z = zooms[zi]
        s, e = c["src_start"], c["src_end"]
        parts.append(
            f"[0:v]trim={s}:{e},setpts=PTS-STARTPTS,"
            f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},"
            f"crop=iw/{z}:ih/{z},scale={W}:{H},setsar=1[v{i}];"
            f"[0:a]atrim={s}:{e},asetpts=PTS-STARTPTS,afade=t=in:d=0.01,afade=t=out:st={max(0, e - s - 0.01):.3f}:d=0.01[a{i}];"
        )
        labels.append(f"[v{i}][a{i}]")

    fc = "".join(parts) + "".join(labels) + f"concat=n={len(labels)}:v=1:a=1[cv][ca]"
    vlast, alast = "[cv]", "[ca]"
    if a.speed != 1.0:
        fc += f";{vlast}setpts=PTS/{a.speed}[sv];{alast}atempo={a.speed}[sa]"
        vlast, alast = "[sv]", "[sa]"

    with tempfile.TemporaryDirectory() as td:
        if not a.no_subs and data.get("subtitles"):
            ass = Path(td) / "subs.ass"
            write_ass(data["subtitles"], ass, W, H, a.font, a.font_size, a.y, a.speed)
            esc = str(ass).replace("\\", "/").replace(":", r"\:")
            fc += f";{vlast}subtitles='{esc}'[fv]"
            vlast = "[fv]"
        script = Path(td) / "fc.txt"
        script.write_text(fc, encoding="utf-8")
        Path(a.out).parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(
            ["ffmpeg", "-v", "error", "-y", "-i", a.src, "-filter_complex_script", str(script),
             "-map", vlast, "-map", alast, "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
             "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", a.out],
            check=True,
        )
    total = data["total_sec"] / a.speed
    print(f"렌더 완료: {a.out} (약 {total:.1f}초, 컷 {len(labels)}개, 자막 {len(data.get('subtitles', []))}개)")


if __name__ == "__main__":
    main()
