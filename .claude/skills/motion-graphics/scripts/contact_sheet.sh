#!/usr/bin/env bash
# 영상 전체를 균등 간격 24장으로 뽑아 6x4 한 장에 깐다 (1겹 눈 검수용)
# 사용법: contact_sheet.sh <영상.mp4> [출력.png]
set -euo pipefail
IN="${1:?영상 파일 경로를 주세요}"
OUT="${2:-contact_sheet.png}"
N=24
DUR=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$IN")
FPS=$(python3 -c "print(${N}/${DUR})")
mkdir -p "$(dirname "$OUT")"
ffmpeg -v error -y -i "$IN" \
  -vf "fps=${FPS},scale=480:-2,drawtext=text='%{pts\:hms}':x=8:y=8:fontsize=20:fontcolor=yellow:box=1:boxcolor=black@0.6,tile=6x4:padding=4:color=gray" \
  -frames:v 1 "$OUT"
echo "콘택트시트 저장: $OUT (${N}장, 영상 ${DUR}초)"
