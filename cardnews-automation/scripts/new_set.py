#!/usr/bin/env python3
"""새 카드뉴스 세트 폴더를 만든다.

사용법:
    python3 cardnews-automation/scripts/new_set.py "경력단절 설계사 현실"
    python3 cardnews-automation/scripts/new_set.py "주제" --date 2026-09-25

결과:
    cardnews-automation/sets/2026-09-24_경력단절-설계사-현실/
        plan.md, plan.json, caption.md, image-prompts.md, images/, output/
"""
import argparse
import datetime as dt
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SETS = ROOT / "sets"
PAGE_COUNT = 9


def slugify(text: str) -> str:
    text = re.sub(r"[^\w가-힣\s-]", "", text).strip()
    text = re.sub(r"\s+", "-", text)
    return text[:40] or "untitled"


def empty_plan(set_id: str, date: str, topic: str) -> dict:
    pages = [{"no": 1, "type": "cover", "label": "", "headline": "", "body": "", "image_scene": ""}]
    for n in range(2, PAGE_COUNT):
        pages.append({"no": n, "type": "body", "headline": "", "body": "", "image_scene": ""})
    pages.append({"no": PAGE_COUNT, "type": "ending", "headline": "", "cta": "", "disclaimer": "", "image_scene": ""})
    return {
        "set_id": set_id,
        "date": date,
        "topic": topic,
        "category": "",
        "hook_type": "",
        "visual_style": "",
        "pages": pages,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="새 카드뉴스 세트 폴더 생성")
    ap.add_argument("topic", help="주제 (한글 가능)")
    ap.add_argument("--date", default=dt.date.today().isoformat(), help="YYYY-MM-DD (기본: 오늘)")
    args = ap.parse_args()

    set_id = f"{args.date}_{slugify(args.topic)}"
    folder = SETS / set_id
    if folder.exists():
        print(f"이미 있는 폴더입니다: {folder}")
        return 1

    (folder / "images").mkdir(parents=True)
    (folder / "output").mkdir()
    (folder / "plan.json").write_text(
        json.dumps(empty_plan(set_id, args.date, args.topic), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (folder / "plan.md").write_text(f"# 카드뉴스 기획안: {args.topic}\n\n(cardnews-plan 스킬이 채웁니다)\n", encoding="utf-8")
    (folder / "caption.md").write_text("# 인스타 캡션\n\n(cardnews-plan 스킬이 채웁니다)\n", encoding="utf-8")
    (folder / "image-prompts.md").write_text("# 이미지 프롬프트 9장\n\n(cardnews-images 스킬이 채웁니다)\n", encoding="utf-8")
    (folder / "images" / ".gitkeep").touch()
    (folder / "output" / ".gitkeep").touch()

    print(f"생성 완료: {folder.relative_to(ROOT.parent)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
