#!/usr/bin/env node
/*
 * render.js — 모션그래픽 HTML을 MP4 영상으로 저장
 *
 * 사용법:
 *   node render.js projects/01-ppt-evolution/index.html
 *   node render.js projects/02-bless-ad/index.html --vertical           (세로 1080x1920)
 *   node render.js <html> --audio narration.mp3 --fps 60 --out output/my.mp4
 *
 * 옵션:
 *   --out <파일>       저장 경로 (기본: output/<프로젝트폴더명>[-vertical].mp4)
 *   --fps <숫자>       초당 프레임 (기본 30)
 *   --vertical         세로(9:16, 1080x1920)로 렌더링
 *   --size <WxH>       해상도 직접 지정 (예: 1280x720)
 *   --audio <파일>     나레이션/음악 합치기 (영상 길이에 맞춰 자름)
 *   --from <초> --to <초>   일부 구간만 렌더링 (빠른 확인용)
 */
const path = require('path');
const fs = require('fs');
const { spawn } = require('child_process');

function loadPlaywright() {
  try { return require('playwright'); } catch {}
  const globalRoot = require('child_process').execSync('npm root -g').toString().trim();
  return require(path.join(globalRoot, 'playwright'));
}

function parseArgs(argv) {
  const a = { fps: 30 };
  for (let i = 0; i < argv.length; i++) {
    const k = argv[i];
    if (k === '--out') a.out = argv[++i];
    else if (k === '--fps') a.fps = +argv[++i];
    else if (k === '--vertical') a.size = '1080x1920';
    else if (k === '--size') a.size = argv[++i];
    else if (k === '--audio') a.audio = argv[++i];
    else if (k === '--from') a.from = +argv[++i];
    else if (k === '--to') a.to = +argv[++i];
    else if (!a.html) a.html = k;
  }
  return a;
}

(async () => {
  const args = parseArgs(process.argv.slice(2));
  if (!args.html) {
    console.log('사용법: node render.js <html 파일> [--vertical] [--audio 파일] [--fps 30] [--out 파일]');
    process.exit(1);
  }
  const htmlPath = path.resolve(args.html);
  const name = path.basename(path.dirname(htmlPath));
  const suffix = args.size === '1080x1920' ? '-vertical' : args.size ? `-${args.size}` : '';
  const out = path.resolve(args.out || path.join(__dirname, 'output', `${name}${suffix}.mp4`));
  fs.mkdirSync(path.dirname(out), { recursive: true });

  const query = new URLSearchParams({ render: '1' });
  if (args.size) { const [w, h] = args.size.split('x'); query.set('w', w); query.set('h', h); }

  const { chromium } = loadPlaywright();
  const launch = { args: ['--force-color-profile=srgb', '--disable-lcd-text'] };
  const browser = await chromium.launch(launch);

  // 1) 크기 확인용으로 한 번 열기
  let page = await browser.newPage();
  await page.goto('file://' + htmlPath + '?' + query);
  await page.waitForFunction(() => window.__DURATION !== undefined);
  const { width, height } = await page.evaluate(() => window.__SIZE);
  const duration = await page.evaluate(() => window.__DURATION);
  await page.close();

  page = await browser.newPage({ viewport: { width, height }, deviceScaleFactor: 1 });
  await page.goto('file://' + htmlPath + '?' + query);
  await page.waitForFunction(() => window.__seek !== undefined);
  await page.evaluate(() => document.fonts && document.fonts.ready);

  const from = args.from || 0;
  const to = Math.min(args.to ?? duration, duration);
  const total = Math.round((to - from) * args.fps);
  console.log(`🎬 ${name}: ${width}x${height}, ${(to - from).toFixed(2)}초, ${args.fps}fps → ${total}프레임`);

  const ff = ['-y', '-f', 'image2pipe', '-framerate', String(args.fps), '-i', '-'];
  if (args.audio) ff.push('-ss', String(from), '-i', path.resolve(args.audio));
  ff.push('-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-preset', 'medium', '-crf', '18', '-movflags', '+faststart');
  if (args.audio) ff.push('-c:a', 'aac', '-b:a', '192k', '-shortest');
  ff.push(out);
  const ffmpeg = spawn('ffmpeg', ff, { stdio: ['pipe', 'ignore', 'pipe'] });
  let ffErr = '';
  ffmpeg.stderr.on('data', d => (ffErr += d));

  const stage = await page.$('#stage');
  for (let i = 0; i < total; i++) {
    const t = from + i / args.fps;
    await page.evaluate(t => window.__seek(t), t);
    const buf = await stage.screenshot({ type: 'png' });
    if (!ffmpeg.stdin.write(buf)) await new Promise(r => ffmpeg.stdin.once('drain', r));
    if (i % args.fps === 0) process.stdout.write(`\r  ${Math.round((i / total) * 100)}%`);
  }
  ffmpeg.stdin.end();
  const code = await new Promise(r => ffmpeg.on('close', r));
  await browser.close();
  if (code !== 0) { console.error('\nffmpeg 오류:\n' + ffErr.slice(-2000)); process.exit(1); }
  console.log(`\r  100%\n✅ 저장 완료: ${path.relative(process.cwd(), out)}`);
})();
