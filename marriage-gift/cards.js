// 카드뉴스 PNG 10장 만들기: node cards.js → out/cards/card_01.png ~ card_10.png
let chromium; try { ({ chromium } = require("playwright")); } catch { ({ chromium } = require("/opt/node-tools/node_modules/playwright")); }
const fs = require("fs"), path = require("path");
(async () => {
  const dir = path.join(__dirname, "out", "cards"); fs.mkdirSync(dir, { recursive: true });
  const b = await chromium.launch(), p = await b.newPage({ viewport: { width: 1080, height: 1350 } });
  const errs = []; p.on("pageerror", e => errs.push(e.message));
  await p.goto("file://" + path.join(__dirname, "index.html") + "?render&ar=card"); await p.evaluate(() => window.ready);
  for (let i = 0; i < 10; i++) {
    await p.evaluate(i => window.renderCard(i), i);
    const b64 = await p.evaluate(() => document.getElementById("c").toDataURL("image/png").split(",")[1]);
    fs.writeFileSync(path.join(dir, `card_${String(i + 1).padStart(2, "0")}.png`), Buffer.from(b64, "base64"));
  }
  console.log(errs.length ? "ERRORS " + errs.join(" | ") : "10 cards ok"); await b.close();
})();
