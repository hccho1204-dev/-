#!/usr/bin/env python3
"""샘플 보장분석 리포트 생성 스크립트.

기존 coverage-analysis-report 스킬의 generate_report.py를 활용하여
매일 샘플 데이터로 PDF 리포트를 생성합니다.
"""

import json
import sys
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
REPORTS_DIR = PROJECT_ROOT / "reports"
REPORT_SCRIPT = PROJECT_ROOT / "scripts" / "generate_report.py"

SAMPLE_CLIENT_DATA = {
    "client_name": "홍길동(샘플)",
    "age": 45,
    "gender": "남성",
    "occupation": "회사원",
    "existing_coverage": {
        "death": {"amount": 50000000, "insurer": "삼성생명", "expiry": "2030-12-31"},
        "cancer": {"amount": 30000000, "insurer": "한화생명", "expiry": "2028-06-30"},
        "hospitalization": {"amount": 50000, "insurer": "DB손해보험", "expiry": "2027-03-15"},
    },
    "recommended_coverage": {
        "death": 100000000,
        "cancer": 50000000,
        "cerebrovascular": 50000000,
        "heart": 50000000,
        "hospitalization": 100000,
        "surgery": 3000000,
    },
    "gaps": [
        {"category": "사망보장", "current": 50000000, "recommended": 100000000, "gap": 50000000},
        {"category": "암보장", "current": 30000000, "recommended": 50000000, "gap": 20000000},
        {"category": "뇌혈관질환", "current": 0, "recommended": 50000000, "gap": 50000000},
        {"category": "심장질환", "current": 0, "recommended": 50000000, "gap": 50000000},
        {"category": "입원일당", "current": 50000, "recommended": 100000, "gap": 50000},
    ],
}


def generate_report_with_builder():
    sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
    try:
        from generate_report import CoverageReportBuilder

        today_str = datetime.now().strftime("%y%m%d")
        output_path = REPORTS_DIR / f"보장분석_샘플_{today_str}.pdf"
        builder = CoverageReportBuilder(SAMPLE_CLIENT_DATA, str(output_path))
        builder.build()
        return str(output_path)
    except ImportError:
        return generate_report_simple()


def generate_report_simple():
    """generate_report.py를 import할 수 없을 때 간단한 텍스트 리포트 생성."""
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units import mm
        from reportlab.pdfgen import canvas

        today_str = datetime.now().strftime("%y%m%d")
        output_path = REPORTS_DIR / f"보장분석_샘플_{today_str}.pdf"

        c = canvas.Canvas(str(output_path), pagesize=A4)
        width, height = A4

        font_path = PROJECT_ROOT / "assets" / "fonts" / "NanumGothic.ttf"
        if font_path.exists():
            from reportlab.pdfbase import pdfmetrics
            from reportlab.pdfbase.ttfonts import TTFont

            pdfmetrics.registerFont(TTFont("NanumGothic", str(font_path)))
            font_name = "NanumGothic"
        else:
            font_name = "Helvetica"

        y = height - 40 * mm
        c.setFont(font_name, 18)
        c.drawString(30 * mm, y, "보장분석 리포트 (샘플)")

        y -= 15 * mm
        c.setFont(font_name, 12)
        c.drawString(30 * mm, y, f"고객명: {SAMPLE_CLIENT_DATA['client_name']}")
        y -= 8 * mm
        c.drawString(30 * mm, y, f"분석일: {datetime.now().strftime('%Y-%m-%d')}")
        y -= 8 * mm
        c.drawString(30 * mm, y, f"나이/성별: {SAMPLE_CLIENT_DATA['age']}세 / {SAMPLE_CLIENT_DATA['gender']}")

        y -= 15 * mm
        c.setFont(font_name, 14)
        c.drawString(30 * mm, y, "보장 갭 분석")

        y -= 10 * mm
        c.setFont(font_name, 10)
        for gap in SAMPLE_CLIENT_DATA["gaps"]:
            line = f"  {gap['category']}: 현재 {gap['current']:,}원 → 권장 {gap['recommended']:,}원 (부족: {gap['gap']:,}원)"
            c.drawString(30 * mm, y, line)
            y -= 7 * mm

        y -= 10 * mm
        c.setFont(font_name, 11)
        c.drawString(30 * mm, y, "* 본 리포트는 샘플 데이터로 생성된 예시입니다.")
        y -= 7 * mm
        c.drawString(30 * mm, y, "* 실제 보장분석은 개인별 맞춤 상담을 통해 진행됩니다.")

        y -= 15 * mm
        c.setFont(font_name, 10)
        c.drawString(30 * mm, y, "블레스본부 | 인카금융서비스")

        c.save()
        return str(output_path)

    except ImportError:
        today_str = datetime.now().strftime("%y%m%d")
        output_path = REPORTS_DIR / f"보장분석_샘플_{today_str}.json"
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "title": "보장분석 리포트 (샘플)",
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "client": SAMPLE_CLIENT_DATA,
                    "note": "reportlab 미설치로 JSON 형식으로 생성됨",
                },
                f,
                ensure_ascii=False,
                indent=2,
            )
        return str(output_path)


def main():
    REPORTS_DIR.mkdir(exist_ok=True)
    output_path = generate_report_with_builder()
    print(f"✅ 보장분석 리포트 생성 완료: {output_path}")

    result_path = REPORTS_DIR / ".last_result.json"
    with open(result_path, "w", encoding="utf-8") as f:
        json.dump({"file": output_path}, f, ensure_ascii=False, indent=2)

    return 0


if __name__ == "__main__":
    sys.exit(main())
