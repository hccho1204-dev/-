#!/usr/bin/env bash
# 야간 모드: 작업 파일(.md)을 하나씩 꺼내 Claude Code를 사람 없이 실행한다.
# 사용법: night_queue.sh [작업 폴더=night/jobs] [작업당 제한시간(분)=90]
# 결과: night/logs/<작업>.log, night/report.md, 끝난 작업은 night/done/ 으로 이동
set -uo pipefail
JOBS="${1:-night/jobs}"
LIMIT_MIN="${2:-90}"
ROOT="$(dirname "$JOBS")"
LOGS="$ROOT/logs"; DONE="$ROOT/done"; REPORT="$ROOT/report.md"
mkdir -p "$LOGS" "$DONE"

command -v claude >/dev/null || { echo "claude 명령이 없습니다 (Claude Code 설치 필요)"; exit 1; }
shopt -s nullglob
FILES=("$JOBS"/*.md)
[ ${#FILES[@]} -gt 0 ] || { echo "$JOBS 에 작업 파일(.md)이 없습니다"; exit 1; }

# 맥: 작업 중 잠자기 방지
KEEP=""
command -v caffeinate >/dev/null && { caffeinate -dimsu & KEEP=$!; }
trap '[ -n "$KEEP" ] && kill "$KEEP" 2>/dev/null' EXIT

TIMEOUT=""
command -v timeout >/dev/null && TIMEOUT="timeout ${LIMIT_MIN}m"
command -v gtimeout >/dev/null && TIMEOUT="gtimeout ${LIMIT_MIN}m"

{
  echo "# 야간 작업 보고서 — $(date '+%Y-%m-%d %H:%M') 시작"
  echo
  echo "| # | 작업 | 결과 | 걸린 시간 | 로그 |"
  echo "|---|---|---|---|---|"
} > "$REPORT"

N=0; RAN=()
for f in "${FILES[@]}"; do
  N=$((N+1)); NAME="$(basename "$f" .md)"; LOG="$LOGS/$NAME.log"; RAN+=("$NAME")
  echo "▶ [$N/${#FILES[@]}] $NAME"
  START=$(date +%s)
  PROMPT="video-studio 스킬을 사용해서 아래 야간 작업을 처음부터 끝까지 혼자 완료해. 사람에게 질문하지 말고, 애매하면 작업 파일의 기본값을 따르고 결정한 내용을 결과 요약에 적어. 업로드는 작업 파일에 'upload: public' 이 있을 때만 공개로 하고, 그 외에는 out/upload/ 에 업로드 준비까지만 해. 마지막 출력은 '결과:' 로 시작하는 5줄 이내 요약(최종 파일 경로·검수 결과·사람이 확인할 것)으로 끝내.

---
$(cat "$f")"
  $TIMEOUT claude -p "$PROMPT" --permission-mode acceptEdits --output-format text > "$LOG" 2>&1
  CODE=$?
  SEC=$(( $(date +%s) - START ))
  if [ $CODE -eq 0 ]; then RES="✅ 완료"; mv "$f" "$DONE/"
  elif [ $CODE -eq 124 ]; then RES="⏰ 시간 초과(${LIMIT_MIN}분)"
  else RES="❌ 실패(코드 $CODE)"; fi
  echo "| $N | $NAME | $RES | $((SEC/60))분 $((SEC%60))초 | logs/$NAME.log |" >> "$REPORT"
done

{
  echo
  echo "## 작업별 요약"
  for NAME in "${RAN[@]}"; do
    echo; echo "### $NAME"
    if grep -q '^결과:' "$LOGS/$NAME.log"; then grep -A5 '^결과:' "$LOGS/$NAME.log" | head -6; else tail -5 "$LOGS/$NAME.log"; fi
  done
  echo; echo "_끝난 시각: $(date '+%Y-%m-%d %H:%M')_"
} >> "$REPORT"

echo "완료 → $REPORT"
