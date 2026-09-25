// CEO 보고서: AI가 마음대로 꾸미지 않고, 고정 양식(standards/templates/ceo-report.html)에 내용만 채운다
const fs = require('fs');
const path = require('path');
const { P, agent } = require('./env');

const esc = (s) => String(s ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const nameOf = (id) => { const a = agent(id); return a ? `${a.emoji} ${a.name}` : id; };

function renderHTML(t) {
  const tpl = fs.readFileSync(path.join(P.standards, 'templates', 'ceo-report.html'), 'utf8');
  const r = t.final?.report || {};
  const lastReview = (t.reviews || []).slice(-1)[0] || { checklist: [] };
  const map = {
    TITLE: esc(t.title),
    STATUS: t.publish?.enabled ? '게시 승인 요청' : '최종 보고',
    TASK_ID: esc(t.id),
    DEADLINE: esc(t.deadline),
    DATE: new Date().toLocaleString('ko-KR'),
    ROUNDS: String((t.reviews || []).length),
    HEADLINE: esc(r.headline),
    DECISION: esc(r.decisionNeeded || '없음'),
    SUMMARY: (r.summary || []).slice(0, 3).map((s) => `<li>${esc(s)}</li>`).join(''),
    POST: t.final?.post?.text ? `<div class="card"><h2>게시 문구 (${t.final.post.text.length}자)</h2><div class="post">${esc(t.final.post.text)}</div></div>` : '',
    FINDINGS: (r.findings || []).map((f) => `<div class="finding"><b>${esc(f.title)}</b>${esc(f.detail)}<div class="ev">근거: ${esc(f.evidence)}</div></div>`).join('') || '<div>없음</div>',
    RISKS: (r.risks || []).map((x) => `<tr><td>${esc(x.risk)}</td><td>${esc(x.mitigation)}</td></tr>`).join('') || '<tr><td colspan="2">없음</td></tr>',
    ACTIONS: (r.nextActions || []).map((x) => `<tr><td>${esc(x.owner)}</td><td>${esc(x.action)}</td><td>${esc(x.due)}</td></tr>`).join('') || '<tr><td colspan="3">없음</td></tr>',
    STRATEGY: (t.final?.strategyDecisions || []).map((x) => `<tr><td>${esc(x.recommendation)}</td><td class="${x.accept ? 'ok' : 'no'}">${x.accept ? '반영' : '보류'}</td><td>${esc(x.reason)}</td></tr>`).join('') || '<tr><td colspan="3">전략 검토 없음</td></tr>',
    CHECKLIST: (lastReview.checklist || []).map((c) => `<tr><td>${esc(c.item)}</td><td class="${c.pass ? 'ok' : 'no'}">${c.pass ? '통과' : '미통과'}</td><td>${esc(c.note)}</td></tr>`).join(''),
    DOCS: (t.assignments || []).filter((a) => a.file).map((a) => `<tr><td>${esc(nameOf(a.agent))}</td><td>${esc(a.summary)}</td></tr>`).join(''),
    INSTRUCTION: esc(t.instruction),
  };
  return tpl.replace(/\{\{(\w+)\}\}/g, (_, k) => map[k] ?? '');
}

function renderMarkdown(t) {
  const r = t.final?.report || {};
  const lines = [
    `> 한줄요약: ${r.headline || t.title}`,
    '',
    `# ${t.title} — 최종 보고`,
    '',
    `**CEO가 결정할 것:** ${r.decisionNeeded || '없음'}`,
    '',
    '## 핵심 요약',
    ...(r.summary || []).map((s, i) => `${i + 1}. ${s}`),
    '',
    '## 근거',
    ...(r.findings || []).map((f) => `- **${f.title}**: ${f.detail} (근거: ${f.evidence})`),
    '',
    '## 리스크와 대응',
    '| 리스크 | 대응 |', '|---|---|',
    ...(r.risks || []).map((x) => `| ${x.risk} | ${x.mitigation} |`),
    '',
    '## 다음 행동',
    '| 담당 | 할 일 | 마감 |', '|---|---|---|',
    ...(r.nextActions || []).map((x) => `| ${x.owner} | ${x.action} | ${x.due} |`),
  ];
  if (t.final?.post?.text) lines.push('', '## 게시 문구', '```', t.final.post.text, '```');
  return lines.join('\n');
}

module.exports = { renderHTML, renderMarkdown };
