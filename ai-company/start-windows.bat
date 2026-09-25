@echo off
chcp 65001 > nul
cd /d "%~dp0"
where node > nul 2>&1
if errorlevel 1 (
  echo.
  echo [안내] Node.js 가 설치되어 있지 않습니다.
  echo https://nodejs.org 에서 LTS 버전을 설치한 뒤 이 파일을 다시 더블클릭하세요.
  echo.
  start https://nodejs.org
  pause
  exit /b
)
start "" http://localhost:8787
node server.js
pause
