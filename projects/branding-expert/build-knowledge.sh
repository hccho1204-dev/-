#!/usr/bin/env bash
# 스킬의 참고 파일 4개를 Claude 프로젝트용 지식 파일 1개로 합친다.
set -euo pipefail
cd "$(dirname "$0")"
SRC="../../.claude/skills/branding-expert/references"
OUT="branding-knowledge.md"
{
  echo "# 브랜딩 전문가 지식 파일 — 노희영 「AI 시대 브랜딩 법칙」"
  echo
  echo "> 이 파일은 build-knowledge.sh로 자동 생성됨. 원본: .claude/skills/branding-expert/references/"
  for f in principles case-studies diagnosis-checklist templates; do
    echo
    echo "---"
    echo
    cat "$SRC/$f.md"
  done
} > "$OUT"
echo "생성 완료: $(pwd)/$OUT"
