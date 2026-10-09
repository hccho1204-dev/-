// 화면에 나오는 모든 글자(장면 + 자막)를 onscreen.txt로 저장 — 숫자 검문용
const { chromium } = require(process.env.PW || "playwright");
const fs = require("fs"), path = require("path");
(async () => {
  const b = await chromium.launch(), p = await b.newPage({ viewport: { width: 1080, height: 1920 } });
  await p.goto("file://" + path.resolve("index.html"));
  const sc = JSON.parse(fs.readFileSync("scenes.json")), tm = JSON.parse(fs.readFileSync("timing.json"));
  await p.evaluate(([s, t]) => window.init(s, t), [sc, tm]);
  const txt = await p.evaluate(() => [...document.querySelectorAll(".scene")].map(e => { e.style.visibility = "visible"; e.querySelectorAll("[data-full]").forEach(n => n.textContent = n.dataset.full); return e.innerText; }).join("\n") + "\n" + document.querySelector("#bar").innerText);
  const subs = tm.scenes.flatMap(s => s.segs.map(g => g.text)).join("\n");
  fs.writeFileSync("onscreen.txt", txt + "\n" + subs + "\n");
  await b.close();
})();
