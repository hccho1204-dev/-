#!/usr/bin/env python3
"""다운로드 폴더의 최신 이미지 9장을 생성 순서대로 01.png~09.png로 정리해 세트 폴더 images/에 넣는다.

사용법:
    python3 cardnews-automation/scripts/rename_images.py <세트폴더> <이미지가 있는 폴더>
    예) python3 cardnews-automation/scripts/rename_images.py cardnews-automation/sets/2026-09-24_주제 ~/Downloads

옵션:
    --count 9     가져올 장수 (기본 9)
    --move        복사 대신 이동
    --dry-run     실제로 옮기지 않고 어떤 파일이 몇 번이 될지 보여주기만

주의: "가장 먼저 만든 이미지 = 01" 기준입니다. 이미지를 1번부터 순서대로 생성했는지 꼭 확인하세요.
"""
import argparse
import shutil
import sys
from pathlib import Path

EXTS = {".png", ".jpg", ".jpeg", ".webp"}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("set_dir")
    ap.add_argument("source_dir")
    ap.add_argument("--count", type=int, default=9)
    ap.add_argument("--move", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    set_dir = Path(args.set_dir).expanduser()
    src = Path(args.source_dir).expanduser()
    if not set_dir.is_dir():
        print(f"세트 폴더가 없습니다: {set_dir}")
        return 1
    if not src.is_dir():
        print(f"이미지 폴더가 없습니다: {src}")
        return 1

    files = [p for p in src.iterdir() if p.is_file() and p.suffix.lower() in EXTS]
    if len(files) < args.count:
        print(f"이미지가 {len(files)}장뿐입니다. {args.count}장이 필요합니다.")
        return 1

    # 가장 최근 N장을 고른 뒤, 오래된 것부터(=먼저 만든 것부터) 번호를 붙인다.
    latest = sorted(files, key=lambda p: p.stat().st_mtime, reverse=True)[: args.count]
    ordered = sorted(latest, key=lambda p: p.stat().st_mtime)

    out = set_dir / "images"
    out.mkdir(exist_ok=True)
    for i, f in enumerate(ordered, 1):
        target = out / f"{i:02d}{f.suffix.lower()}"
        print(f"{f.name}  →  {target.name}")
        if args.dry_run:
            continue
        if args.move:
            shutil.move(str(f), target)
        else:
            shutil.copy2(f, target)

    print("미리보기만 했습니다 (--dry-run)." if args.dry_run else f"완료: {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
