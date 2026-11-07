#!/usr/bin/env bash
# 화면 녹화 영상에서 "장면이 바뀌는 순간"만 캡처한다.
# 사용법: bash extract_frames.sh <영상파일> [출력폴더] [민감도 0.0~1.0, 기본 0.08]
set -euo pipefail
IN="${1:?영상 파일 경로를 넣어 주세요}"
OUT="${2:-./frames}"
TH="${3:-0.08}"
command -v ffmpeg >/dev/null || { echo "ffmpeg가 없습니다. 스크린샷으로 대신 주세요."; exit 1; }
mkdir -p "$OUT"
# 1) 장면 전환 프레임 + 2) 최소 5초마다 1장 (변화 없는 구간 놓치지 않게)
ffmpeg -hide_banner -loglevel error -i "$IN" \
  -vf "select='gt(scene,${TH})+isnan(prev_selected_t)+gte(t-prev_selected_t,5)',scale='min(1280,iw)':-2" \
  -vsync vfr "$OUT/frame_%04d.png"
N=$(ls "$OUT"/frame_*.png 2>/dev/null | wc -l)
echo "캡처 ${N}장 → $OUT"
# 너무 많으면 민감도를 올려 다시 실행하라고 안내
if [ "$N" -gt 60 ]; then echo "장수가 많습니다. 민감도를 0.15로 올려 다시 실행해 보세요."; fi
