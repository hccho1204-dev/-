#!/usr/bin/env python3
"""영상/음성을 단어 단위로 받아써서 words.json 으로 저장한다.

사용법: python3 transcribe.py <영상.mp4> <출력 words.json> [--model small] [--lang ko]

출력 형식:
{"source": "...", "duration": 237.4,
 "words": [{"w": "안녕하세요", "start": 0.52, "end": 1.10}, ...]}

faster-whisper 가 있으면 그걸 쓰고, 없으면 openai-whisper 로 시도한다.
둘 다 없으면 설치 명령을 안내하고 끝낸다.
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path


def duration_of(path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path],
        capture_output=True, text=True, check=True,
    ).stdout.strip()
    return float(out)


def with_faster_whisper(path, model, lang):
    from faster_whisper import WhisperModel
    m = WhisperModel(model, device="auto", compute_type="auto")
    segments, _ = m.transcribe(path, language=lang, word_timestamps=True, vad_filter=False)
    words = []
    for seg in segments:
        for w in seg.words or []:
            words.append({"w": w.word.strip(), "start": round(w.start, 3), "end": round(w.end, 3)})
    return words


def with_openai_whisper(path, model, lang):
    import whisper
    m = whisper.load_model(model)
    r = m.transcribe(path, language=lang, word_timestamps=True)
    words = []
    for seg in r["segments"]:
        for w in seg.get("words", []):
            words.append({"w": w["word"].strip(), "start": round(w["start"], 3), "end": round(w["end"], 3)})
    return words


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("out")
    ap.add_argument("--model", default="small")
    ap.add_argument("--lang", default="ko")
    a = ap.parse_args()

    words = None
    for fn in (with_faster_whisper, with_openai_whisper):
        try:
            words = fn(a.src, a.model, a.lang)
            break
        except ImportError:
            continue
    if words is None:
        sys.exit("받아쓰기 도구가 없습니다. 먼저 설치하세요:  pip install faster-whisper")

    words = [w for w in words if w["w"]]
    data = {"source": a.src, "duration": duration_of(a.src), "words": words}
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"받아쓰기 저장: {a.out} (단어 {len(words)}개, 길이 {data['duration']:.1f}초)")


if __name__ == "__main__":
    main()
