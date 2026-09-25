// 관리 화면
const S = { data: null, tab: 'home', sel: null, task: null, memFile: 'company-memory.md', stdFile: 'threads-post.md', texts: {}, drafts: {}, pending: false };
const $ = (s) => document.querySelector(s);
const esc = (s) => String(s ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const today = () => new Date(Date.now() - new Date().getTimezoneOffset() * 6e4).toISOString().slice(0, 10);

async function api(method, url, body) {
  const r = await fetch(url, { method, headers: { 'content-type': 'application/json' }, body: body ? JSON.stringify(body) : undefined });
  const j = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(j.error || r.status);
  return j;
}
function toast(msg) { const t = $('#toast'); t.textContent = msg; t.classList.remove('hidden'); clearTimeout(t._h); t._h = setTimeout(() => t.classList.add('hidden'), 3500); }
function modal(title, html) { $('#modalTitle').textContent = title; $('#modalBody').innerHTML = html; $('#modal').classList.remove('hidden'); }

const agentMap = () => Object.fromEntries((S.data?.agents || []).map((a) => [a.id, a]));
function who(id) {
  if (id === 'ceo') return { emoji: '👑', name: 'CEO', title: '대표', color: '#4f46e5' };
  if (id === 'system') return { emoji: '⚙️', name: '시스템', title: '', color: '#dc2626' };
  return agentMap()[id] || { emoji: '🙂', name: id, title: '' };
}
function pillFor(t) {
  if (t.running) return `<span class="pill run">⏳ ${esc(t.status)}</span>`;
  if (['rejected', 'publish_wait', 'ceo_wait'].includes(t.stage)) return `<span class="pill wait">✋ ${esc(t.status)}</span>`;
  if (t.stage === 'done') return `<span class="pill ok">✔ ${esc(t.status)}</span>`;
  if (t.stage === 'failed') return `<span class="pill no">⚠ ${esc(t.status)}</span>`;
  return `<span class="pill run">⏳ ${esc(t.status)}</span>`;
}
const fmt = (iso) => iso ? new Date(iso).toLocaleString('ko-KR', { month: 'numeric', day: 'numeric', hour: '2-digit', minute: '2-digit' }) : '';

// ---------- 불러오기 ----------
async function load() {
  S.data = await api('GET', '/api/state');
  $('#companyName').textContent = S.data.company.name;
  const b = $('#modeBadge');
  b.textContent = S.data.mode.demo ? '체험 모드 (API 키 없음)' : `실전 모드 · 클로드${S.data.mode.gpt ? ' + GPT' : ''}`;
  b.className = 'badge ' + (S.data.mode.demo ? 'demo' : 'live');
  const waiting = S.data.tasks.filter((t) => ['rejected', 'publish_wait', 'ceo_wait'].includes(t.stage)).length;
  const pub = S.data.tasks.filter((t) => t.stage === 'publish_wait').length;
  document.querySelector('[data-tab=home]').innerHTML = `👑 CEO 홈${waiting ? `<span class="cnt">${waiting}</span>` : ''}`;
  document.querySelector('[data-tab=publish]').innerHTML = `🚀 발행 큐${pub ? `<span class="cnt">${pub}</span>` : ''}`;
  if (S.sel) S.task = await api('GET', '/api/tasks/' + S.sel).catch(() => null);
  render();
}

function saveDrafts() {
  document.querySelectorAll('#view [data-keep]').forEach((el) => { S.drafts[el.dataset.keep] = el.type === 'checkbox' ? el.checked : el.value; });
}
function restoreDrafts() {
  document.querySelectorAll('#view [data-keep]').forEach((el) => {
    const v = S.drafts[el.dataset.keep];
    if (v === undefined) return;
    if (el.type === 'checkbox') el.checked = v; else el.value = v;
  });
}
function render() {
  const f = document.activeElement;
  if (f && $('#view').contains(f) && /INPUT|TEXTAREA|SELECT/.test(f.tagName) && f.type !== 'checkbox') { S.pending = true; return; }
  saveDrafts();
  const chat = $('.chat');
  const atBottom = chat ? chat.scrollHeight - chat.scrollTop - chat.clientHeight < 80 : true;
  $('#view').innerHTML = VIEWS[S.tab]();
  restoreDrafts();
  const c2 = $('.chat');
  if (c2 && atBottom) c2.scrollTop = c2.scrollHeight;
  document.querySelectorAll('#tabs button').forEach((b) => b.classList.toggle('on', b.dataset.tab === S.tab));
}
document.addEventListener('focusout', () => setTimeout(() => { if (S.pending) { S.pending = false; render(); } }, 150));

// ---------- 화면들 ----------
const VIEWS = {};

VIEWS.home = () => {
  const d = S.data;
  const waiting = d.tasks.filter((t) => ['rejected', 'publish_wait', 'ceo_wait', 'failed'].includes(t.stage));
  const running = d.tasks.filter((t) => !['rejected', 'publish_wait', 'ceo_wait', 'failed', 'done'].includes(t.stage));
  return `
  <div class="card"><div class="flow">
    <span>👑 지시</span><i>→</i><span>🗣 토론</span><i>→</i><span>📌 배정</span><i>→</i><span>🛠 수행</span><i>→</i><span>🧭 검수(완료 기준)</span><i>→</i><span>🔴 반려 시 보강 지시</span><i>→</i><span>♟️ 전략 검토(GPT)</span><i>→</i><span>✅ 승인</span><i>→</i><span>🚀 쓰레드 게시</span>
  </div></div>
  <div class="grid">
    <div class="card">
      <h2>업무 지시</h2>
      <p class="hint">비서실장에게만 말하면 됩니다. 관련 직원 소집·토론·배정·검수는 비서실장이 알아서 진행합니다.</p>
      <label>지시 내용</label>
      <textarea id="inInstr" data-keep="instr" placeholder="예) 콘텐츠 영상 폴더에 있는 AI 뮤직비디오를 쓰레드 계정에 올려줘. 첫 게시물이니까 리포스트와 좋아요 수를 극대화해줘."></textarea>
      <div class="row">
        <div><label>마감일</label><input type="date" id="inDeadline" data-keep="deadline" value="${today()}"></div>
        <div><label>토론 강도</label><select id="inIntensity" data-keep="intensity">
          <option value="light">가볍게 (담당자만, 토큰 절약)</option><option value="normal" selected>보통 (담당자 + 나머지 짧은 반응)</option><option value="deep">깊게 (토론 2바퀴)</option></select></div>
        <div><label>최종 승인자</label><select id="inApprover" data-keep="approver">
          <option value="ceo" ${d.company.policy?.defaultApprover !== 'chief' ? 'selected' : ''}>CEO (중요 업무)</option><option value="chief">비서실장 전결 (반복·저위험)</option></select></div>
      </div>
      <label class="check"><input type="checkbox" id="inPublish" data-keep="publish"> 결과물을 쓰레드에 게시하는 업무입니다</label>
      <div class="row">
        <div><label>첨부 영상 (content/videos 폴더)</label><select id="inVideo" data-keep="video"><option value="">— 없음 (글만 게시) —</option>${d.videos.map((v) => `<option>${esc(v.file)}</option>`).join('')}</select></div>
      </div>
      <p class="hint">영상 목록이 비어 있으면 <code>ai-company/content/videos</code> 폴더에 mp4 파일을 넣고 새로고침하세요.</p>
      <div class="actions"><button class="btn" data-action="create">비서실장에게 지시하기</button></div>
    </div>
    <div>
      <div class="card"><h2>✋ 내 결정이 필요한 일 (${waiting.length})</h2>
        ${waiting.map(decisionCard).join('') || '<div class="empty">지금은 없습니다</div>'}
      </div>
      <div class="card"><h2>⏳ 진행 중 (${running.length})</h2>
        ${running.map((t) => `<div class="task"><div class="t">${esc(t.title)}</div><div class="meta">${pillFor(t)}<span>${fmt(t.updatedAt)}</span></div><div class="actions"><button class="ghost sm" data-action="open-chat" data-id="${t.id}">💬 토론 보기</button></div></div>`).join('') || '<div class="empty">없음</div>'}
      </div>
    </div>
  </div>
  <div class="card"><h2>최근 업무</h2>${taskTable(d.tasks.slice(0, 10))}</div>`;
};

function decisionCard(t) {
  const rv = t.lastReview;
  let body = '';
  if (t.stage === 'rejected') {
    body = `<p><b>🔴 비서실장 반려</b> — ${esc((rv?.reasons || []).join(' / '))}</p>
      <label>보강 지시</label><textarea data-keep="rein-${t.id}" id="rein-${t.id}" placeholder="예) 반려 사유를 해소하고, 결론을 맨 위에 두고 다음 행동에 담당·마감을 넣어서 다시 진행해"></textarea>
      <div class="actions"><button class="btn" data-action="reinforce" data-id="${t.id}">보강 지시 내리기</button><button class="ghost" data-action="open-chat" data-id="${t.id}">💬 토론 보기</button><button class="ghost" data-action="cancel" data-id="${t.id}">취소</button></div>`;
  } else if (t.stage === 'ceo_wait') {
    body = `<p><b>📑 ${esc(t.headline || '최종 보고')}</b></p>
      <div class="actions"><button class="ghost" data-action="report" data-id="${t.id}">보고서 보기</button><button class="btn good" data-action="approve" data-id="${t.id}">승인</button></div>
      <label>마음에 안 들면 보강 지시</label><textarea data-keep="rein-${t.id}" id="rein-${t.id}" placeholder="예) 이 내용을 보기 좋게 정리해서 다시 만들어줘 — 근거 수치를 표로"></textarea>
      <div class="actions"><button class="ghost" data-action="reinforce" data-id="${t.id}">보강 지시 내리기</button></div>`;
  } else if (t.stage === 'publish_wait') {
    body = `<p><b>🚀 게시 승인 요청</b>${t.publish?.status === 'failed' ? ` <span class="pill no">게시 실패: ${esc(t.publish.error)}</span>` : ''}</p>
      <div class="post">${esc(t.publish?.text)}</div>
      <div class="actions"><button class="btn" data-action="goto" data-tab="publish">발행 큐에서 확인</button><button class="ghost" data-action="report" data-id="${t.id}">보고서 보기</button></div>`;
  } else if (t.stage === 'failed') {
    body = `<p class="pill no">⚠ ${esc(t.error)}</p><div class="actions"><button class="btn" data-action="retry" data-id="${t.id}">다시 시도</button><button class="ghost" data-action="cancel" data-id="${t.id}">취소</button></div>`;
  }
  return `<div class="task"><div class="t">${esc(t.title)}</div><div class="meta">${pillFor(t)}<span>마감 ${esc(t.deadline)}</span><span>검수 ${t.round}차</span></div>${body}</div>`;
}

function taskTable(tasks) {
  if (!tasks.length) return '<div class="empty">아직 업무가 없습니다. 위에서 첫 지시를 내려보세요.</div>';
  return `<table><thead><tr><th>업무</th><th>상태</th><th>마감</th><th>AI 호출</th><th></th></tr></thead><tbody>${tasks.map((t) => `
    <tr><td><b>${esc(t.title)}</b><div class="sub">${esc(t.instruction.slice(0, 60))}</div></td><td>${pillFor(t)}</td><td>${esc(t.deadline)}</td>
    <td class="sub">${t.usage?.calls || 0}회${t.usage?.in ? `<br>${Math.round((t.usage.in + t.usage.out) / 1000)}k 토큰` : ''}</td>
    <td><button class="ghost sm" data-action="open-chat" data-id="${t.id}">💬</button> ${t.hasReport ? `<button class="ghost sm" data-action="report" data-id="${t.id}">📑</button>` : ''}</td></tr>`).join('')}</tbody></table>`;
}

VIEWS.messenger = () => {
  const d = S.data;
  if (!S.sel && d.tasks[0]) { S.sel = d.tasks[0].id; setTimeout(load, 0); }
  const t = S.task;
  const chans = d.tasks.map((x) => `<div class="chan ${x.id === S.sel ? 'on' : ''}" data-action="select" data-id="${x.id}"><div class="t"># ${esc(x.title)}</div><div class="meta sub">${pillFor(x)}</div></div>`).join('') || '<div class="empty">채널 없음</div>';
  const KIND = { debate: '토론', reaction: '반응', work: '작업', review: '검수', strategy: '전략 검토', publish: '발행', chief: '', ceo: '', system: '' };
  let chat = '<div class="empty">왼쪽에서 채널을 고르세요</div>';
  if (t) {
    chat = `<div class="card"><h2># ${esc(t.title)} <span class="sub">비서실장 채널</span></h2>
      <div class="chat">${t.messages.map((m) => { const w = who(m.from); return `
        <div class="msg ${m.from === 'ceo' ? 'ceo' : ''} ${m.kind}">
          <div class="av" style="border-color:${w.color || 'var(--line)'}">${w.emoji}</div>
          <div class="bubble"><div class="who">${esc(w.name)} <small>${esc(w.title)}${KIND[m.kind] ? ' · ' + KIND[m.kind] : ''} · ${fmt(m.ts)}</small></div>${esc(m.text)}</div>
        </div>`; }).join('')}
        ${t.running ? `<div class="typing">⏳ ${esc(t.status)} 중… (직원들이 이야기하는 중)</div>` : ''}
      </div></div>`;
  }
  return `<div class="msgr"><div class="card">${chans}</div><div>${chat}</div></div>`;
};

VIEWS.queue = () => {
  const d = S.data;
  return `<div class="card"><h2>작업 큐</h2><p class="hint">모든 작업 문서 맨 위에는 "이 문서를 보면 무엇을 알 수 있는지" 한 줄 요약이 있습니다. AI도 이 한 줄만 먼저 읽고 필요한 문서인지 판단합니다(토큰 절약).</p>
  ${d.tasks.map((t) => `<div class="task">
    <div class="t">${esc(t.title)} <span class="sub">${esc(t.id)}</span></div>
    <div class="meta">${pillFor(t)}<span>유형 ${esc(t.taskType || '-')}</span><span>마감 ${esc(t.deadline)}</span><span>검수 ${t.round}차</span><span>승인자 ${t.approver === 'ceo' ? 'CEO' : '비서실장'}</span></div>
    ${t.assignments.length ? `<table><thead><tr><th>차수</th><th>담당</th><th>결과물</th><th>한줄요약</th></tr></thead><tbody>${t.assignments.map((a) => { const w = who(a.agent); return `
      <tr><td>${a.round}차</td><td>${w.emoji} ${esc(w.name)}</td><td>${esc(a.deliverable)} ${a.status === 'done' ? '✔' : '⏳'}</td>
      <td>${a.file ? `<span class="doclink" data-action="doc" data-id="${t.id}" data-file="${esc(a.file)}">${esc(a.summary)}</span>` : '<span class="sub">작업 중</span>'}</td></tr>`; }).join('')}</tbody></table>` : ''}
    ${t.lastReview ? `<p class="sub">최근 검수: ${t.lastReview.verdict === 'approve' ? '🟢 통과' : '🔴 반려'} — ${esc((t.lastReview.reasons || []).join(' / '))}</p>` : ''}
    <div class="actions">
      <button class="ghost sm" data-action="open-chat" data-id="${t.id}">💬 토론</button>
      ${t.hasReport ? `<button class="ghost sm" data-action="report" data-id="${t.id}">📑 보고서</button>` : ''}
      ${t.stage === 'failed' ? `<button class="btn sm" data-action="retry" data-id="${t.id}">다시 시도</button>` : ''}
      ${!t.running && !['done'].includes(t.stage) ? `<button class="ghost sm" data-action="cancel" data-id="${t.id}">취소</button>` : ''}
    </div></div>`).join('') || '<div class="empty">없음</div>'}</div>`;
};

VIEWS.strategy = () => {
  const list = S.data.tasks.filter((t) => t.strategy);
  return `<div class="card"><h2>♟️ 전략실장 한수합 검토</h2><p class="hint">한수합은 다른 모델(GPT)로 돌아갑니다. 같은 모델끼리 함께 놓치는 부분을 찾는 역할이며, <b>승인권은 없고 의견만</b> 냅니다. 반영 여부는 비서실장이 판단합니다.</p>
  ${list.map((t) => { const s = t.strategy; const v = { go: '<span class="pill ok">실행 권고</span>', caution: '<span class="pill wait">주의 후 실행</span>', rethink: '<span class="pill no">재검토 권고</span>' }[s.verdict] || ''; return `
    <div class="task"><div class="t">${esc(t.title)} ${v}</div><div class="meta"><span>모델: ${esc(s.model)}</span><span>${fmt(s.ts)}</span></div>
    <p>${esc(s.summary)}</p>
    <table><thead><tr><th>심각도</th><th>문제 제기</th><th>이유</th></tr></thead><tbody>${(s.concerns || []).map((c) => `<tr><td><span class="pill ${c.severity === 'high' ? 'no' : c.severity === 'mid' ? 'wait' : ''}">${esc(c.severity)}</span></td><td>${esc(c.issue)}</td><td>${esc(c.why)}</td></tr>`).join('')}</tbody></table>
    <h3>권고안</h3><ul>${(s.recommendations || []).map((r) => `<li>${esc(r)}</li>`).join('')}</ul>
    ${t.hasReport ? `<button class="ghost sm" data-action="report" data-id="${t.id}">비서실장 반영 결과 (보고서)</button>` : ''}</div>`; }).join('') || '<div class="empty">아직 전략 검토가 없습니다</div>'}</div>`;
};

VIEWS.publish = () => {
  const list = S.data.tasks.filter((t) => t.publish?.enabled && t.publish.text);
  const conn = S.data.threads.connected;
  return `<div class="card"><h2>🚀 발행 큐</h2>
  <p class="hint">SNS에 실제로 나가기 직전 단계입니다. 쓰레드 연결: ${conn ? `<span class="pill ok">@${esc(S.data.threads.username)}</span>` : `<span class="pill no">미연결</span> — 소셜·설정 탭에서 연결하세요${S.data.mode.demo ? ' (체험 모드에서는 모의 게시로 처리)' : ''}`}</p>
  ${list.map((t) => { const p = t.publish; const st = { pending: '<span class="pill wait">승인 대기</span>', failed: '<span class="pill no">게시 실패</span>', published: '<span class="pill ok">게시됨</span>', manual: '<span class="pill ok">수동 게시됨</span>', simulated: '<span class="pill">모의 게시</span>', rejected: '<span class="pill">취소</span>' }[p.status] || ''; return `
    <div class="task"><div class="t">${esc(t.title)} ${st}</div>
    <div class="meta"><span>승인자 ${t.approver === 'ceo' ? 'CEO' : '비서실장 전결'}</span>${p.videoFile ? `<span>🎬 ${esc(p.videoFile)}</span>` : '<span>📝 글만</span>'}</div>
    ${p.error ? `<p class="pill no">${esc(p.error)}</p>` : ''}
    ${t.stage === 'publish_wait' ? `
      <label>게시 문구 (수정 가능, 500자 이내) — <span class="sub" id="len-${t.id}">${p.text.length}자</span></label>
      <textarea id="pub-${t.id}" data-keep="pub-${t.id}" data-len="len-${t.id}" style="min-height:160px">${esc(p.text)}</textarea>
      ${p.videoFile ? `<p class="hint">🎬 영상 게시: 쓰레드 API는 영상 파일을 직접 받지 않고 "공개 인터넷 주소"가 있어야 합니다. PUBLIC_URL이 없으면 아래 <b>수동 게시</b>를 쓰세요.<br><a href="/preview/${encodeURIComponent(p.videoFile)}" target="_blank">영상 미리보기</a></p>` : ''}
      <div class="actions">
        <button class="btn good" data-action="approve-publish" data-id="${t.id}">✅ 승인하고 게시</button>
        <button class="ghost" data-action="copy" data-id="${t.id}">📋 문구 복사</button>
        <button class="ghost" data-action="report" data-id="${t.id}">📑 보고서</button>
        <button class="ghost" data-action="cancel" data-id="${t.id}">게시 취소</button>
      </div>
      <details><summary class="sub">수동 게시 (영상이거나 API가 막힐 때)</summary>
        <ol class="steps"><li>📋 문구 복사를 누릅니다</li><li><a href="https://www.threads.net" target="_blank">threads.net</a> 또는 휴대폰 쓰레드 앱에서 새 글 → 문구 붙여넣기${p.videoFile ? ` → 영상(<code>content/videos/${esc(p.videoFile)}</code>) 첨부` : ''} → 게시</li><li>게시된 글 주소(선택)를 아래에 붙여넣고 완료를 누릅니다</li></ol>
        <div class="row"><input type="text" id="perma-${t.id}" data-keep="perma-${t.id}" placeholder="https://www.threads.net/@.../post/..."><button class="ghost" style="flex:0" data-action="manual-done" data-id="${t.id}">수동 게시 완료</button></div>
      </details>`
    : `<div class="post">${esc(p.text)}</div>
      ${p.result ? `<p class="sub">게시 ${fmt(p.result.publishedAt)} ${p.result.permalink ? `· <a href="${esc(p.result.permalink)}" target="_blank">게시물 보기</a>` : ''}</p>` : ''}
      ${p.insights ? `<p>👀 조회 ${p.insights.views ?? '-'} · ❤️ 좋아요 ${p.insights.likes ?? '-'} · 🔁 리포스트 ${p.insights.reposts ?? '-'} · 💬 답글 ${p.insights.replies ?? '-'} · 인용 ${p.insights.quotes ?? '-'} <span class="sub">(${fmt(p.insights.checkedAt)} 기준)</span></p>` : ''}
      ${p.status === 'published' ? `<button class="ghost sm" data-action="insights" data-id="${t.id}">📊 성과 새로고침</button>` : ''}`}
    </div>`; }).join('') || '<div class="empty">발행 대기 중인 게시물이 없습니다</div>'}</div>`;
};

function fileEditor(kind, files, cur) {
  const c = (S.texts[kind] || []).find((f) => f.name === cur);
  return `<div class="filetabs">${files.map((f) => `<button class="${f === cur ? 'btn sm' : 'ghost sm'}" data-action="file" data-kind="${kind}" data-name="${f}">${f}</button>`).join('')}</div>
    <textarea class="code" id="ed-${kind}" data-keep="ed-${kind}-${cur}">${esc(c?.content ?? '불러오는 중…')}</textarea>
    <div class="actions"><button class="btn" data-action="save-file" data-kind="${kind}" data-name="${cur}">저장</button></div>`;
}

VIEWS.memory = () => {
  if (!S.texts.memory) loadTexts('memory');
  if (!S.docs) api('GET', '/api/docs').then((d) => { S.docs = d; render(); });
  return `<div class="grid">
    <div class="card"><h2>🧠 회사 기억</h2><p class="hint"><b>company-memory.md</b>: 중요한 의사결정·변하지 않는 원칙. <b>lessons.md</b>: 반려(실패)·통과(성공) 교훈이 자동으로 쌓입니다. 비서실장이 새 업무를 시작할 때 먼저 읽습니다.</p>
      ${fileEditor('memory', ['company-memory.md', 'lessons.md'], S.memFile)}</div>
    <div class="card"><h2>📄 작업 문서 색인 (한줄요약)</h2><p class="hint">AI는 문서 전체가 아니라 이 한 줄만 보고 필요한 문서를 고릅니다.</p>
      <table><tbody>${(S.docs || []).map((d) => `<tr><td class="sub">${esc(d.task)}<br>${esc(d.file)}</td><td><span class="doclink" data-action="doc" data-id="${esc(d.task)}" data-file="${esc(d.file)}">${esc(d.summary)}</span></td></tr>`).join('') || '<tr><td class="empty">아직 없음</td></tr>'}</tbody></table></div>
  </div>`;
};

VIEWS.standards = () => {
  if (!S.texts.standards) loadTexts('standards');
  return `<div class="card"><h2>✅ 완료 기준 — "우리 회사에서 이 정도면 완료"</h2>
    <p class="hint">이 시스템의 핵심입니다. 직원 구조를 아무리 잘 만들어도 <b>결과물의 기준</b>을 안 주면 형편없는 보고서가 나옵니다.<br>
    · 직원들은 작업 전에 이 기준을 읽고 작업합니다. · 비서실장은 <code>- [ ]</code> 줄을 체크리스트로 삼아 검수합니다. · 최종 보고서는 고정 양식(<code>standards/templates/ceo-report.html</code>)에 채워집니다.<br>
    마음에 드는 보고서가 있으면 그 특징을 여기에 문장으로 적어두세요. 그게 레퍼런스가 됩니다.</p>
    ${fileEditor('standards', ['threads-post.md', 'analysis.md', 'general.md', 'ceo-report.md', 'README.md'], S.stdFile)}</div>`;
};

VIEWS.social = () => {
  const d = S.data, s = d.secrets, th = d.threads;
  const field = (k, label, ph, secret) => `<label>${label} ${s[k].set ? `<span class="pill ok">설정됨 ${esc(s[k].preview)}</span>` : '<span class="pill">미설정</span>'}</label><input type="${secret ? 'password' : 'text'}" id="set-${k}" data-keep="set-${k}" placeholder="${esc(ph)}" autocomplete="off">`;
  return `<div class="grid">
  <div class="card"><h2>🔑 AI 연결 (API 키)</h2>
    <p class="hint">키가 없으면 <b>체험 모드</b>로 돌아갑니다(가짜 응답으로 전체 흐름만 보여줌). 키는 이 컴퓨터의 <code>data/secrets.json</code>에만 저장되고 화면에는 끝 4자리만 보입니다.</p>
    ${field('ANTHROPIC_API_KEY', '클로드 API 키 (비서실장·직원 9명)', 'sk-ant-...', true)}
    ${field('OPENAI_API_KEY', 'OpenAI API 키 (전략실장 한수합, 선택)', 'sk-... (없으면 클로드가 대신)', true)}
    <div class="actions"><button class="btn" data-action="save-settings" data-keys="ANTHROPIC_API_KEY,OPENAI_API_KEY">저장</button></div>
    <h3>사용 모델 (config/company.json 에서 변경)</h3>
    <table><tbody><tr><td>비서실장 (검수 담당 → 강한 모델)</td><td><code>${esc(d.company.models.chief)}</code></td></tr><tr><td>직원 8명 (실무 → 비용 절약 모델)</td><td><code>${esc(d.company.models.staff)}</code></td></tr><tr><td>전략실장 (다른 회사 모델)</td><td><code>${esc(d.company.models.strategist)}</code></td></tr></tbody></table>
  </div>
  <div class="card"><h2>🧵 쓰레드 연결</h2>
    <p>상태: ${th.connected ? `<span class="pill ok">연결됨 @${esc(th.username)}</span> <span class="sub">토큰 만료 ${fmt(th.expiresAt)} (자동 갱신)</span>` : '<span class="pill no">미연결</span>'}</p>
    ${field('THREADS_APP_ID', '① 쓰레드 앱 ID', '메타 개발자 > 앱 > 이용 사례 > 설정의 Threads 앱 ID')}
    ${field('THREADS_APP_SECRET', '② 쓰레드 앱 시크릿 코드 (절대 외부 공유 금지)', '시크릿 보기 → 비밀번호 입력 → 복사', true)}
    ${field('THREADS_REDIRECT_URI', '③ 콜백(리디렉션) 주소 — 메타 설정에도 똑같이 등록', 'https://localhost/threads-callback')}
    <div class="actions"><button class="btn" data-action="save-settings" data-keys="THREADS_APP_ID,THREADS_APP_SECRET,THREADS_REDIRECT_URI">저장</button></div>
    <h3>④ 연결하기</h3>
    <ol class="steps">
      <li><button class="btn sm" data-action="threads-auth">연결하기 (쓰레드 로그인 창 열기)</button></li>
      <li>쓰레드에서 <b>계속/허용</b>을 누릅니다</li>
      <li>"사이트에 연결할 수 없음" 화면이 떠도 정상입니다. <b>주소창의 주소 전체</b>를 복사해 아래에 붙여넣으세요</li>
    </ol>
    <div class="row"><input type="text" id="thCode" data-keep="thCode" placeholder="https://localhost/threads-callback?code=...&state=..."><button class="btn" style="flex:0" data-action="threads-code">연결 완료</button></div>
    <details><summary class="sub">다른 방법: 액세스 토큰 직접 붙여넣기</summary>
      <p class="hint">메타 개발자 화면의 토큰 생성기에서 받은 토큰이 있으면 여기에 붙여넣어도 됩니다.</p>
      <div class="row"><input type="password" id="thToken" placeholder="THAA..."><button class="ghost" style="flex:0" data-action="threads-token">저장</button></div></details>
    <h3>⑤ 연결 시험</h3>
    <div class="row"><input type="text" id="thTest" data-keep="thTest" placeholder="연결 시험 중입니다."><button class="ghost" style="flex:0" data-action="threads-test" ${th.connected ? '' : 'disabled'}>시험 게시</button></div>
  </div>
  <div class="card"><h2>🎬 영상 자동 게시 (고급, 선택)</h2>
    <p class="hint">쓰레드 API는 영상 <b>파일</b>을 받지 않고, 쓰레드 서버가 가져갈 수 있는 <b>공개 인터넷 주소</b>만 받습니다. 방법은 두 가지입니다.</p>
    <ol class="steps"><li><b>수동 게시 (추천)</b>: 발행 큐에서 문구 복사 → 앱에서 영상 첨부해 직접 게시 → "수동 게시 완료"</li>
    <li><b>터널로 공개 주소 만들기</b>: cloudflared 같은 터널 프로그램으로 이 컴퓨터에 임시 공개 주소를 만들고 아래에 입력. 외부에서는 <code>content/videos</code> 영상 파일만 접근 가능하고 관리 화면은 차단됩니다.</li></ol>
    ${field('PUBLIC_URL', '공개 주소 (PUBLIC_URL)', 'https://xxxx.trycloudflare.com')}
    <div class="actions"><button class="btn" data-action="save-settings" data-keys="PUBLIC_URL">저장</button></div>
  </div>
  <div class="card"><h2>👥 조직도</h2><table><tbody>${d.agents.map((a) => `<tr><td style="white-space:nowrap">${a.emoji} <b>${esc(a.name)}</b><br><span class="sub">${esc(a.title)}</span></td><td class="sub">${esc(a.role)}</td></tr>`).join('')}</tbody></table>
  <p class="hint">직원 이름·역할·성격은 <code>config/agents.json</code>, 회사 정보·브랜드는 <code>config/company.json</code>에서 바꿉니다.</p></div>
  </div>`;
};

async function loadTexts(kind) {
  S.texts[kind] = await api('GET', '/api/text/' + kind);
  render();
}

// ---------- 버튼 동작 ----------
const ACT = {
  async create() {
    const body = { instruction: $('#inInstr').value, deadline: $('#inDeadline').value, intensity: $('#inIntensity').value, approver: $('#inApprover').value, publish: $('#inPublish').checked, videoFile: $('#inVideo').value };
    if (body.videoFile) body.publish = true;
    const t = await api('POST', '/api/tasks', body);
    S.drafts.instr = ''; S.drafts.publish = false; S.drafts.video = '';
    toast('지시 완료 — 비서실장이 토론을 소집합니다');
    S.sel = t.id; S.tab = 'messenger'; await load();
  },
  async reinforce(el) {
    const v = $('#rein-' + el.dataset.id).value;
    await api('POST', `/api/tasks/${el.dataset.id}/reinforce`, { text: v });
    delete S.drafts['rein-' + el.dataset.id];
    toast('보강 지시 전달'); S.sel = el.dataset.id; S.tab = 'messenger'; await load();
  },
  async approve(el) { await api('POST', `/api/tasks/${el.dataset.id}/approve`, {}); toast('승인 완료'); await load(); },
  async 'approve-publish'(el) {
    if (!confirm('이 문구로 쓰레드에 게시할까요?')) return;
    await api('POST', `/api/tasks/${el.dataset.id}/approve`, { text: $('#pub-' + el.dataset.id).value });
    toast('게시 진행 중…'); await load();
  },
  async 'manual-done'(el) { await api('POST', `/api/tasks/${el.dataset.id}/manual-published`, { permalink: $('#perma-' + el.dataset.id).value }); toast('수동 게시 기록 완료'); await load(); },
  async copy(el) { const v = $('#pub-' + el.dataset.id).value; await navigator.clipboard.writeText(v).then(() => toast('문구를 복사했습니다'), () => toast('복사 실패 — 직접 선택해서 복사하세요')); },
  async cancel(el) { if (!confirm('이 업무를 취소할까요?')) return; await api('POST', `/api/tasks/${el.dataset.id}/cancel`); await load(); },
  async retry(el) { await api('POST', `/api/tasks/${el.dataset.id}/retry`); toast('멈춘 단계부터 다시 진행합니다'); await load(); },
  async insights(el) { const r = await api('POST', `/api/tasks/${el.dataset.id}/insights`); toast(`조회 ${r.views ?? '-'} · 좋아요 ${r.likes ?? '-'} · 리포스트 ${r.reposts ?? '-'}`); await load(); },
  async 'open-chat'(el) { S.sel = el.dataset.id; S.tab = 'messenger'; await load(); },
  async select(el) { S.sel = el.dataset.id; await load(); },
  async goto(el) { S.tab = el.dataset.tab; render(); },
  async report(el) { modal('최종 보고서', `<iframe src="/api/doc/${el.dataset.id}/final-report.html"></iframe><div class="actions"><a class="ghost" href="/api/doc/${el.dataset.id}/final-report.html" target="_blank">새 창으로 열기</a></div>`); },
  async doc(el) { const r = await fetch(`/api/doc/${el.dataset.id}/${el.dataset.file}`); modal(el.dataset.file, `<pre>${esc(await r.text())}</pre>`); },
  async file(el) { if (el.dataset.kind === 'memory') S.memFile = el.dataset.name; else S.stdFile = el.dataset.name; render(); },
  async 'save-file'(el) {
    await api('POST', `/api/text/${el.dataset.kind}/${el.dataset.name}`, { content: $('#ed-' + el.dataset.kind).value });
    delete S.drafts[`ed-${el.dataset.kind}-${el.dataset.name}`];
    toast('저장했습니다'); S.texts[el.dataset.kind] = null; S.docs = null; await loadTexts(el.dataset.kind);
  },
  async 'save-settings'(el) {
    const body = {};
    for (const k of el.dataset.keys.split(',')) { const v = $('#set-' + k).value; if (v) body[k] = v; delete S.drafts['set-' + k]; }
    if (!Object.keys(body).length) return toast('입력한 값이 없습니다');
    await api('POST', '/api/settings', body); toast('저장했습니다'); await load();
  },
  async 'threads-auth'() { const r = await api('GET', '/api/threads/auth-url'); window.open(r.url, '_blank'); toast('새 창에서 쓰레드 로그인 후 주소창 주소를 복사해 오세요'); },
  async 'threads-code'() { const r = await api('POST', '/api/threads/code', { code: $('#thCode').value }); S.drafts.thCode = ''; toast(`연결 완료: @${r.username}`); await load(); },
  async 'threads-token'() { const r = await api('POST', '/api/threads/token', { token: $('#thToken').value }); toast(`연결 완료: @${r.username}`); await load(); },
  async 'threads-test'() { if (!confirm('실제로 쓰레드에 시험 글이 올라갑니다. 진행할까요?')) return; const r = await api('POST', '/api/threads/test', { text: $('#thTest').value }); toast('게시 성공!'); if (r.permalink) window.open(r.permalink, '_blank'); },
  async 'close-modal'() { $('#modal').classList.add('hidden'); },
};

document.addEventListener('click', async (e) => {
  const tab = e.target.closest('#tabs button');
  if (tab) { S.tab = tab.dataset.tab; render(); return; }
  if (e.target.id === 'modal') { $('#modal').classList.add('hidden'); return; }
  const el = e.target.closest('[data-action]');
  if (!el || !ACT[el.dataset.action]) return;
  if (el.tagName === 'BUTTON') el.disabled = true;
  try { await ACT[el.dataset.action](el); } catch (err) { toast('⚠ ' + err.message); } finally { if (el.tagName === 'BUTTON') el.disabled = false; }
});
document.addEventListener('input', (e) => {
  if (e.target.dataset.len) { const l = document.getElementById(e.target.dataset.len); if (l) l.textContent = e.target.value.length + '자'; }
});

// ---------- 실시간 ----------
let timer = null;
function connect() {
  const es = new EventSource('/api/events');
  es.onopen = () => $('#liveDot').classList.add('on');
  es.onerror = () => $('#liveDot').classList.remove('on');
  es.onmessage = () => { clearTimeout(timer); timer = setTimeout(() => load().catch(() => {}), 250); };
}
load().then(connect).catch((e) => { $('#view').innerHTML = `<div class="card">서버에 연결할 수 없습니다: ${esc(e.message)}</div>`; });
