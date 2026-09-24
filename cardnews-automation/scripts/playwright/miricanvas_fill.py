#!/usr/bin/env python3
"""[뼈대] 미리캔버스 카드뉴스 자동 조립 스크립트.

전체 흐름(읽기 → 템플릿 복제 → 이미지 업로드 → 페이지별 사진/글자 교체 → 다운로드)은 완성돼 있고,
미리캔버스 화면의 버튼 위치(selector)만 `playwright codegen` 녹화 결과로 채우면 동작한다.
TODO 표시가 있는 SELECTORS 값을 채우는 것이 유일한 작업이다.

사용법:
    python3 miricanvas_fill.py <세트폴더> [--headed]
"""
import argparse
import json
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

HERE = Path(__file__).resolve().parent
AUTH = HERE / "auth.json"
TEMPLATE_NAME = "카드뉴스_마스터템플릿"  # config/design-spec.md 1번과 동일하게

# TODO: codegen 녹화 결과로 채우기. 값이 None이면 해당 단계에서 멈추고 알려준다.
SELECTORS = {
    "my_designs": None,          # 예: "text=내 디자인"
    "template_card": None,       # 예: f"text={TEMPLATE_NAME}"
    "copy_menu": None,           # 예: "text=사본 만들기"
    "upload_tab": None,          # 예: "text=업로드"
    "upload_input": None,        # 예: "input[type=file]"
    "page_thumb": None,          # 예: "[data-page-index='{i}']"  ({i}=0부터)
    "photo_frame": None,         # 페이지 안의 사진 프레임
    "text_box": None,            # 예: "[data-role='{role}']"  role = label/headline/body/cta/disclaimer
    "download_btn": None,        # 예: "text=다운로드"
    "download_png": None,        # 예: "text=PNG"
    "download_confirm": None,    # 예: "button:has-text('다운로드')"
}

FIELDS_BY_TYPE = {
    "cover": ["label", "headline", "body"],
    "body": ["headline", "body"],
    "ending": ["headline", "cta", "disclaimer"],
}


def need(key: str) -> str:
    sel = SELECTORS.get(key)
    if not sel:
        raise SystemExit(f"[멈춤] SELECTORS['{key}'] 가 비어 있습니다. codegen 녹화로 채워주세요.")
    return sel


def type_multiline(page, text: str) -> None:
    lines = text.split("\n")
    for i, line in enumerate(lines):
        page.keyboard.type(line, delay=15)
        if i < len(lines) - 1:
            page.keyboard.press("Enter")


def run(set_dir: Path, headed: bool) -> None:
    plan = json.loads((set_dir / "plan.json").read_text(encoding="utf-8"))
    images = sorted((set_dir / "images").glob("0[1-9].*"))
    out_dir = set_dir / "output"
    out_dir.mkdir(exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=not headed)
        context = browser.new_context(storage_state=str(AUTH) if AUTH.exists() else None, accept_downloads=True)
        page = context.new_page()
        page.goto("https://www.miricanvas.com")

        # 1) 템플릿 복제 후 열기
        page.click(need("my_designs"))
        page.click(need("template_card"), button="right")
        page.click(need("copy_menu"))
        # TODO: 사본 이름을 f"카드뉴스_{plan['set_id']}" 로 바꾸고 사본을 여는 동작 (녹화에서 확인)

        # 2) 이미지 9장 업로드
        page.click(need("upload_tab"))
        page.set_input_files(need("upload_input"), [str(i) for i in images])
        page.wait_for_timeout(5000)

        # 3) 페이지별 사진·글자 교체
        for idx, pg in enumerate(plan["pages"]):
            page.click(need("page_thumb").format(i=idx))
            # TODO: 업로드 패널의 idx번째 이미지를 photo_frame 으로 드래그 (녹화에서 확인)
            for role in FIELDS_BY_TYPE.get(pg["type"], []):
                text = pg.get(role, "")
                if not text:
                    continue
                page.dblclick(need("text_box").format(role=role))
                page.keyboard.press("Control+A")
                type_multiline(page, text)
                page.keyboard.press("Escape")

        # 4) 다운로드
        page.click(need("download_btn"))
        page.click(need("download_png"))
        with page.expect_download() as dl:
            page.click(need("download_confirm"))
        target = out_dir / dl.value.suggested_filename
        dl.value.save_as(target)
        print(f"저장 완료: {target}")

        context.storage_state(path=str(AUTH))
        browser.close()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("set_dir")
    ap.add_argument("--headed", action="store_true", help="브라우저 화면을 보면서 실행")
    args = ap.parse_args()
    run(Path(args.set_dir).expanduser(), args.headed)
    return 0


if __name__ == "__main__":
    sys.exit(main())
