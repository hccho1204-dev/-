// 쓰레드(Threads) API 연결: 로그인(OAuth) → 토큰 저장 → 게시 → 성과(인사이트) 조회
const path = require('path');
const crypto = require('crypto');
const { P, readJSON, writeJSON, secrets } = require('./env');

const GRAPH = 'https://graph.threads.net';
const tokenFile = path.join(P.data, 'threads.json');
const SCOPES = ['threads_basic', 'threads_content_publish', 'threads_manage_replies', 'threads_read_replies', 'threads_manage_insights'];
let pendingState = null;

const load = () => readJSON(tokenFile, null);
const save = (o) => writeJSON(tokenFile, o);

function status() {
  const t = load();
  if (!t) return { connected: false };
  return { connected: true, username: t.username, userId: t.userId, savedAt: t.savedAt, expiresAt: t.expiresAt };
}

function authUrl() {
  const s = secrets();
  if (!s.THREADS_APP_ID) throw new Error('먼저 설정에서 쓰레드 앱 ID(THREADS_APP_ID)를 입력하세요');
  pendingState = crypto.randomBytes(8).toString('hex');
  const q = new URLSearchParams({
    client_id: s.THREADS_APP_ID,
    redirect_uri: s.THREADS_REDIRECT_URI,
    scope: SCOPES.join(','),
    response_type: 'code',
    state: pendingState,
  });
  return `https://threads.net/oauth/authorize?${q}`;
}

async function api(method, urlPath, params = {}) {
  const url = new URL(urlPath.startsWith('http') ? urlPath : GRAPH + urlPath);
  const opts = { method };
  if (method === 'GET') for (const [k, v] of Object.entries(params)) url.searchParams.set(k, v);
  else opts.body = new URLSearchParams(params);
  const r = await fetch(url, opts);
  const j = await r.json().catch(() => ({}));
  if (!r.ok || j.error) throw new Error(`쓰레드 API 오류: ${j.error?.message || j.error_message || r.status}`);
  return j;
}

async function finishLogin(shortToken, userId) {
  const s = secrets();
  let token = shortToken, expiresIn = 3600;
  try { // 60일짜리 장기 토큰으로 교환
    const long = await api('GET', '/access_token', { grant_type: 'th_exchange_token', client_secret: s.THREADS_APP_SECRET, access_token: shortToken });
    token = long.access_token; expiresIn = long.expires_in || expiresIn;
  } catch { /* 이미 장기 토큰이면 교환 실패해도 괜찮다 */ }
  const me = await api('GET', '/v1.0/me', { fields: 'id,username', access_token: token });
  const obj = {
    token, userId: me.id || userId, username: me.username,
    savedAt: new Date().toISOString(), expiresAt: new Date(Date.now() + expiresIn * 1000).toISOString(),
  };
  save(obj);
  return status();
}

// 로그인 후 받은 주소 전체(또는 code 값)를 붙여넣으면 연결 완료
async function exchangeCode(input) {
  const s = secrets();
  if (!s.THREADS_APP_ID || !s.THREADS_APP_SECRET) throw new Error('앱 ID와 앱 시크릿 코드를 먼저 설정하세요');
  let code = String(input || '').trim();
  if (code.includes('code=')) {
    const u = new URL(code.startsWith('http') ? code : 'https://x/?' + code.split('?').pop());
    const st = u.searchParams.get('state');
    if (pendingState && st && st !== pendingState) throw new Error('로그인 요청 정보가 맞지 않습니다. "연결하기"를 다시 눌러주세요');
    code = u.searchParams.get('code');
  }
  code = (code || '').replace(/#_$/, '');
  if (!code) throw new Error('code 값을 찾지 못했습니다');
  const j = await api('POST', '/oauth/access_token', {
    client_id: s.THREADS_APP_ID, client_secret: s.THREADS_APP_SECRET,
    grant_type: 'authorization_code', redirect_uri: s.THREADS_REDIRECT_URI, code,
  });
  pendingState = null;
  return finishLogin(j.access_token, j.user_id);
}

// 메타 개발자 화면에서 직접 발급받은 토큰을 붙여넣는 방법
async function useToken(token) {
  if (!token) throw new Error('토큰이 비어 있습니다');
  return finishLogin(token.trim());
}

async function refreshIfNeeded() {
  const t = load();
  if (!t) return;
  const ageDays = (Date.now() - new Date(t.savedAt).getTime()) / 864e5;
  if (ageDays < 30) return;
  try {
    const j = await api('GET', '/refresh_access_token', { grant_type: 'th_refresh_token', access_token: t.token });
    save({ ...t, token: j.access_token, savedAt: new Date().toISOString(), expiresAt: new Date(Date.now() + (j.expires_in || 5184000) * 1000).toISOString() });
  } catch (e) { console.log('[쓰레드] 토큰 갱신 실패:', e.message); }
}

const wait = (ms) => new Promise((r) => setTimeout(r, ms));

/**
 * 게시. media: { type: 'TEXT' | 'VIDEO' | 'IMAGE', url }
 * 영상/이미지는 쓰레드 서버가 가져갈 수 있는 "공개 인터넷 주소"가 필요하다.
 */
async function publish(text, media = { type: 'TEXT' }) {
  await refreshIfNeeded();
  const t = load();
  if (!t) throw new Error('쓰레드 계정이 연결되지 않았습니다 (소셜 탭에서 연결)');
  const params = { media_type: media.type || 'TEXT', text, access_token: t.token };
  if (media.type === 'VIDEO') params.video_url = media.url;
  if (media.type === 'IMAGE') params.image_url = media.url;

  const c = await api('POST', `/v1.0/${t.userId}/threads`, params);
  // 컨테이너 준비될 때까지 대기 (영상은 수 분 걸릴 수 있음)
  const limit = media.type === 'VIDEO' ? 60 : 12;
  for (let i = 0; i < limit; i++) {
    await wait(media.type === 'VIDEO' ? 5000 : 2000);
    const st = await api('GET', `/v1.0/${c.id}`, { fields: 'status,error_message', access_token: t.token });
    if (st.status === 'FINISHED') break;
    if (st.status === 'ERROR' || st.status === 'EXPIRED') throw new Error(`쓰레드가 미디어 처리에 실패: ${st.error_message || st.status}`);
    if (i === limit - 1) throw new Error('쓰레드 미디어 처리 시간 초과');
  }
  const pub = await api('POST', `/v1.0/${t.userId}/threads_publish`, { creation_id: c.id, access_token: t.token });
  let permalink = '';
  try { permalink = (await api('GET', `/v1.0/${pub.id}`, { fields: 'permalink', access_token: t.token })).permalink; } catch {}
  return { mediaId: pub.id, permalink, publishedAt: new Date().toISOString() };
}

async function insights(mediaId) {
  const t = load();
  if (!t) throw new Error('쓰레드 계정이 연결되지 않았습니다');
  const j = await api('GET', `/v1.0/${mediaId}/insights`, { metric: 'views,likes,replies,reposts,quotes', access_token: t.token });
  const out = {};
  for (const d of j.data || []) out[d.name] = d.total_value?.value ?? d.values?.[0]?.value ?? 0;
  out.checkedAt = new Date().toISOString();
  return out;
}

module.exports = { status, authUrl, exchangeCode, useToken, publish, insights, refreshIfNeeded };
