#!/usr/bin/env bash
# 2겹 숫자 검수: 밝기 · 장면 전환 속도 · 움직임 양 · 음량 · 멈춘 화면 측정
# 사용법: measure_video.sh <영상.mp4> [톤코드] [timing.json]   (톤코드 주면 목표와 비교)
set -euo pipefail
IN="${1:?영상 파일 경로를 주세요}"
TONE="${2:-}"
TIMING="${3:-}"
DIR="$(cd "$(dirname "$0")" && pwd)"
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT

DUR=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$IN")

# 밝기(YAVG)·움직임(프레임 차이) — 분석 속도를 위해 10fps, 360px로 축소
ffmpeg -v error -i "$IN" -vf "fps=10,scale=-2:360,signalstats,metadata=print:file=$TMP/stats.txt" -f null - || true
ffmpeg -v error -i "$IN" -vf "fps=10,scale=-2:360,format=gray,tblend=all_mode=difference,signalstats,metadata=print:file=$TMP/diff.txt" -f null - || true
# 장면 전환
ffmpeg -v error -i "$IN" -vf "scale=-2:360,select='gt(scene,0.30)',metadata=print:file=$TMP/scene.txt" -f null - || true
# 멈춘 화면 (1초 이상)
ffmpeg -v info -i "$IN" -vf "freezedetect=n=0.003:d=1" -map 0:v -f null - 2> "$TMP/freeze.txt" || true
# 음량 (EBU R128)
if ffprobe -v error -select_streams a -show_entries stream=index -of csv=p=0 "$IN" | grep -q .; then
  ffmpeg -v info -i "$IN" -map 0:a -af ebur128=peak=true -f null - 2> "$TMP/loud.txt" || true
else
  : > "$TMP/loud.txt"
fi

python3 -I "$DIR/_summarize.py" "$TMP" "$DUR" "$TONE" "$TIMING"
