// 업무(task) 저장소, 작업 문서(workspace), 회사 기억(memory)
const fs = require('fs');
const path = require('path');
const { EventEmitter } = require('events');
const { P, readJSON, writeJSON } = require('./env');

const bus = new EventEmitter();
bus.setMaxListeners(100);

const safeId = (id) => /^[\w-]+$/.test(String(id || ''));
const taskFile = (id) => path.join(P.tasks, id + '.json');

function newId() {
  const d = new Date();
  const p = (n) => String(n).padStart(2, '0');
  return `T${d.getFullYear()}${p(d.getMonth() + 1)}${p(d.getDate())}-${p(d.getHours())}${p(d.getMinutes())}${p(d.getSeconds())}`;
}
function getTask(id) {
  if (!safeId(id)) return null;
  return readJSON(taskFile(id), null);
}
function saveTask(t) {
  t.updatedAt = new Date().toISOString();
  writeJSON(taskFile(t.id), t);
  bus.emit('event', { type: 'task', id: t.id });
}
function listTasks() {
  return fs.readdirSync(P.tasks)
    .filter((f) => f.endsWith('.json'))
    .map((f) => readJSON(path.join(P.tasks, f), null))
    .filter(Boolean)
    .sort((a, b) => (b.createdAt || '').localeCompare(a.createdAt || ''));
}

// ---------- 작업 문서 ----------
const taskDir = (id) => path.join(P.workspace, id);
function saveDoc(taskId, file, content) {
  fs.mkdirSync(taskDir(taskId), { recursive: true });
  fs.writeFileSync(path.join(taskDir(taskId), file), content);
}
function readDoc(taskId, file) {
  if (!safeId(taskId) || !/^[\w.-]+$/.test(file)) return null;
  const f = path.join(taskDir(taskId), file);
  return fs.existsSync(f) ? fs.readFileSync(f, 'utf8') : null;
}
// 문서 맨 윗줄 "> 한줄요약: ..." 만 읽는다 (토큰 절약 장치)
function firstLineSummary(text) {
  const line = String(text || '').split(/\r?\n/).find((l) => l.trim()) || '';
  return line.replace(/^>\s*/, '').replace(/^한줄요약\s*[:：]\s*/, '').trim();
}
function readSummaryOnly(file) {
  try {
    const fd = fs.openSync(file, 'r');
    const buf = Buffer.alloc(600);
    const n = fs.readSync(fd, buf, 0, 600, 0);
    fs.closeSync(fd);
    return firstLineSummary(buf.slice(0, n).toString('utf8'));
  } catch { return ''; }
}
function docIndex(limit = 40) {
  const out = [];
  if (!fs.existsSync(P.workspace)) return out;
  const dirs = fs.readdirSync(P.workspace).filter(safeId).sort().reverse();
  for (const d of dirs) {
    const full = path.join(P.workspace, d);
    if (!fs.statSync(full).isDirectory()) continue;
    for (const f of fs.readdirSync(full).filter((x) => x.endsWith('.md')).sort()) {
      out.push({ task: d, file: f, summary: readSummaryOnly(path.join(full, f)) });
      if (out.length >= limit) return out;
    }
  }
  return out;
}

// ---------- 회사 기억 ----------
const memFile = (name) => path.join(P.memory, name);
function readMemory(name) {
  try { return fs.readFileSync(memFile(name), 'utf8'); } catch { return ''; }
}
function appendMemory(name, line) {
  const d = new Date().toISOString().slice(0, 10);
  fs.appendFileSync(memFile(name), `- [${d}] ${line.replace(/\s+/g, ' ').trim()}\n`);
  bus.emit('event', { type: 'memory' });
}

// 편집 가능한 텍스트 파일(회사 기억, 완료 기준)
const EDITABLE = {
  memory: { dir: P.memory, files: ['company-memory.md', 'lessons.md'] },
  standards: { dir: P.standards, files: ['threads-post.md', 'analysis.md', 'general.md', 'ceo-report.md', 'README.md'] },
};
function readEditable(kind, name) {
  const e = EDITABLE[kind];
  if (!e || !e.files.includes(name)) return null;
  try { return fs.readFileSync(path.join(e.dir, name), 'utf8'); } catch { return ''; }
}
function writeEditable(kind, name, content) {
  const e = EDITABLE[kind];
  if (!e || !e.files.includes(name)) return false;
  fs.writeFileSync(path.join(e.dir, name), String(content));
  bus.emit('event', { type: kind });
  return true;
}

module.exports = {
  bus, newId, getTask, saveTask, listTasks, saveDoc, readDoc, firstLineSummary, docIndex,
  readMemory, appendMemory, EDITABLE, readEditable, writeEditable, taskDir,
};
