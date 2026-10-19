#!/usr/bin/env bash
# 없는 도구만 골라서 설치한다. (맥·리눅스용. 윈도우는 references/install-guide.md 참고)
# 사용법: setup.sh [OpenMontage 설치 위치]   (기본: ./OpenMontage)
set -uo pipefail
OM_DIR="${1:-./OpenMontage}"
FAIL=()

step() { echo; echo "▶ $1"; }

has_skill() {
  for base in .claude/skills .agents/skills "$HOME/.claude/skills" "$HOME/.agents/skills"; do
    ls -1 "$base" 2>/dev/null | grep -qi "$1" && return 0
  done
  return 1
}

# 1) 기본 도구 — 패키지 관리자가 있으면 자동, 없으면 안내만
step "FFmpeg"
if command -v ffmpeg >/dev/null; then echo "이미 있음"
elif command -v brew >/dev/null; then brew install ffmpeg || FAIL+=("ffmpeg")
elif command -v apt-get >/dev/null; then sudo apt-get install -y ffmpeg || FAIL+=("ffmpeg")
else echo "자동 설치 불가 → https://ffmpeg.org 에서 설치"; FAIL+=("ffmpeg"); fi

step "Node.js 22+"
if command -v node >/dev/null && [ "$(node -v | sed -E 's/^v([0-9]+).*/\1/')" -ge 22 ]; then echo "이미 있음 ($(node -v))"
elif command -v brew >/dev/null; then brew install node@22 && brew link --overwrite node@22 || FAIL+=("node")
else echo "자동 설치 불가 → https://nodejs.org 에서 LTS(22 이상) 설치"; FAIL+=("node"); fi

command -v npx >/dev/null || { echo "npx가 없어 스킬 설치를 건너뜀"; FAIL+=("remotion-skill" "hyperframes-skill"); }

# 2) Remotion 스킬
if command -v npx >/dev/null; then
  step "Remotion 스킬"
  if has_skill remotion; then echo "이미 있음"
  else npx --yes skills add remotion-dev/skills --yes || npx --yes skills add remotion-dev/skills || FAIL+=("remotion-skill"); fi

  # 3) HyperFrames 스킬 (--full-depth: 최신 main 기준으로 받음)
  step "HyperFrames 스킬"
  if has_skill hyperframes; then echo "이미 있음"
  else npx --yes skills add heygen-com/hyperframes --full-depth --yes || FAIL+=("hyperframes-skill"); fi
fi

# 4) OpenMontage
step "OpenMontage → $OM_DIR"
if [ -d "$OM_DIR/.venv" ]; then echo "이미 설치됨"
else
  if [ ! -d "$OM_DIR" ]; then git clone https://github.com/calesthio/OpenMontage.git "$OM_DIR" || FAIL+=("openmontage-clone"); fi
  if [ -d "$OM_DIR" ]; then
    if command -v make >/dev/null; then (cd "$OM_DIR" && make setup) || FAIL+=("openmontage-setup")
    else
      (cd "$OM_DIR" && python3 -m venv .venv && . .venv/bin/activate \
        && python -m pip install -r requirements.txt \
        && (cd remotion-composer && npm install) \
        && python -m pip install piper-tts \
        && { [ -f .env ] || cp .env.example .env; }) || FAIL+=("openmontage-setup")
    fi
  fi
fi

# 5) 선택: 받아쓰기
step "faster-whisper (선택)"
python3 -c 'import faster_whisper' 2>/dev/null && echo "이미 있음" || python3 -m pip install --user faster-whisper || echo "건너뜀 (선택 사항)"

echo
if [ ${#FAIL[@]} -eq 0 ]; then echo "설치 완료 ✅"; else echo "실패/수동 설치 필요: ${FAIL[*]}"; echo "각 공식 README를 읽고 다시 시도하세요."; fi
echo
bash "$(dirname "$0")/doctor.sh" "$OM_DIR"
