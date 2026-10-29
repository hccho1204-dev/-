// 사용법: node instagram/render-card.js "제목<br>둘째줄" "부제<br>둘째줄" instagram/cards/YYYY-MM-DD.jpg
const fs = require('fs'), path = require('path');
const { chromium } = require('playwright');
(async () => {
  const [title, sub, out] = process.argv.slice(2);
  const tpl = fs.readFileSync(path.join(__dirname, 'card-template.html'), 'utf8');
  const html = tpl.replace('{{TITLE}}', title).replace('{{SUB}}', sub);
  const tmp = path.join(require('os').tmpdir(), 'bless-card.html');
  fs.writeFileSync(tmp, html);
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 1080, height: 1350 } });
  await p.goto('file://' + tmp);
  await p.evaluate(() => document.fonts.ready);
  await p.waitForTimeout(1500);
  await p.screenshot({ path: out, type: 'jpeg', quality: 92 });
  await b.close();
})();
