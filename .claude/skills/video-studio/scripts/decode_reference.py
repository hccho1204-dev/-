#!/usr/bin/env python3
"""레퍼런스 영상을 숫자로 해부해 VIDEO_SPEC.json 초안을 만든다.

기계로 뽑는 것: 길이·해상도·fps, 장면 컷 시점과 길이, 장면별 대표색(HEX)·밝기·움직임,
음량(LUFS), 장면별 대표 캡처와 모아보기 1장.
자막 스타일·그래픽 종류·움직임 말투 같은 주관 요소는 비워 두고(layers),
클로드가 캡처를 직접 보고 채운다.

사용법: decode_reference.py <영상> <출력폴더> [--threshold 0.30] [--fps 4]
"""
import argparse
import json
import math
import os
import re
import subprocess
import sys

W, H = 96, 54  # 분석용 축소 크기 (빠르게)


def run(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, **kw)


def probe(path):
    out = run(["ffprobe", "-v", "error", "-print_format", "json", "-show_format", "-show_streams", path])
    if out.returncode != 0:
        sys.exit(f"ffprobe 실패: {out.stderr.strip()}")
    info = json.loads(out.stdout)
    v = next((s for s in info["streams"] if s["codec_type"] == "video"), None)
    if v is None:
        sys.exit("영상 트랙이 없습니다")
    num, den = (v.get("avg_frame_rate") or "0/1").split("/")
    fps = float(num) / float(den) if float(den) else 0.0
    return {
        "duration_sec": round(float(info["format"].get("duration", 0)), 3),
        "width": int(v["width"]),
        "height": int(v["height"]),
        "fps": round(fps, 3),
        "has_audio": any(s["codec_type"] == "audio" for s in info["streams"]),
    }


def scene_cuts(path, threshold):
    out = run(["ffmpeg", "-hide_banner", "-i", path, "-vf",
               f"scale=320:-2,select='gt(scene,{threshold})',showinfo", "-an", "-f", "null", "-"])
    return [round(float(t), 3) for t in re.findall(r"pts_time:([0-9.]+)", out.stderr)]


def sample_frames(path, fps):
    """축소한 RGB 프레임을 fps 간격으로 읽는다 → [(t, bytes)]"""
    proc = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-vf", f"fps={fps},scale={W}:{H}",
                           "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True)
    size = W * H * 3
    data = proc.stdout
    return [(i / fps, data[i * size:(i + 1) * size]) for i in range(len(data) // size)]


def luma(px):
    return sum(0.299 * px[i] + 0.587 * px[i + 1] + 0.114 * px[i + 2] for i in range(0, len(px), 3)) / (len(px) / 3) / 255


def diff(a, b):
    return sum(abs(a[i] - b[i]) for i in range(0, len(a), 3)) / (len(a) / 3) / 255


def palette(frames, k=5):
    """색을 4단계(채널당 32칸)로 묶어 많이 나온 순서대로 k개"""
    counts = {}
    for px in frames:
        for i in range(0, len(px), 3):
            key = (px[i] >> 5, px[i + 1] >> 5, px[i + 2] >> 5)
            counts[key] = counts.get(key, 0) + 1
    total = sum(counts.values()) or 1
    top = sorted(counts.items(), key=lambda x: -x[1])[:k]
    return [{"hex": "#%02X%02X%02X" % tuple(c * 32 + 16 for c in key), "share": round(n / total, 3)} for key, n in top]


def loudness(path):
    out = run(["ffmpeg", "-hide_banner", "-i", path, "-map", "0:a:0", "-af", "ebur128=peak=true", "-f", "null", "-"])
    m = re.findall(r"I:\s+(-?[0-9.]+) LUFS", out.stderr)
    p = re.findall(r"Peak:\s+(-?[0-9.]+) dBFS", out.stderr)
    return {"integrated_lufs": float(m[-1]) if m else None, "true_peak_dbtp": float(p[-1]) if p else None}


def grab(path, t, dst):
    run(["ffmpeg", "-v", "error", "-y", "-ss", f"{t:.3f}", "-i", path, "-frames:v", "1",
         "-vf", "scale=540:-2", "-q:v", "3", dst])


def contact_sheet(path, out_path, n=24):
    run(["ffmpeg", "-v", "error", "-y", "-i", path, "-vf",
         f"fps={n}/{max(probe(path)['duration_sec'], 0.1)},scale=320:-2,tile=6x4:padding=4:margin=4",
         "-frames:v", "1", "-q:v", "3", out_path])


def decode(path, out_dir, threshold=0.30, fps=4.0, images=True):
    os.makedirs(out_dir, exist_ok=True)
    meta = probe(path)
    dur = meta["duration_sec"]
    cuts = [c for c in scene_cuts(path, threshold) if 0.2 < c < dur - 0.2]
    bounds = [0.0] + cuts + [dur]
    frames = sample_frames(path, fps)

    scenes = []
    for i in range(len(bounds) - 1):
        s, e = bounds[i], bounds[i + 1]
        fr = [px for t, px in frames if s <= t < e] or [min(frames, key=lambda f: abs(f[0] - s))[1]] if frames else []
        motion = (sum(diff(fr[j], fr[j + 1]) for j in range(len(fr) - 1)) / (len(fr) - 1)) if len(fr) > 1 else 0.0
        scene = {
            "id": i + 1,
            "start": round(s, 3),
            "end": round(e, 3),
            "duration": round(e - s, 3),
            "brightness": round(sum(luma(px) for px in fr) / len(fr), 3) if fr else None,
            "motion": round(motion, 4),
            "palette": palette(fr) if fr else [],
            "keyframe": None,
            # ↓ 클로드가 캡처를 보고 채우는 칸
            "layers": [],
            "transition_out": None,
            "notes": "",
        }
        if images:
            kf = os.path.join(out_dir, f"scene_{i + 1:02d}.jpg")
            grab(path, (s + e) / 2, kf)
            scene["keyframe"] = os.path.basename(kf)
        scenes.append(scene)

    durs = [sc["duration"] for sc in scenes]
    mean = sum(durs) / len(durs)
    measured = {
        **meta,
        "aspect": "vertical" if meta["height"] > meta["width"] else ("square" if meta["height"] == meta["width"] else "horizontal"),
        "scene_count": len(scenes),
        "shot_sec_mean": round(mean, 3),
        "shot_sec_median": round(sorted(durs)[len(durs) // 2], 3),
        "shot_sec_std": round(math.sqrt(sum((d - mean) ** 2 for d in durs) / len(durs)), 3),
        "cuts_per_min": round(len(cuts) / dur * 60, 2) if dur else 0,
        "brightness_mean": round(sum(luma(px) for _, px in frames) / len(frames), 3) if frames else None,
        "motion_mean": round(sum(diff(frames[j][1], frames[j + 1][1]) for j in range(len(frames) - 1)) / max(len(frames) - 1, 1), 4) if frames else None,
        "palette_global": palette([px for _, px in frames], k=6) if frames else [],
        "audio": loudness(path) if meta["has_audio"] else None,
    }
    if images:
        contact_sheet(path, os.path.join(out_dir, "sheet.jpg"))

    spec = {
        "spec_version": 1,
        "source": os.path.abspath(path),
        "measured": measured,
        "style": {  # 클로드가 sheet.jpg·scene_*.jpg를 보고 채운다 (references/video-spec-schema.md)
            "tone_keywords": [],
            "typography": {"family_feel": "", "weight": "", "size_pct_of_height": None, "position": "", "color": "", "stroke_or_shadow": "", "max_chars_per_line": None, "entrance": ""},
            "motion_language": {"default_entrance": "", "easing": "", "speed": ""},
            "transitions": {"default": "", "continuity": ""},
            "graphics_inventory": [],
            "sound": {"bgm_mood": "", "sfx": []},
        },
        "scenes": scenes,
    }
    with open(os.path.join(out_dir, "VIDEO_SPEC.json"), "w", encoding="utf-8") as f:
        json.dump(spec, f, ensure_ascii=False, indent=2)
    return spec


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("video")
    ap.add_argument("out_dir")
    ap.add_argument("--threshold", type=float, default=0.30, help="장면 전환 민감도 (낮을수록 컷을 더 많이 잡음)")
    ap.add_argument("--fps", type=float, default=4.0, help="분석용 샘플링 fps")
    a = ap.parse_args()
    spec = decode(a.video, a.out_dir, a.threshold, a.fps)
    m = spec["measured"]
    print(f"VIDEO_SPEC.json 저장: {os.path.join(a.out_dir, 'VIDEO_SPEC.json')}")
    print(f"| 길이 {m['duration_sec']}초 | {m['width']}x{m['height']} {m['aspect']} | {m['fps']}fps |")
    print(f"| 장면 {m['scene_count']}개 | 평균 컷 {m['shot_sec_mean']}초 | 분당 컷 {m['cuts_per_min']} |")
    print(f"| 밝기 {m['brightness_mean']} | 움직임 {m['motion_mean']} | 음량 {(m['audio'] or {}).get('integrated_lufs')} LUFS |")
    print("다음: sheet.jpg와 scene_*.jpg를 보고 style·scenes[].layers를 채우세요.")


if __name__ == "__main__":
    main()
