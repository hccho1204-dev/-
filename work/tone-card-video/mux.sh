#!/usr/bin/env bash
# 조각 영상 4개 이어 붙이기 + 목소리 합치기 → out/final.mp4
set -euo pipefail
cd "$(dirname "$0")"
printf "file 'chunks/c%d.mp4'\n" 0 1 2 3 > out/list.txt
ffmpeg -v error -y -f concat -safe 0 -i out/list.txt -i voice.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -movflags +faststart -shortest out/final.mp4
ffprobe -v error -show_entries format=duration,size -of default=nw=1 out/final.mp4
