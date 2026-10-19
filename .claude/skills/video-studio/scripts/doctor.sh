#!/usr/bin/env bash
# 영상 자동화에 필요한 도구가 설치돼 있는지 점검표로 보여 준다.
# 사용법: doctor.sh [OpenMontage 폴더 경로]   (기본: ./OpenMontage, ~/OpenMontage)
set -uo pipefail
OM_HINT="${1:-}"
MISSING=0

row() { printf '| %-18s | %-4s | %s |\n' "$1" "$2" "$3"; }
ok()  { row "$1" "✅" "$2"; }
bad() { row "$1" "❌" "$2"; MISSING=$((MISSING+1)); }

ver_major() { echo "$1" | sed -E 's/^v?([0-9]+).*/\1/'; }

echo "| 도구               | 상태 | 내용 |"
echo "|--------------------|------|------|"

if command -v node >/dev/null 2>&1; then
  V=$(node -v); M=$(ver_major "$V")
  if [ "$M" -ge 22 ]; then ok "Node.js" "$V"; else bad "Node.js" "$V (22 이상 필요 — HyperFrames 요구사항)"; fi
else bad "Node.js" "없음 → https://nodejs.org (LTS 22+)"; fi

command -v npx >/dev/null 2>&1 && ok "npx" "$(npx -v 2>/dev/null)" || bad "npx" "없음 (Node.js 설치 시 같이 깔림)"

if command -v ffmpeg >/dev/null 2>&1; then
  ok "FFmpeg" "$(ffmpeg -version 2>/dev/null | head -1 | awk '{print $3}')"
else bad "FFmpeg" "없음 → 맥: brew install ffmpeg / 윈도우: winget install Gyan.FFmpeg"; fi

if command -v python3 >/dev/null 2>&1; then
  PV=$(python3 -c 'import sys;print("%d.%d"%sys.version_info[:2])')
  python3 -c 'import sys;sys.exit(0 if sys.version_info>=(3,10) else 1)' && ok "Python" "$PV" || bad "Python" "$PV (3.10 이상 필요)"
else bad "Python" "없음 → https://python.org (3.10+)"; fi

command -v git >/dev/null 2>&1 && ok "git" "$(git --version | awk '{print $3}')" || bad "git" "없음 (OpenMontage 내려받기에 필요)"
command -v claude >/dev/null 2>&1 && ok "Claude Code" "$(claude --version 2>/dev/null | head -1)" || bad "Claude Code" "없음 (야간 모드에 필요)"

# 스킬은 프로젝트(.claude/skills, .agents/skills) 또는 사용자 홈(~/.claude/skills)에 깔릴 수 있다
find_skill() {
  for base in .claude/skills .agents/skills "$HOME/.claude/skills" "$HOME/.agents/skills"; do
    [ -d "$base" ] || continue
    ls -1 "$base" 2>/dev/null | grep -i -m1 "$1" && return 0
  done
  return 1
}
S=$(find_skill remotion) && ok "Remotion 스킬" "$S" || bad "Remotion 스킬" "없음 → npx skills add remotion-dev/skills"
S=$(find_skill hyperframes) && ok "HyperFrames 스킬" "$S" || bad "HyperFrames 스킬" "없음 → npx skills add heygen-com/hyperframes --full-depth --yes"

OM=""
for d in "$OM_HINT" ./OpenMontage "$HOME/OpenMontage"; do
  [ -n "$d" ] && [ -f "$d/CLAUDE.md" ] && [ -d "$d/pipeline_defs" ] && { OM="$d"; break; }
done
if [ -n "$OM" ]; then
  if [ -d "$OM/.venv" ]; then ok "OpenMontage" "$OM (설치 완료)"; else bad "OpenMontage" "$OM 있음, 설치 미완료 → cd $OM && make setup"; fi
else bad "OpenMontage" "없음 → git clone https://github.com/calesthio/OpenMontage.git && cd OpenMontage && make setup"; fi

python3 -c 'import faster_whisper' 2>/dev/null && ok "faster-whisper" "받아쓰기 가능" || row "faster-whisper" "➖" "선택. 단어 타이밍 필요 시 pip install faster-whisper"

echo
if [ "$MISSING" -eq 0 ]; then echo "결과: 모두 준비됨 ✅"; else echo "결과: ${MISSING}개 부족 ❌ → bash $(dirname "$0")/setup.sh 로 한 번에 설치"; fi
exit 0
