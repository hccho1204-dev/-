"""lessons/*.md, README.md, SELF_CHECK.md 를 읽어 공부 허브 페이지(hub.html)를 만든다."""
import json, pathlib, re

ROOT = pathlib.Path(__file__).resolve().parent.parent
lessons = []
for p in sorted((ROOT / "lessons").glob("day*.md")):
    text = p.read_text(encoding="utf-8")
    first = text.splitlines()[0].lstrip("# ").strip()
    day = int(re.search(r"day(\d+)", p.stem).group(1))
    lessons.append({"day": day, "title": first, "md": text})
data = {
    "curriculum": (ROOT / "README.md").read_text(encoding="utf-8"),
    "selfcheck": (ROOT / "SELF_CHECK.md").read_text(encoding="utf-8"),
    "lessons": lessons,
}
tpl = (pathlib.Path(__file__).parent / "template.html").read_text(encoding="utf-8")
payload = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
(pathlib.Path(__file__).parent / "hub.html").write_text(tpl.replace("__DATA__", payload), encoding="utf-8")
print(f"hub.html built with {len(lessons)} lesson(s)")
