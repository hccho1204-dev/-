#!/usr/bin/env python3
"""results.json을 대시보드 HTML에 끼워 넣는다.

사용법: python3 build_dashboard.py results.json dashboard.html
"""
import json
import sys
from pathlib import Path

tpl = Path(__file__).resolve().parent.parent / "assets" / "dashboard_template.html"
data = json.load(open(sys.argv[1], encoding="utf-8"))
html = tpl.read_text(encoding="utf-8").replace(
    "/*__DATA__*/null", json.dumps(data, ensure_ascii=False).replace("</", "<\\/"))
Path(sys.argv[2]).write_text(html, encoding="utf-8")
print(f"대시보드 저장 → {sys.argv[2]}")
