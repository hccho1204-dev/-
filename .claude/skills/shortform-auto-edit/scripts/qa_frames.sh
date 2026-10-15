#!/usr/bin/env bash
# 렌더 결과를 N초 간격으로 캡처하고 한 장 모아보기를 만든다 (F단계 자가 검수용)
# 사용법: qa_frames.sh <영상.mp4> <출력폴더> [간격초=2]
# 마지막 프레임(영상 끝)도 따로 저장한다 → "마지막 카드가 끝까지 남아 있나" 확인용
set -euo pipefail
IN="${1:?영상 파일 경로를 주세요}"
OUT="${2:?출력 폴더를 주세요}"
STEP="${3:-2}"
mkdir -p "$OUT"
DUR=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$IN")
ffmpeg -v error -y -i "$IN" \
  -vf "fps=1/${STEP},scale=360:-2,drawtext=text='%{pts\:hms}':x=6:y=6:fontsize=18:fontcolor=yellow:box=1:boxcolor=black@0.6" \
  "$OUT/q_%03d.jpg"
LAST=$(python3 -c "print(max(0, ${DUR} - 0.1))")
ffmpeg -v error -y -ss "$LAST" -i "$IN" -frames:v 1 -vf "scale=360:-2" "$OUT/q_last.jpg"
N=$(ls "$OUT"/q_[0-9]*.jpg | wc -l)
COLS=6
ffmpeg -v error -y -framerate 1 -i "$OUT/q_%03d.jpg" -vf "tile=${COLS}x$(( (N + COLS - 1) / COLS )):padding=4:color=gray" \
  -frames:v 1 "$OUT/sheet.jpg"
echo "검수 캡처 ${N}장 (${STEP}초 간격, 영상 ${DUR}초) → $OUT/  · 모아보기: $OUT/sheet.jpg · 마지막 장면: $OUT/q_last.jpg"
