"""문답형 대본(EPxx.md) → 참고 서식(질문/답/꼬리질문 3칸 표) 워드 파일 변환.

사용: python3 build_docx.py <참고서식.docx> <출력폴더>
- 편마다 EPxx_제목.docx 1개 + 25편 합본 1개를 만든다.
"""
import copy, glob, os, re, sys
from xml.sax.saxutils import escape
from docx import Document
from docx.oxml import parse_xml

HERE = os.path.dirname(os.path.abspath(__file__))
NS = 'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"'
FONT = '<w:rFonts w:ascii="맑은 고딕" w:eastAsia="맑은 고딕" w:hAnsi="맑은 고딕"/>'
COLS = (1843, 5386, 1786)
DISCLAIMER = ("본 영상은 일반적인 보험 정보 제공 목적이며 특정 상품 가입을 권유하지 않습니다. "
              "보장 내용과 보험료는 상품·가입 조건에 따라 다릅니다. 가입 전 상품설명서와 약관을 꼭 확인하세요. "
              "기존 계약 해지 후 신규 가입 시 보험료 인상, 보장 제한 등 불이익이 생길 수 있습니다.")


def parse(path):
    ep = {"title": "", "parts": []}
    cur = None
    for raw in open(path, encoding="utf-8"):
        line = raw.rstrip("\n").strip()
        if line.startswith("# "):
            ep["title"] = line[2:].strip()
        elif line.startswith("## PART"):
            ep["parts"].append({"name": line[len("## PART"):].strip(), "qa": []})
        elif line.startswith("### "):
            cur = {"n": line[4:].strip(), "q": "", "a": [], "f": ""}
            ep["parts"][-1]["qa"].append(cur)
        elif line.startswith("Q: "):
            cur["q"] = line[3:].strip()
        elif line.startswith("A: "):
            cur["a"].append(line[3:].strip())
        elif line.startswith("F: "):
            cur["f"] = line[3:].strip()
    return ep


def run(text, bold=False, br=False, size=19):
    b = "<w:b/>" if bold else ""
    brk = "<w:br/>" if br else ""
    return (f'<w:r><w:rPr>{FONT}{b}<w:sz w:val="{size}"/><w:lang w:eastAsia="ko-KR"/></w:rPr>'
            f'{brk}<w:t xml:space="preserve">{escape(text)}</w:t></w:r>')


def cell(width, runs):
    return (f'<w:tc><w:tcPr><w:tcW w:w="{width}" w:type="dxa"/><w:vAlign w:val="center"/></w:tcPr>'
            f'<w:p><w:pPr><w:jc w:val="center"/></w:pPr>{runs}</w:p></w:tc>')


def row(cells, header=False):
    hdr = "<w:tblHeader/>" if header else ""
    return f'<w:tr><w:trPr><w:cantSplit/>{hdr}<w:jc w:val="center"/></w:trPr>{"".join(cells)}</w:tr>'


def table_xml(style_id, qas):
    head = row([cell(COLS[0], run("질문", True)), cell(COLS[1], run("답", True)),
                cell(COLS[2], run("꼬리질문", True))], header=True)
    rows = [head]
    for qa in qas:
        ans = "".join(run(p, br=(i > 0)) for i, p in enumerate(qa["a"]))
        rows.append(row([cell(COLS[0], run(f'{qa["n"]}. {qa["q"]}', True)),
                         cell(COLS[1], ans), cell(COLS[2], run(qa["f"]))]))
    style = f'<w:tblStyle w:val="{style_id}"/>' if style_id else ""
    return parse_xml(
        f'<w:tbl {NS}><w:tblPr>{style}<w:tblW w:w="0" w:type="auto"/><w:jc w:val="center"/>'
        f'<w:tblLayout w:type="fixed"/><w:tblLook w:val="04A0" w:firstRow="1" w:lastRow="0" '
        f'w:firstColumn="1" w:lastColumn="0" w:noHBand="0" w:noVBand="1"/></w:tblPr>'
        f'<w:tblGrid>{"".join(f"<w:gridCol w:w=\"{c}\"/>" for c in COLS)}</w:tblGrid>{"".join(rows)}</w:tbl>')


def para_xml(text, size=19, bold=False, center=False, page_break=False, color=None):
    jc = '<w:jc w:val="center"/>' if center else ""
    pb = '<w:r><w:br w:type="page"/></w:r>' if page_break else ""
    col = f'<w:color w:val="{color}"/>' if color else ""
    b = "<w:b/>" if bold else ""
    r = (f'<w:r><w:rPr>{FONT}{b}{col}<w:sz w:val="{size}"/><w:lang w:eastAsia="ko-KR"/></w:rPr>'
         f'<w:t xml:space="preserve">{escape(text)}</w:t></w:r>') if text else ""
    return parse_xml(f'<w:p {NS}><w:pPr>{jc}</w:pPr>{pb}{r}</w:p>')


def new_doc(template):
    doc = Document(template)
    body = doc.element.body
    style_id = body.find('.//{*}tblStyle')
    style_id = style_id.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val') if style_id is not None else None
    if style_id is None:  # 빈 템플릿: 참고 서식의 표 스타일(af9 = 표 테두리) 사용
        ids = [s.style_id for s in doc.styles]
        style_id = "af9" if "af9" in ids else ("TableGrid" if "TableGrid" in ids else None)
    for el in list(body):
        if not el.tag.endswith('sectPr'):
            body.remove(el)
    return doc, style_id


def add_episode(doc, style_id, ep, first=True):
    body = doc.element.body
    sect = body[-1]
    els = []
    if not first:
        els.append(para_xml("", page_break=True))
    els.append(para_xml(ep["title"], size=28, bold=True, center=True))
    els.append(para_xml("문답 30개 · 약 30분 · 진행자 질문 → 전문가 답 → 진행자 꼬리질문", size=18, center=True, color="666666"))
    for part in ep["parts"]:
        els.append(para_xml(""))
        els.append(para_xml(f"■ {part['name']}", size=21, bold=True))
        els.append(table_xml(style_id, part["qa"]))
    els.append(para_xml(""))
    els.append(para_xml("※ " + DISCLAIMER, size=16, color="666666"))
    for el in els:
        sect.addprevious(el)


def main():
    template, out = sys.argv[1], sys.argv[2]
    os.makedirs(out, exist_ok=True)
    files = sorted(glob.glob(os.path.join(HERE, "EP[0-9][0-9].md")))
    eps = [parse(f) for f in files]
    for f, ep in zip(files, eps):
        n = sum(len(p["qa"]) for p in ep["parts"])
        assert n == 30, f"{f}: {n} questions"
        doc, sid = new_doc(template)
        add_episode(doc, sid, ep)
        short = re.sub(r'[\\/:*?"<>|]', '', ep["title"]).replace(" ", "_")[:40]
        doc.save(os.path.join(out, f"{short}.docx"))
    doc, sid = new_doc(template)
    for i, ep in enumerate(eps):
        add_episode(doc, sid, ep, first=(i == 0))
    doc.save(os.path.join(out, f"보험콘텐츠_30문30답_{len(eps)}편_합본.docx"))
    print(f"{len(eps)} episodes → {out}")


if __name__ == "__main__":
    main()
