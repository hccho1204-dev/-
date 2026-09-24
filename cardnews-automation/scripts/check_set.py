#!/usr/bin/env python3
"""2단계(미리캔버스 작업) 들어가기 전에 세트 폴더 재료가 다 준비됐는지 점검한다.

사용법:
    python3 cardnews-automation/scripts/check_set.py <세트폴더>

점검 항목:
    - plan.json 형식, 9페이지, 빈 칸 여부
    - 글자수 제한 (design-spec 기본값 기준)
    - 금지 표현 (config/brand.md 5번 항목)
    - images/01~09 파일 존재
결과: 문제가 없으면 "READY", 있으면 고칠 목록을 출력하고 종료코드 1.
"""
import json
import sys
from pathlib import Path

PAGE_COUNT = 9
EXTS = (".png", ".jpg", ".jpeg", ".webp")

# 한 줄 최대 글자수, 최대 줄 수 (config/design-spec.md 와 맞출 것)
LIMITS = {
    ("cover", "label"): (12, 1),
    ("cover", "headline"): (10, 2),
    ("cover", "body"): (24, 1),
    ("body", "headline"): (14, 2),
    ("body", "body"): (22, 3),
    ("ending", "headline"): (16, 2),
    ("ending", "cta"): (20, 1),
}
BANNED = [
    "무조건", "반드시 성공", "100%", "확실한 수입", "실패 없는",
    "돈 벌기 쉬운", "누구나 할 수 있는", "보장합니다", "최고의 보험", "유일한",
]
REQUIRED = {"cover": ["headline", "body"], "body": ["headline", "body"], "ending": ["headline", "cta"]}


def check(set_dir: Path) -> list:
    problems = []
    plan_path = set_dir / "plan.json"
    if not plan_path.exists():
        return ["plan.json 이 없습니다 → cardnews-plan 스킬로 기획부터 하세요."]
    try:
        plan = json.loads(plan_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        return [f"plan.json 형식 오류: {e}"]

    pages = plan.get("pages", [])
    if len(pages) != PAGE_COUNT:
        problems.append(f"페이지 수가 {len(pages)}장입니다 (9장 필요).")

    for p in pages:
        no, kind = p.get("no"), p.get("type")
        for field in REQUIRED.get(kind, []):
            if not str(p.get(field, "")).strip():
                problems.append(f"{no}장({kind}) '{field}' 가 비어 있습니다.")
        for (k, field), (max_chars, max_lines) in LIMITS.items():
            if k != kind or not p.get(field):
                continue
            lines = str(p[field]).split("\n")
            if len(lines) > max_lines:
                problems.append(f"{no}장 {field}: {len(lines)}줄 (최대 {max_lines}줄)")
            for line in lines:
                if len(line) > max_chars:
                    problems.append(f"{no}장 {field}: '{line}' {len(line)}자 (한 줄 최대 {max_chars}자)")
        text = " ".join(str(v) for v in p.values())
        for word in BANNED:
            if word in text:
                problems.append(f"{no}장 금지 표현 '{word}' 발견")

    img_dir = set_dir / "images"
    for n in range(1, PAGE_COUNT + 1):
        if not any((img_dir / f"{n:02d}{ext}").exists() for ext in EXTS):
            problems.append(f"images/{n:02d}.png 가 없습니다.")

    return problems


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    set_dir = Path(sys.argv[1]).expanduser()
    if not set_dir.is_dir():
        print(f"폴더가 없습니다: {set_dir}")
        return 2
    problems = check(set_dir)
    if problems:
        print(f"NOT READY — 고칠 곳 {len(problems)}개")
        for p in problems:
            print(f"  - {p}")
        return 1
    print("READY — 2단계(미리캔버스) 시작 가능")
    return 0


if __name__ == "__main__":
    sys.exit(main())
