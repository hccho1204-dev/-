"""숏폼 문답형(EPxx.md, 편당 5개) → 롱폼과 같은 3칸 표 서식 워드 파일.

사용: python3 build_shorts.py <출력폴더>
- 편별 EPxx_숏폼5개.docx 25개, 125개 합본 1개, 우선공개 5개(EP02·05·10·14·19의 숏폼 1) 1개.
"""
import glob, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "문답형"))
from build_docx import new_doc, table_xml, para_xml  # noqa: E402

TEMPLATE = os.path.join(HERE, "..", "문답형", "서식_템플릿.docx")
CIRCLED = "①②③④⑤"
PRIORITY = ["EP02", "EP05", "EP10", "EP14", "EP19"]
SYL_PER_SEC = 4.6  # 분당 약 275음절


def parse(path):
    ep = {"title": "", "shorts": []}
    cur = qa = None
    for raw in open(path, encoding="utf-8"):
        line = raw.strip()
        if line.startswith("# "):
            ep["title"] = line[2:].strip()
        elif line.startswith("## SHORT"):
            name = line.split("|", 1)[1].strip() if "|" in line else line
            cur = {"name": name, "hook": "", "qa": [], "end": ""}
            ep["shorts"].append(cur)
        elif line.startswith("HOOK:"):
            cur["hook"] = line[5:].strip()
        elif line.startswith("### "):
            qa = {"n": line[4:].strip(), "q": "", "a": [], "f": ""}
            cur["qa"].append(qa)
        elif line.startswith("Q: "):
            qa["q"] = line[3:].strip()
        elif line.startswith("A: "):
            qa["a"].append(line[3:].strip())
        elif line.startswith("F: "):
            qa["f"] = line[3:].strip()
        elif line.startswith("END:"):
            cur["end"] = line[4:].strip()
    return ep


def seconds(sh):
    text = " ".join([q["q"] + " ".join(q["a"]) + q["f"] for q in sh["qa"]] + [sh["end"]])
    return round(len(re.findall("[가-힣]", text)) / SYL_PER_SEC / 5) * 5


def add_short(doc, sid, label, sh):
    sect = doc.element.body[-1]
    for el in [
        para_xml(""),
        para_xml(f"{label} {sh['name']}", size=22, bold=True),
        para_xml(f"첫 화면 자막(0~3초): {sh['hook']}   ·   약 {seconds(sh)}초", size=18, color="C00000"),
        table_xml(sid, sh["qa"]),
        para_xml(f"마무리 멘트: {sh['end']}", size=19, bold=True),
    ]:
        sect.addprevious(el)


def add_header(doc, title, sub, page_break):
    sect = doc.element.body[-1]
    if page_break:
        sect.addprevious(para_xml("", page_break=True))
    sect.addprevious(para_xml(title, size=28, bold=True, center=True))
    sect.addprevious(para_xml(sub, size=18, center=True, color="666666"))


def main():
    out = sys.argv[1]
    os.makedirs(out, exist_ok=True)
    files = sorted(glob.glob(os.path.join(HERE, "EP[0-9][0-9].md")))
    eps = {os.path.basename(f)[:4]: parse(f) for f in files}
    for key, ep in eps.items():
        assert len(ep["shorts"]) == 5, f"{key}: {len(ep['shorts'])} shorts"
    sub = "숏폼 5개 · 각 40~60초 · 진행자 질문 → 전문가 답 → 진행자 꼬리질문"

    combo, csid = new_doc(TEMPLATE)
    for i, (key, ep) in enumerate(eps.items()):
        doc, sid = new_doc(TEMPLATE)
        for d, s, pb in ((doc, sid, False), (combo, csid, i > 0)):
            add_header(d, f"{ep['title']} — 숏폼", sub, pb)
            for j, sh in enumerate(ep["shorts"]):
                add_short(d, s, f"숏폼{CIRCLED[j]}", sh)
        doc.save(os.path.join(out, f"{key}_숏폼5개.docx"))
    combo.save(os.path.join(out, f"보험콘텐츠_숏폼_{len(eps) * 5}개_합본.docx"))

    pri, psid = new_doc(TEMPLATE)
    add_header(pri, "우선 공개 숏폼 5개", "먼저 올릴 5개 · 각 편 숏폼① 기준", False)
    for k, key in enumerate(k for k in PRIORITY if k in eps):
        add_short(pri, psid, f"{k + 1}번 ({eps[key]['title'].split('.')[0]})", eps[key]["shorts"][0])
    pri.save(os.path.join(out, "우선공개_숏폼5개.docx"))
    print(f"{len(eps)} episodes → {out}")


if __name__ == "__main__":
    main()
