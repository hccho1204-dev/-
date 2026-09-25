// 경로, 설정, 비밀값(API 키) 관리
const fs = require('fs');
const path = require('path');

const ROOT = path.resolve(__dirname, '..');
const P = {
  root: ROOT,
  config: path.join(ROOT, 'config'),
  data: path.join(ROOT, 'data'),
  tasks: path.join(ROOT, 'data', 'tasks'),
  workspace: path.join(ROOT, 'workspace'),
  memory: path.join(ROOT, 'memory'),
  standards: path.join(ROOT, 'standards'),
  videos: path.join(ROOT, 'content', 'videos'),
  public: path.join(ROOT, 'public'),
};
for (const d of [P.data, P.tasks, P.workspace, P.videos]) fs.mkdirSync(d, { recursive: true });

function readJSON(file, fallback) {
  try { return JSON.parse(fs.readFileSync(file, 'utf8')); } catch { return fallback; }
}
function writeJSON(file, obj) {
  const tmp = file + '.tmp';
  fs.writeFileSync(tmp, JSON.stringify(obj, null, 2));
  fs.renameSync(tmp, file);
}

const company = () => readJSON(path.join(P.config, 'company.json'), {});
const agents = () => readJSON(path.join(P.config, 'agents.json'), []);
const agent = (id) => agents().find((a) => a.id === id);

// .env 파일도 읽는다 (선택). 관리 화면에서 입력한 값은 data/secrets.json 에 저장된다.
function loadDotEnv() {
  const f = path.join(ROOT, '.env');
  if (!fs.existsSync(f)) return {};
  const out = {};
  for (const line of fs.readFileSync(f, 'utf8').split(/\r?\n/)) {
    const m = line.match(/^\s*([A-Z0-9_]+)\s*=\s*(.*)\s*$/);
    if (m) out[m[1]] = m[2].replace(/^["']|["']$/g, '');
  }
  return out;
}

const SECRET_KEYS = ['ANTHROPIC_API_KEY', 'OPENAI_API_KEY', 'THREADS_APP_ID', 'THREADS_APP_SECRET', 'THREADS_REDIRECT_URI', 'PUBLIC_URL'];
const secretsFile = path.join(P.data, 'secrets.json');

function secrets() {
  const env = loadDotEnv();
  const saved = readJSON(secretsFile, {});
  const out = {};
  for (const k of SECRET_KEYS) out[k] = saved[k] || process.env[k] || env[k] || '';
  if (!out.THREADS_REDIRECT_URI) out.THREADS_REDIRECT_URI = 'https://localhost/threads-callback';
  out.PUBLIC_URL = out.PUBLIC_URL.replace(/\/+$/, '');
  return out;
}
function saveSecrets(patch) {
  const saved = readJSON(secretsFile, {});
  for (const k of SECRET_KEYS) if (typeof patch[k] === 'string') saved[k] = patch[k].trim();
  writeJSON(secretsFile, saved);
}
// 화면에는 키 값 대신 "설정됨/미설정"과 끝 4자리만 보여준다
function secretsStatus() {
  const s = secrets();
  const out = {};
  for (const k of SECRET_KEYS) {
    const v = s[k];
    const isKey = /KEY|SECRET/.test(k);
    out[k] = { set: !!v, preview: !v ? '' : isKey ? '••••' + v.slice(-4) : v };
  }
  return out;
}

module.exports = { P, readJSON, writeJSON, company, agents, agent, secrets, saveSecrets, secretsStatus };
