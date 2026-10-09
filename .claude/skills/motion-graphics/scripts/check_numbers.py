"""숫자 검문: 화면에 나온 숫자가 대본에 진짜 있는지 대조한다.

사용법: python3 check_numbers.py <대본.txt> <화면텍스트.txt>
대본에 없는 숫자가 하나라도 있으면 종료코드 1 (= 무조건 재제작)
"""
import re
import sys

NUM = re.compile(r"\d[\d,]*(?:\.\d+)?")


def numbers(text):
    out = set()
    for m in NUM.findall(text):
        v = m.replace(",", "")
        out.add(v.rstrip("0").rstrip(".") if "." in v else v)
    return out


def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    script = open(sys.argv[1], encoding="utf-8").read()
    screen = open(sys.argv[2], encoding="utf-8").read()
    allowed, shown = numbers(script), numbers(screen)
    fake = sorted(shown - allowed, key=lambda s: float(s))
    print(f"대본 숫자 {len(allowed)}개 / 화면 숫자 {len(shown)}개")
    if fake:
        print("❌ 대본에 없는 숫자 발견 → 무조건 재제작")
        for n in fake:
            lines = [l.strip() for l in screen.splitlines() if n in l.replace(",", "")]
            print(f"  - {n}   (화면: {lines[0] if lines else '?'})")
        sys.exit(1)
    print("✅ 화면의 모든 숫자가 대본에 있습니다")


if __name__ == "__main__":
    main()
