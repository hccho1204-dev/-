/*
 * 모벨릭스 광고 index.html 애니메이션을 30fps MP4로 렌더링 (음악 포함)
 *   node render.js            → 가로/세로 둘 다
 *   node render.js 16x9       → 가로만
 *   node render.js storyboard → 스토리보드 이미지만
 */
const http = require("http");
const fs = require("fs");
const path = require("path");
const { spawn } = require("child_process");
let chromium;
try { ({ chromium } = require("playwright")); } catch { ({ chromium } = require("/opt/node-tools/node_modules/playwright")); }

const ROOT = __dirname, OUT = path.join(ROOT, "out");
const FPS = 30, DUR = 20;
// 인스타 아이디: INSTA=@아이디 node render.js  (없으면 index.html 기본값 사용)
const INSTA = process.env.INSTA || "";
const TYPES = { ".jpg": "image/jpeg", ".html": "text/html", ".ttf": "font/ttf", ".wav": "audio/wav", ".js": "text/javascript" };

function serve() {
  return new Promise(res => {
    const srv = http.createServer((req, rsp) => {
      const p = path.join(ROOT, decodeURIComponent(req.url.split("?")[0]));
      fs.readFile(p, (e, d) => {
        if (e) { rsp.writeHead(404); return rsp.end(); }
        rsp.writeHead(200, { "Content-Type": TYPES[path.extname(p)] || "application/octet-stream" });
        rsp.end(d);
      });
    }).listen(0, () => res(srv));
  });
}

async function openPage(browser, port, ar) {
  const [w, h] = ar === "9x16" ? [1080, 1920] : [1920, 1080];
  const page = await browser.newPage({ viewport: { width: w, height: h } });
  await page.goto(`http://localhost:${port}/index.html?render&ar=${ar}${INSTA ? "&insta=" + encodeURIComponent(INSTA) : ""}`);
  await page.evaluate(() => window.ready);
  return page;
}

const grab = page => page.evaluate(() => document.getElementById("c").toDataURL("image/png").split(",")[1]);

async function renderVideo(browser, port, ar) {
  const page = await openPage(browser, port, ar);
  const file = path.join(OUT, `mobelix_${ar}.mp4`);
  const ff = spawn("ffmpeg", ["-y", "-loglevel", "error",
    "-f", "image2pipe", "-framerate", String(FPS), "-i", "-",
    "-i", path.join(OUT, "music.wav"),
    "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-maxrate", "10M", "-bufsize", "20M", "-pix_fmt", "yuv420p",
    "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", file], { stdio: ["pipe", "inherit", "inherit"] });
  const total = FPS * DUR;
  for (let f = 0; f < total; f++) {
    await page.evaluate(t => window.renderFrame(t), f / FPS);
    const b64 = await grab(page);
    if (!ff.stdin.write(Buffer.from(b64, "base64"))) await new Promise(r => ff.stdin.once("drain", r));
    if (f % 60 === 0) process.stdout.write(`\r[${ar}] ${f}/${total}`);
  }
  ff.stdin.end();
  await new Promise(r => ff.on("close", r));
  console.log(`\r[${ar}] 완료 → ${path.relative(ROOT, file)}`);
  await page.close();
}

// 장면별 대표 컷 10장을 한 장의 스토리보드로
async function storyboard(browser, port, ar) {
  const page = await openPage(browser, port, ar);
  const times = [0.95, 2.2, 3.3, 6.1, 8.1, 9.5, 12.3, 14.0, 17.4, 19.5];
  const dir = path.join(OUT, `sb_${ar}`);
  fs.mkdirSync(dir, { recursive: true });
  for (let i = 0; i < times.length; i++) {
    await page.evaluate(t => window.renderFrame(t), times[i]);
    fs.writeFileSync(path.join(dir, `${String(i).padStart(2, "0")}.png`), Buffer.from(await grab(page), "base64"));
  }
  await page.close();
  const tile = ar === "9x16" ? "5x2" : "5x2";
  const scale = ar === "9x16" ? "324:576" : "576:324";
  await new Promise(r => spawn("ffmpeg", ["-y", "-loglevel", "error", "-i", path.join(dir, "%02d.png"),
    "-vf", `scale=${scale},pad=iw+16:ih+16:8:8:white,tile=${tile}:padding=0:color=white`, "-frames:v", "1",
    path.join(OUT, `storyboard_${ar}.png`)], { stdio: "inherit" }).on("close", r));
  fs.rmSync(dir, { recursive: true });
  console.log(`스토리보드 → out/storyboard_${ar}.png`);
}

(async () => {
  fs.mkdirSync(OUT, { recursive: true });
  if (!fs.existsSync(path.join(OUT, "music.wav"))) { console.error("먼저 python3 music.py 를 실행하세요"); process.exit(1); }
  const arg = process.argv[2];
  const srv = await serve();
  const port = srv.address().port;
  const browser = await chromium.launch();
  try {
    if (arg === "storyboard") { for (const ar of ["16x9", "9x16"]) await storyboard(browser, port, ar); }
    else {
      const ars = arg ? [arg] : ["16x9", "9x16"];
      for (const ar of ars) { await storyboard(browser, port, ar); await renderVideo(browser, port, ar); }
    }
  } finally { await browser.close(); srv.close(); }
})();
