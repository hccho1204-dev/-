# (나중 단계) 미리캔버스 작업을 Playwright 스크립트로 굳히기

> **지금 당장 안 해도 됩니다.** Cowork로 2단계를 2~3주 돌려서 클릭 순서가 완전히 굳으면 그때 넘어오세요.

## 왜?
- Cowork: 매번 화면을 **보고 판단**하면서 클릭 → 느리고 비용이 듦, 대신 화면이 바뀌어도 알아서 대응
- 스크립트: 정해진 순서를 **기계처럼 반복** → 빠르고 가벼움, 대신 미리캔버스 화면이 바뀌면 고쳐야 함

## 순서 (Cowork에게 시키면 됩니다)
1. 내 PC에 설치 (1번만):
   ```
   pip install playwright
   playwright install chromium
   ```
2. 클릭 녹화 (1번만) — 브라우저가 열리면 평소처럼 작업하면 코드가 자동으로 적힙니다:
   ```
   playwright codegen https://www.miricanvas.com --save-storage=cardnews-automation/scripts/playwright/auth.json
   ```
3. Cowork에게:
   > "codegen으로 녹화된 코드 보고 `miricanvas_fill.py`의 TODO 부분 채워줘. selector는 녹화된 걸 써."
4. 실행:
   ```
   python3 cardnews-automation/scripts/playwright/miricanvas_fill.py cardnews-automation/sets/2026-09-24_주제
   ```

## 주의
- `auth.json`(로그인 정보)은 **절대 GitHub에 올리지 마세요.** `.gitignore`에 이미 등록돼 있습니다.
- 미리캔버스 이용약관을 지키는 범위에서 **내 계정·내 디자인**에만 사용하세요.
- 스크립트가 실패하면 Cowork 방식(`/cardnews-miricanvas`)으로 돌아가면 됩니다.
