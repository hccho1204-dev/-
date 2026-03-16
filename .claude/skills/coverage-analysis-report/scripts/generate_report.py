#!/usr/bin/env python3
"""
보장분석 리포트 PDF 생성 스크립트

사용법:
    python generate_report.py --input data.json --output 보장분석_홍길동_260315.pdf

입력: 고객 보장분석 JSON 데이터
출력: A4 PDF 리포트

브랜딩: 블레스본부 | 인카금융서비스 VIP총괄 | 본부장 조홍철
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    NextPageTemplate,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

# ──────────────────────────────────────────────
# 색상 정의 (report-style.md 기준)
# ──────────────────────────────────────────────
BLESS_ORANGE = colors.HexColor("#FF6B35")
TEXT_COLOR = colors.HexColor("#2D3748")
BG_WHITE = colors.HexColor("#FFFFFF")
ROW_EVEN = colors.HexColor("#F7FAFC")
GRID_LINE = colors.HexColor("#E2E8F0")
SUB_TEXT = colors.HexColor("#718096")

RATING_COLORS = {
    "충분": {"text": colors.HexColor("#38A169"), "bg": colors.HexColor("#F0FFF4")},
    "보통": {"text": colors.HexColor("#D69E2E"), "bg": colors.HexColor("#FFFFF0")},
    "부족": {"text": colors.HexColor("#E53E3E"), "bg": colors.HexColor("#FFF5F5")},
    "미가입": {"text": colors.HexColor("#A0AEC0"), "bg": colors.HexColor("#F7FAFC")},
}

PRIORITY_COLORS = {
    "높음": colors.HexColor("#E53E3E"),
    "보통": colors.HexColor("#D69E2E"),
    "낮음": colors.HexColor("#38A169"),
}

SCORE_COLORS = [
    (25, colors.HexColor("#E53E3E")),
    (50, colors.HexColor("#DD6B20")),
    (75, colors.HexColor("#D69E2E")),
    (100, colors.HexColor("#38A169")),
]

PAGE_WIDTH, PAGE_HEIGHT = A4
MARGIN = 20 * mm
CONTENT_WIDTH = PAGE_WIDTH - MARGIN * 2

FOOTER_TEXT = "블레스본부 | 인카금융서비스 VIP총괄 | 본부장 조홍철"


# ──────────────────────────────────────────────
# 한글 폰트 탐색
# ──────────────────────────────────────────────
def _resolve_font():
    """시스템에 설치된 한글 폰트를 탐색하여 등록한다. NotoSansCJK 우선."""
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont

    font_candidates = [
        # NotoSansCJK 우선 탐색
        ("NotoSansCJK", "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"),
        ("NotoSansCJK", "/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc"),
        ("NotoSansCJK", "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc"),
        ("NotoSansCJK", "/usr/share/fonts/OTF/NotoSansCJK-Regular.ttc"),
        ("NotoSansCJK", "/usr/share/fonts/google-noto-cjk/NotoSansCJKkr-Regular.otf"),
        ("NotoSansKR", "/usr/share/fonts/truetype/noto/NotoSansKR-Regular.ttf"),
        ("NotoSansKR", "/usr/share/fonts/noto/NotoSansKR-Regular.ttf"),
        ("NotoSansKR", "/usr/share/fonts/truetype/noto/NotoSansKR-Regular.otf"),
        # 나눔고딕 fallback
        ("NanumGothic", "/usr/share/fonts/truetype/nanum/NanumGothic.ttf"),
        ("NanumGothic", "/usr/share/fonts/nanum/NanumGothic.ttf"),
        # Malgun Gothic fallback
        ("MalgunGothic", "/usr/share/fonts/truetype/malgun/malgun.ttf"),
        # macOS fallback
        ("AppleGothic", "/System/Library/Fonts/AppleSDGothicNeo.ttc"),
    ]
    for name, path in font_candidates:
        if Path(path).exists():
            try:
                pdfmetrics.registerFont(TTFont(name, path))
                return name
            except Exception:
                continue
    return "Helvetica"


# ──────────────────────────────────────────────
# 스타일 정의
# ──────────────────────────────────────────────
def get_styles():
    """PDF에 사용할 ParagraphStyle 딕셔너리를 반환한다."""
    base = getSampleStyleSheet()
    font_name = _resolve_font()

    styles = {
        "cover_title": ParagraphStyle(
            "cover_title",
            parent=base["Normal"],
            fontName=font_name,
            fontSize=24,
            leading=32,
            alignment=TA_CENTER,
            textColor=TEXT_COLOR,
            spaceAfter=12,
        ),
        "cover_sub": ParagraphStyle(
            "cover_sub",
            parent=base["Normal"],
            fontName=font_name,
            fontSize=12,
            leading=18,
            alignment=TA_CENTER,
            textColor=TEXT_COLOR,
        ),
        "section_title": ParagraphStyle(
            "section_title",
            parent=base["Normal"],
            fontName=font_name,
            fontSize=14,
            leading=20,
            textColor=BLESS_ORANGE,
            spaceBefore=14,
            spaceAfter=8,
        ),
        "subsection": ParagraphStyle(
            "subsection",
            parent=base["Normal"],
            fontName=font_name,
            fontSize=11,
            leading=15,
            textColor=TEXT_COLOR,
            spaceBefore=8,
            spaceAfter=5,
        ),
        "body": ParagraphStyle(
            "body",
            parent=base["Normal"],
            fontName=font_name,
            fontSize=10,
            leading=15,
            textColor=TEXT_COLOR,
        ),
        "table_header": ParagraphStyle(
            "table_header",
            parent=base["Normal"],
            fontName=font_name,
            fontSize=9,
            leading=12,
            textColor=colors.white,
            alignment=TA_CENTER,
        ),
        "table_cell": ParagraphStyle(
            "table_cell",
            parent=base["Normal"],
            fontName=font_name,
            fontSize=9,
            leading=12,
            textColor=TEXT_COLOR,
            alignment=TA_CENTER,
        ),
        "table_cell_left": ParagraphStyle(
            "table_cell_left",
            parent=base["Normal"],
            fontName=font_name,
            fontSize=9,
            leading=12,
            textColor=TEXT_COLOR,
            alignment=TA_LEFT,
        ),
        "disclaimer": ParagraphStyle(
            "disclaimer",
            parent=base["Normal"],
            fontName=font_name,
            fontSize=8,
            leading=11,
            textColor=SUB_TEXT,
        ),
        "cta": ParagraphStyle(
            "cta",
            parent=base["Normal"],
            fontName=font_name,
            fontSize=10,
            leading=15,
            textColor=TEXT_COLOR,
            alignment=TA_CENTER,
        ),
        "footer_style": ParagraphStyle(
            "footer_style",
            parent=base["Normal"],
            fontName=font_name,
            fontSize=7,
            leading=10,
            textColor=SUB_TEXT,
        ),
    }
    return styles


# ──────────────────────────────────────────────
# 헤더/푸터
# ──────────────────────────────────────────────
def _draw_header_footer(canvas, doc):
    """모든 본문 페이지에 헤더와 푸터를 그린다."""
    canvas.saveState()
    font_name = _resolve_font()

    # 헤더 오렌지 바
    canvas.setFillColor(BLESS_ORANGE)
    canvas.rect(0, PAGE_HEIGHT - 6 * mm, PAGE_WIDTH, 6 * mm, fill=1, stroke=0)

    # 헤더 텍스트
    canvas.setFillColor(TEXT_COLOR)
    canvas.setFont(font_name, 8)
    canvas.drawString(MARGIN, PAGE_HEIGHT - 16 * mm, "보장분석 리포트")
    canvas.drawRightString(PAGE_WIDTH - MARGIN, PAGE_HEIGHT - 16 * mm, "블레스본부")

    # 헤더 구분선
    canvas.setStrokeColor(GRID_LINE)
    canvas.setLineWidth(0.5)
    canvas.line(MARGIN, PAGE_HEIGHT - 18 * mm, PAGE_WIDTH - MARGIN, PAGE_HEIGHT - 18 * mm)

    # 푸터 구분선
    canvas.line(MARGIN, MARGIN, PAGE_WIDTH - MARGIN, MARGIN)

    # 푸터 텍스트
    canvas.setFillColor(SUB_TEXT)
    canvas.setFont(font_name, 7)
    canvas.drawString(MARGIN, MARGIN - 10, FOOTER_TEXT)
    canvas.drawRightString(PAGE_WIDTH - MARGIN, MARGIN - 10, f"p.{doc.page}")

    canvas.restoreState()


def _draw_cover_page(canvas, doc):
    """표지 전용: 오렌지 바 + 푸터만 그린다."""
    canvas.saveState()
    font_name = _resolve_font()

    # 오렌지 바
    canvas.setFillColor(BLESS_ORANGE)
    canvas.rect(0, PAGE_HEIGHT - 10 * mm, PAGE_WIDTH, 10 * mm, fill=1, stroke=0)

    # 푸터
    canvas.setStrokeColor(GRID_LINE)
    canvas.setLineWidth(0.5)
    canvas.line(MARGIN, MARGIN, PAGE_WIDTH - MARGIN, MARGIN)
    canvas.setFillColor(SUB_TEXT)
    canvas.setFont(font_name, 7)
    canvas.drawString(MARGIN, MARGIN - 10, FOOTER_TEXT)

    canvas.restoreState()


# ──────────────────────────────────────────────
# 점수 계산
# ──────────────────────────────────────────────
COVERAGE_AREAS = [
    "사망보장", "암보장", "뇌/심장보장", "실손보장",
    "후유장해", "입원/수술", "운전자/일상배상",
]

RATING_SCORES = {"충분": 100, "보통": 65, "부족": 30, "미가입": 0}


def calculate_total_score(analysis):
    """7대 영역 평가를 기반으로 전체 점수를 계산한다."""
    total = 0
    for area in COVERAGE_AREAS:
        rating = analysis.get(area, {}).get("rating", "미가입")
        total += RATING_SCORES.get(rating, 0)
    return round(total / len(COVERAGE_AREAS))


def get_score_color(score):
    """점수에 해당하는 색상을 반환한다."""
    for threshold, color in SCORE_COLORS:
        if score <= threshold:
            return color
    return SCORE_COLORS[-1][1]


# ──────────────────────────────────────────────
# 리포트 빌더
# ──────────────────────────────────────────────
class CoverageReportBuilder:
    """보장분석 리포트 PDF를 생성한다."""

    def __init__(self, data: dict, output_path: str):
        self.data = data
        self.output_path = output_path
        self.styles = get_styles()
        self.elements = []

        self.customer = data.get("customer", {})
        self.policies = data.get("policies", [])
        self.analysis = data.get("analysis", {})
        self.findings = data.get("findings", {})
        self.suggestions = data.get("suggestions", [])

        self.total_score = calculate_total_score(self.analysis)
        self.analysis_date = data.get(
            "analysis_date", datetime.now().strftime("%Y.%m.%d")
        )

    def build(self):
        """PDF를 생성하고 저장한다."""
        doc = BaseDocTemplate(
            self.output_path,
            pagesize=A4,
            topMargin=MARGIN + 2 * mm,
            bottomMargin=MARGIN + 2 * mm,
            leftMargin=MARGIN,
            rightMargin=MARGIN,
            title="보장분석 리포트",
            author=FOOTER_TEXT,
        )

        cover_frame = Frame(
            MARGIN, MARGIN,
            CONTENT_WIDTH, PAGE_HEIGHT - MARGIN * 2,
            id="cover",
        )
        content_frame = Frame(
            MARGIN, MARGIN + 5 * mm,
            CONTENT_WIDTH, PAGE_HEIGHT - MARGIN * 2 - 15 * mm,
            id="content",
        )

        doc.addPageTemplates([
            PageTemplate(id="Cover", frames=[cover_frame], onPage=_draw_cover_page),
            PageTemplate(id="Content", frames=[content_frame], onPage=_draw_header_footer),
        ])

        self._build_cover()
        self.elements.append(NextPageTemplate("Content"))
        self.elements.append(PageBreak())
        self._build_summary()
        self._build_coverage_table()
        self._build_findings()
        self._build_suggestions()
        self._build_policy_details()
        self._build_disclaimer()

        doc.build(self.elements)
        print(f"PDF 생성 완료: {self.output_path}")

    # ── 표지 ──
    def _build_cover(self):
        s = self.styles
        self.elements.append(Spacer(1, 70 * mm))
        self.elements.append(Paragraph("보장분석 리포트", s["cover_title"]))
        self.elements.append(Spacer(1, 20 * mm))

        name = self.customer.get("name", "고객")
        self.elements.append(Paragraph(f"고객명: {name}", s["cover_sub"]))
        self.elements.append(Spacer(1, 3 * mm))
        self.elements.append(Paragraph(f"분석일: {self.analysis_date}", s["cover_sub"]))
        self.elements.append(Spacer(1, 40 * mm))

        self.elements.append(Paragraph("─" * 30, s["cover_sub"]))
        self.elements.append(Spacer(1, 3 * mm))
        self.elements.append(Paragraph("블레스본부", s["cover_sub"]))
        self.elements.append(Paragraph("인카금융서비스 VIP총괄", s["cover_sub"]))
        self.elements.append(Paragraph("본부장 조홍철", s["cover_sub"]))

    # ── 분석 요약 ──
    def _build_summary(self):
        s = self.styles
        self.elements.append(Paragraph("분석 요약", s["section_title"]))

        # 전체 보장 점수
        score_color = get_score_color(self.total_score)
        self.elements.append(
            Paragraph(
                f'<font color="{score_color.hexval()}" size="32">{self.total_score}</font>'
                f'<font color="{TEXT_COLOR.hexval()}" size="14"> / 100점</font>',
                ParagraphStyle(
                    "score_inline", parent=s["body"],
                    alignment=TA_CENTER, spaceBefore=8,
                ),
            )
        )
        self.elements.append(Spacer(1, 5 * mm))

        # 월 총 보험료
        total_premium = sum(p.get("monthly_premium", 0) for p in self.policies)
        self.elements.append(
            Paragraph(f"월 총 보험료: {total_premium:,}원", s["body"])
        )
        self.elements.append(Spacer(1, 3 * mm))

        # 핵심 코멘트
        comment = self.data.get("summary_comment", "")
        if comment:
            self.elements.append(Paragraph(comment, s["body"]))
        self.elements.append(Spacer(1, 5 * mm))

        # 7대 영역 미니 요약 테이블
        header = [Paragraph(a[:4], s["table_header"]) for a in COVERAGE_AREAS]
        ratings = []
        for area in COVERAGE_AREAS:
            rating = self.analysis.get(area, {}).get("rating", "미가입")
            rc = RATING_COLORS.get(rating, RATING_COLORS["미가입"])
            ratings.append(
                Paragraph(
                    f'<font color="{rc["text"].hexval()}">{rating}</font>',
                    s["table_cell"],
                )
            )

        col_w = CONTENT_WIDTH / len(COVERAGE_AREAS)
        t = Table([header, ratings], colWidths=[col_w] * len(COVERAGE_AREAS))

        style_cmds = [
            ("BACKGROUND", (0, 0), (-1, 0), BLESS_ORANGE),
            ("GRID", (0, 0), (-1, -1), 0.5, GRID_LINE),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]
        for i, area in enumerate(COVERAGE_AREAS):
            rating = self.analysis.get(area, {}).get("rating", "미가입")
            bg = RATING_COLORS.get(rating, RATING_COLORS["미가입"])["bg"]
            style_cmds.append(("BACKGROUND", (i, 1), (i, 1), bg))

        t.setStyle(TableStyle(style_cmds))
        self.elements.append(t)
        self.elements.append(Spacer(1, 8 * mm))

    # ── 보장영역별 현황표 ──
    def _build_coverage_table(self):
        s = self.styles
        self.elements.append(Paragraph("보장영역별 현황", s["section_title"]))

        header = [
            Paragraph("보장영역", s["table_header"]),
            Paragraph("가입 상품", s["table_header"]),
            Paragraph("보장금액", s["table_header"]),
            Paragraph("평가", s["table_header"]),
        ]
        rows = [header]

        for area in COVERAGE_AREAS:
            info = self.analysis.get(area, {})
            rating = info.get("rating", "미가입")
            product = info.get("product", "-")
            amount = info.get("amount", "-")
            rc = RATING_COLORS.get(rating, RATING_COLORS["미가입"])

            rows.append([
                Paragraph(area, s["table_cell_left"]),
                Paragraph(str(product), s["table_cell"]),
                Paragraph(str(amount), s["table_cell"]),
                Paragraph(
                    f'<font color="{rc["text"].hexval()}">{rating}</font>',
                    s["table_cell"],
                ),
            ])

        col_widths = [CONTENT_WIDTH * r for r in [0.22, 0.33, 0.25, 0.20]]
        t = Table(rows, colWidths=col_widths)

        style_cmds = [
            ("BACKGROUND", (0, 0), (-1, 0), BLESS_ORANGE),
            ("GRID", (0, 0), (-1, -1), 0.5, GRID_LINE),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ]
        for i, area in enumerate(COVERAGE_AREAS):
            row_idx = i + 1
            rating = self.analysis.get(area, {}).get("rating", "미가입")
            # 평가 셀 배경
            bg = RATING_COLORS.get(rating, RATING_COLORS["미가입"])["bg"]
            style_cmds.append(("BACKGROUND", (3, row_idx), (3, row_idx), bg))
            # 짝수행 연한 그레이
            if row_idx % 2 == 0:
                style_cmds.append(("BACKGROUND", (0, row_idx), (2, row_idx), ROW_EVEN))

        t.setStyle(TableStyle(style_cmds))
        self.elements.append(t)
        self.elements.append(Spacer(1, 8 * mm))

    # ── 주요 발견사항 ──
    def _build_findings(self):
        s = self.styles
        self.elements.append(Paragraph("주요 발견사항", s["section_title"]))

        strengths = self.findings.get("strengths", [])
        if strengths:
            self.elements.append(Paragraph("잘 갖춰진 보장", s["subsection"]))
            for item in strengths:
                self.elements.append(Paragraph(f"• {item}", s["body"]))
            self.elements.append(Spacer(1, 3 * mm))

        weaknesses = self.findings.get("weaknesses", [])
        if weaknesses:
            self.elements.append(Paragraph("보완이 필요한 보장", s["subsection"]))
            for item in weaknesses:
                self.elements.append(Paragraph(f"• {item}", s["body"]))
            self.elements.append(Spacer(1, 3 * mm))

        duplicates = self.findings.get("duplicates", [])
        if duplicates:
            self.elements.append(Paragraph("중복 보장", s["subsection"]))
            for item in duplicates:
                self.elements.append(Paragraph(f"• {item}", s["body"]))
        self.elements.append(Spacer(1, 8 * mm))

    # ── 우선순위별 개선 제안 ──
    def _build_suggestions(self):
        s = self.styles
        if not self.suggestions:
            return

        self.elements.append(Paragraph("우선순위별 개선 제안", s["section_title"]))

        header = [
            Paragraph("우선순위", s["table_header"]),
            Paragraph("영역", s["table_header"]),
            Paragraph("제안 내용", s["table_header"]),
        ]
        rows = [header]

        for sg in self.suggestions:
            priority = sg.get("priority", "보통")
            pc = PRIORITY_COLORS.get(priority, PRIORITY_COLORS["보통"])
            rows.append([
                Paragraph(
                    f'<font color="{pc.hexval()}">{priority}</font>',
                    s["table_cell"],
                ),
                Paragraph(sg.get("area", ""), s["table_cell"]),
                Paragraph(sg.get("description", ""), s["table_cell_left"]),
            ])

        col_widths = [CONTENT_WIDTH * r for r in [0.15, 0.20, 0.65]]
        t = Table(rows, colWidths=col_widths)

        style_cmds = [
            ("BACKGROUND", (0, 0), (-1, 0), BLESS_ORANGE),
            ("GRID", (0, 0), (-1, -1), 0.5, GRID_LINE),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ]
        for i in range(1, len(rows)):
            if i % 2 == 0:
                style_cmds.append(("BACKGROUND", (0, i), (-1, i), ROW_EVEN))

        t.setStyle(TableStyle(style_cmds))
        self.elements.append(t)
        self.elements.append(Spacer(1, 8 * mm))

    # ── 가입 상세 내역 ──
    def _build_policy_details(self):
        s = self.styles
        self.elements.append(Paragraph("가입 상세 내역", s["section_title"]))

        for policy in self.policies:
            insurer = policy.get("insurer", "")
            product = policy.get("product_name", "")
            self.elements.append(
                Paragraph(f"{insurer} — {product}", s["subsection"])
            )
            start = policy.get("start_date", "-")
            premium = policy.get("monthly_premium", 0)
            payment = policy.get("payment_period", "")
            end = policy.get("end_date", "")

            detail_parts = [f"가입일: {start}", f"월 보험료: {premium:,}원"]
            if payment:
                detail_parts.append(f"납입기간: {payment}")
            if end:
                detail_parts.append(f"만기: {end}")
            self.elements.append(Paragraph("  |  ".join(detail_parts), s["body"]))

            coverages = policy.get("coverages", [])
            if coverages:
                header = [
                    Paragraph("담보명", s["table_header"]),
                    Paragraph("보장금액", s["table_header"]),
                ]
                rows = [header]
                for cov in coverages:
                    amount = cov.get("amount", 0)
                    if isinstance(amount, (int, float)) and amount >= 10000:
                        display_amount = f"{amount:,}원"
                    else:
                        display_amount = str(amount)
                    rows.append([
                        Paragraph(cov.get("type", ""), s["table_cell_left"]),
                        Paragraph(display_amount, s["table_cell"]),
                    ])

                col_widths = [CONTENT_WIDTH * 0.5, CONTENT_WIDTH * 0.5]
                t = Table(rows, colWidths=col_widths)

                style_cmds = [
                    ("BACKGROUND", (0, 0), (-1, 0), BLESS_ORANGE),
                    ("GRID", (0, 0), (-1, -1), 0.5, GRID_LINE),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("TOPPADDING", (0, 0), (-1, -1), 3),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ]
                for i in range(1, len(rows)):
                    if i % 2 == 0:
                        style_cmds.append(("BACKGROUND", (0, i), (-1, i), ROW_EVEN))

                t.setStyle(TableStyle(style_cmds))
                self.elements.append(t)

            self.elements.append(Spacer(1, 5 * mm))

    # ── 면책 및 안내 ──
    def _build_disclaimer(self):
        s = self.styles
        self.elements.append(Spacer(1, 10 * mm))
        self.elements.append(Paragraph("면책 및 안내", s["section_title"]))

        disclaimer_text = (
            "본 보장분석 리포트는 고객님께서 제공해 주신 정보를 기반으로 작성된 참고 자료입니다. "
            "정확한 보장 내용은 반드시 보험증권 원본을 통해 확인하시기 바랍니다. "
            "본 자료는 보험 상품의 가입을 권유하거나 특정 상품을 추천하는 것이 아닙니다."
        )
        self.elements.append(Paragraph(disclaimer_text, s["disclaimer"]))
        self.elements.append(Spacer(1, 8 * mm))

        cta_text = (
            "더 자세한 상담이 필요하시면 블레스본부로 연락해 주세요.<br/><br/>"
            "카카오 오픈채팅 상담<br/>"
            "bless-insight-recruit.netlify.app"
        )
        self.elements.append(Paragraph(cta_text, s["cta"]))
        self.elements.append(Spacer(1, 10 * mm))

        # 하단 브랜딩
        footer_brand = (
            f'<font color="{SUB_TEXT.hexval()}">'
            "블레스본부 | 인카금융서비스 VIP총괄 | 본부장 조홍철"
            "</font>"
        )
        self.elements.append(
            Paragraph(
                footer_brand,
                ParagraphStyle(
                    "brand_footer", parent=s["disclaimer"],
                    alignment=TA_CENTER, spaceBefore=5,
                ),
            )
        )


# ──────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description="보장분석 리포트 PDF 생성",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
사용 예시:
  python generate_report.py --input data.json --output 보장분석_홍길동_260315.pdf

입력 JSON 구조:
  {
    "customer": {"name": "홍길동", "gender": "남", "birth_date": "1985-03-15", ...},
    "policies": [...],
    "analysis": {
      "사망보장": {"rating": "충분", "product": "무배당통합", "amount": "1억 원"},
      ...
    },
    "findings": {"strengths": [...], "weaknesses": [...], "duplicates": [...]},
    "suggestions": [{"priority": "높음", "area": "뇌/심장", "description": "..."}],
    "summary_comment": "전반적으로 ...",
    "analysis_date": "2026.03.15"
  }
        """,
    )
    parser.add_argument("--input", "-i", required=True, help="입력 JSON 파일 경로")
    parser.add_argument("--output", "-o", required=True, help="출력 PDF 파일 경로")

    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"오류: 입력 파일을 찾을 수 없습니다: {input_path}", file=sys.stderr)
        sys.exit(1)

    with open(input_path, encoding="utf-8") as f:
        data = json.load(f)

    builder = CoverageReportBuilder(data, args.output)
    builder.build()


if __name__ == "__main__":
    main()
