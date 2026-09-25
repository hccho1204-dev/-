#!/bin/bash
cd "$(dirname "$0")"
if ! command -v node >/dev/null 2>&1; then
  echo "[안내] Node.js 가 없습니다. https://nodejs.org 에서 LTS 버전을 설치하세요."
  open https://nodejs.org
  read -p "엔터를 누르면 닫힙니다"
  exit 1
fi
(sleep 1.5 && open http://localhost:8787) &
node server.js
