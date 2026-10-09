// 사용법: node render.js preview t1,t2,...   |   node render.js chunk <시작프레임> <끝프레임> <출력.mp4>
const { chromium } = require(process.env.PW || "playwright");
const fs = require("fs"), path = require("path"), { spawn } = require("child_process");
const FPS = 30;
(async () => {
  const [mode, a, b, out] = process.argv.slice(2);
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1080, height: 1920 } });
  await page.goto("file://" + path.resolve("index.html"));
  await page.evaluate(([s, t]) => window.init(s, t), [JSON.parse(fs.readFileSync("scenes.json")), JSON.parse(fs.readFileSync("timing.json"))]);
  await page.evaluate(() => document.fonts.ready);
  if (mode === "preview") {
    fs.mkdirSync("preview", { recursive: true });
    for (const t of a.split(",").map(Number)) {
      await page.evaluate(t => window.renderAt(t), t);
      await page.screenshot({ path: `preview/t${t.toFixed(2)}.png` });
    }
  } else {
    const ff = spawn("ffmpeg", ["-v", "error", "-y", "-f", "image2pipe", "-framerate", String(FPS), "-c:v", "mjpeg", "-i", "-",
      "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p", out], { stdio: ["pipe", "inherit", "inherit"] });
    for (let f = +a; f < +b; f++) {
      await page.evaluate(t => window.renderAt(t), f / FPS);
      const buf = await page.screenshot({ type: "jpeg", quality: 92 });
      if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once("drain", r));
      if ((f - a) % 600 === 0) console.log(out, f, "/", b);
    }
    ff.stdin.end(); await new Promise(r => ff.on("close", r));
  }
  await browser.close();
})();
