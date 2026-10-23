#!/bin/bash
# 클라우드 세션 시작 시 agent-browser 프로그램을 자동 설치한다.
set -euo pipefail
[ "${CLAUDE_CODE_REMOTE:-}" = "true" ] || exit 0

if ! command -v agent-browser >/dev/null 2>&1; then
  npm i -g agent-browser >/dev/null 2>&1 || true
fi

# 미리 설치된 Chromium을 쓰도록 지정 (따로 다운로드하지 않음)
if [ -n "${CLAUDE_ENV_FILE:-}" ] && [ -e /opt/pw-browsers/chromium ]; then
  echo 'export AGENT_BROWSER_EXECUTABLE_PATH=/opt/pw-browsers/chromium' >> "$CLAUDE_ENV_FILE"
fi
