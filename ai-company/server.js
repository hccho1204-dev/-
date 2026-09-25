// AI 회사 관리 서버 — 실행: node server.js  →  브라우저에서 http://localhost:8787
const http = require('http');
const fs = require('fs');
const path = require('path');
const { P, company, agents, secrets, saveSecrets, secretsStatus } = require('./lib/env');
const store = require('./lib/store');
const wf = require('./lib/workflow');
const threads = require('./lib/threads');
const { mode } = require('./lib/llm');

const PORT = Number(process.env.PORT) || company().server?.port || 8787;
const MIME = { '.html': 'text/html; charset=utf-8', '.js': 'text/javascript; charset=utf-8', '.css': 'text/css; charset=utf-8', '.json': 'application/json', '.md': 'text/markdown; charset=utf-8', '.mp4': 'video/mp4', '.mov': 'video/quicktime', '.png': 'image/png', '.jpg': 'image/jpeg', '.svg': 'image/svg+xml' };

const send = (res, code, body, type = 'application/json; charset=utf-8') => {
  res.writeHead(code, { 'content-type': type, 'cache-control': 'no-store' });
  res.end(typeof body === 'string' || Buffer.isBuffer(body) ? body : JSON.stringify(body));
};
const ok = (res, body) => send(res, 200, body);
const fail = (res, e, code = 400) => send(res, code, { error: e.message || String(e) });

function readBody(req) {
  return new Promise((resolve, reject) => {
    let b = '';
    req.on('data', (c) => { b += c; if (b.length > 1e6) req.destroy(); });
    req.on('end', () => { try { resolve(b ? JSON.parse(b) : {}); } catch (e) { reject(new Error('잘못된 요청')); } });
  });
}

function listVideos() {
  return fs.readdirSync(P.videos).filter((f) => /\.(mp4|mov)$/i.test(f)).map((f) => ({ file: f, size: fs.statSync(path.join(P.videos, f)).size }));
}

function taskSummary(t) {
  return {
    id: t.id, title: t.title, instruction: t.instruction, stage: t.stage, status: t.status, round: t.round,
    deadline: t.deadline, approver: t.approver, taskType: t.taskType, createdAt: t.createdAt, updatedAt: t.updatedAt,
    running: wf.isRunning(t.id), publish: t.publish, strategy: t.strategy, usage: t.usage, error: t.error,
    headline: t.final?.report?.headline, lastReview: (t.reviews || []).slice(-1)[0] || null,
    assignments: (t.assignments || []).map((a) => ({ agent: a.agent, deliverable: a.deliverable, status: a.status, round: a.round, file: a.file, summary: a.summary })),
    lastMessage: (t.messages || []).slice(-1)[0] || null,
    hasReport: !!t.final?.report,
  };
}

// 내 컴퓨터(localhost)에서 온 요청인지. 터널(PUBLIC_URL)로 들어온 외부 요청은 영상 파일만 허용.
const isLocal = (req) => /^(localhost|127\.0\.0\.1|\[::1\])(:\d+)?$/.test(req.headers.host || '');

const routes = [];
const on = (method, pattern, fn) => routes.push({ method, re: new RegExp('^' + pattern.replace(/:(\w+)/g, '(?<$1>[^/]+)') + '$'), fn });

// ---------- 상태 ----------
on('GET', '/api/state', (req, res) => ok(res, {
  company: company(), agents: agents(), mode: mode(), secrets: secretsStatus(), threads: threads.status(),
  videos: listVideos(), stages: wf.STAGES, tasks: store.listTasks().map(taskSummary),
}));
on('GET', '/api/events', (req, res) => {
  res.writeHead(200, { 'content-type': 'text/event-stream', 'cache-control': 'no-store', connection: 'keep-alive' });
  res.write('retry: 2000\n\n');
  const h = (e) => res.write(`data: ${JSON.stringify(e)}\n\n`);
  store.bus.on('event', h);
  const ping = setInterval(() => res.write(': ping\n\n'), 20000);
  req.on('close', () => { store.bus.off('event', h); clearInterval(ping); });
});

// ---------- 업무 ----------
on('POST', '/api/tasks', async (req, res) => ok(res, taskSummary(wf.create(await readBody(req)))));
on('GET', '/api/tasks/:id', (req, res, p) => { const t = store.getTask(p.id); t ? ok(res, { ...t, running: wf.isRunning(t.id) }) : fail(res, new Error('없음'), 404); });
on('POST', '/api/tasks/:id/reinforce', async (req, res, p) => ok(res, taskSummary(wf.reinforce(p.id, (await readBody(req)).text))));
on('POST', '/api/tasks/:id/approve', async (req, res, p) => ok(res, taskSummary(wf.approve(p.id, await readBody(req)))));
on('POST', '/api/tasks/:id/manual-published', async (req, res, p) => ok(res, taskSummary(wf.manualPublished(p.id, (await readBody(req)).permalink))));
on('POST', '/api/tasks/:id/cancel', (req, res, p) => ok(res, taskSummary(wf.cancel(p.id))));
on('POST', '/api/tasks/:id/retry', (req, res, p) => ok(res, taskSummary(wf.retry(p.id))));
on('POST', '/api/tasks/:id/insights', async (req, res, p) => ok(res, await wf.refreshInsights(p.id)));
on('GET', '/api/doc/:id/:file', (req, res, p) => {
  const d = store.readDoc(p.id, p.file);
  if (d == null) return fail(res, new Error('문서 없음'), 404);
  send(res, 200, d, p.file.endsWith('.html') ? MIME['.html'] : 'text/plain; charset=utf-8');
});
on('GET', '/api/docs', (req, res) => ok(res, store.docIndex(200)));

// ---------- 회사 기억 / 완료 기준 ----------
on('GET', '/api/text/:kind', (req, res, p) => {
  const e = store.EDITABLE[p.kind];
  if (!e) return fail(res, new Error('없음'), 404);
  ok(res, e.files.map((name) => ({ name, content: store.readEditable(p.kind, name) })));
});
on('POST', '/api/text/:kind/:name', async (req, res, p) => {
  store.writeEditable(p.kind, p.name, (await readBody(req)).content) ? ok(res, { saved: true }) : fail(res, new Error('저장할 수 없는 파일'));
});

// ---------- 설정 / 쓰레드 ----------
on('POST', '/api/settings', async (req, res) => { saveSecrets(await readBody(req)); ok(res, { secrets: secretsStatus(), mode: mode() }); });
on('GET', '/api/threads/auth-url', (req, res) => ok(res, { url: threads.authUrl(), redirectUri: secrets().THREADS_REDIRECT_URI }));
on('POST', '/api/threads/code', async (req, res) => ok(res, await threads.exchangeCode((await readBody(req)).code)));
on('POST', '/api/threads/token', async (req, res) => ok(res, await threads.useToken((await readBody(req)).token)));
on('POST', '/api/threads/test', async (req, res) => {
  const text = (await readBody(req)).text || `연결 시험 중입니다. (${new Date().toLocaleString('ko-KR')})`;
  ok(res, await threads.publish(text.slice(0, 500)));
});
on('GET', '/threads-callback', async (req, res) => {
  try {
    await threads.exchangeCode(req.url);
    send(res, 200, '<meta charset="utf-8"><h2>✅ 쓰레드 연결 완료</h2><p>이 창을 닫고 관리 화면으로 돌아가세요.</p>', MIME['.html']);
  } catch (e) { send(res, 400, `<meta charset="utf-8"><h2>연결 실패</h2><p>${String(e.message).replace(/</g, '&lt;')}</p>`, MIME['.html']); }
});

// ---------- 정적 파일 ----------
function serveFile(res, file, req) {
  if (!fs.existsSync(file) || !fs.statSync(file).isFile()) return fail(res, new Error('없음'), 404);
  const type = MIME[path.extname(file).toLowerCase()] || 'application/octet-stream';
  const size = fs.statSync(file).size;
  const range = req.headers.range && /bytes=(\d*)-(\d*)/.exec(req.headers.range);
  if (range && type.startsWith('video')) {
    const start = range[1] ? Number(range[1]) : 0;
    const end = range[2] ? Number(range[2]) : size - 1;
    res.writeHead(206, { 'content-type': type, 'content-range': `bytes ${start}-${end}/${size}`, 'accept-ranges': 'bytes', 'content-length': end - start + 1 });
    return fs.createReadStream(file, { start, end }).pipe(res);
  }
  res.writeHead(200, { 'content-type': type, 'content-length': size, 'accept-ranges': 'bytes' });
  fs.createReadStream(file).pipe(res);
}

const server = http.createServer(async (req, res) => {
  const url = new URL(req.url, 'http://x');
  const pathname = decodeURIComponent(url.pathname);

  // 쓰레드 서버가 영상을 가져가는 경로 (외부 접근 허용: content/videos 폴더의 영상만)
  if (req.method === 'GET' && pathname.startsWith('/media/')) {
    const f = path.basename(pathname.slice(7));
    if (!/\.(mp4|mov)$/i.test(f)) return fail(res, new Error('없음'), 404);
    return serveFile(res, path.join(P.videos, f), req);
  }
  if (!isLocal(req) && pathname !== '/threads-callback') return fail(res, new Error('외부 접근 차단'), 403);

  for (const r of routes) {
    const m = req.method === r.method && r.re.exec(pathname);
    if (!m) continue;
    try { return await r.fn(req, res, m.groups || {}); } catch (e) { return fail(res, e); }
  }
  if (req.method === 'GET' && pathname.startsWith('/preview/')) return serveFile(res, path.join(P.videos, path.basename(pathname.slice(9))), req);
  if (req.method === 'GET') {
    const f = path.join(P.public, pathname === '/' ? 'index.html' : path.normalize(pathname).replace(/^([/\\])+/, ''));
    if (f.startsWith(P.public)) return serveFile(res, f, req);
  }
  fail(res, new Error('없음'), 404);
});

server.listen(PORT, '127.0.0.1', () => {
  const m = mode();
  console.log('');
  console.log('  ==============================================');
  console.log(`   ${company().name} 가동 중`);
  console.log(`   관리 화면:  http://localhost:${PORT}`);
  console.log(`   모드: ${m.demo ? '체험 모드 (API 키 없음 — 가짜 응답)' : `실전 모드 (클로드${m.gpt ? ' + GPT' : ''})`}`);
  console.log('   끄려면 이 창에서 Ctrl + C');
  console.log('  ==============================================');
  console.log('');
  wf.resumeAll();
  threads.refreshIfNeeded();
});
