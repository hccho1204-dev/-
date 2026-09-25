// 업무 흐름 엔진
// 지시 → 토론 소집 → 1차 토론(관련자 깊게, 비관련자 짧게) → 업무 배정 → 수행(문서 저장, 첫 줄 한줄요약)
// → 비서실장 검수(완료 기준) → [반려 → CEO 보강 지시 → 보강 토론 → 재수행 → 재검수]
// → 전략실장(GPT) 독립 검토 → 비서실장 최종 판단 → CEO 승인 / 발행 큐 → 쓰레드 게시
const fs = require('fs');
const path = require('path');
const { P, company, agents, agent, secrets } = require('./env');
const store = require('./store');
const { ask, mode } = require('./llm');
const mock = require('./mock');
const report = require('./report');
const threads = require('./threads');

const STAGES = {
  triage: '토론 소집', debate: '1차 토론', assign: '업무 배정', execute: '업무 수행', review: '비서실장 검수',
  rejected: '반려 · 보강 지시 대기', rework: '보강 토론', strategy: '전략실장 검토', final: '비서실장 최종 판단',
  publish_wait: '발행 승인 대기', publishing: '쓰레드 게시 중', ceo_wait: 'CEO 최종 승인 대기', done: '완료', failed: '오류',
};
const WAIT = new Set(['rejected', 'publish_wait', 'ceo_wait', 'done', 'failed']);
const STANDARD_FOR = { threads_post: 'threads-post.md', analysis: 'analysis.md', general: 'general.md' };
const running = new Set();

// ---------- 공통 도우미 ----------
const staff = () => agents().filter((a) => a.tier === 'staff');
const nm = (id) => { const a = agent(id); return a ? `${a.name}(${a.title})` : id; };
const cut = (s, n) => (String(s || '').length > n ? String(s).slice(0, n) + '\n…(이하 생략)' : String(s || ''));

function say(t, from, text, kind = 'chat') {
  t.messages.push({ id: t.messages.length + 1, from, kind, text: String(text || '').trim(), round: t.round, ts: new Date().toISOString() });
  store.saveTask(t);
}

function readStandard(t) {
  const f = STANDARD_FOR[t.taskType] || 'general.md';
  const main = fs.readFileSync(path.join(P.standards, f), 'utf8');
  const ceo = fs.readFileSync(path.join(P.standards, 'ceo-report.md'), 'utf8');
  return { file: f, text: `${main}\n\n${ceo}` };
}
function checklistItems(standardText) {
  return standardText.split(/\r?\n/).filter((l) => /^\s*-\s*\[ \]/.test(l)).map((l) => l.replace(/^\s*-\s*\[ \]\s*/, '').trim());
}

function companyBlock() {
  const c = company();
  return `[회사] ${c.name}
- 미션: ${c.mission}
- 브랜드 정체성: ${c.brand?.identity}
- 문체: ${c.brand?.tone}
- 타깃: ${c.brand?.audience}
- 금지: ${(c.brand?.forbidden || []).join(' / ')}`;
}
function systemFor(agentId) {
  const a = agent(agentId);
  return `너는 ${company().name}의 ${a.title} "${a.name}"이다. 실제 회사의 직원처럼 행동한다.
[너의 역할] ${a.role}
[너의 성격] ${a.persona}

${companyBlock()}

[공통 규칙]
- 한국어로 쓴다. 결론부터 짧게.
- CEO 지시라도 회사에 손해라고 판단되면 근거를 들어 분명히 말한다. 예스맨 금지.
- 모르는 것은 모른다고, 추측은 "추정"이라고 표시한다. 수치를 지어내지 않는다.
- 자기 전문 영역 관점에서만 말한다.`;
}
function memoryDigest(forAnalysis = false) {
  const mem = cut(store.readMemory('company-memory.md'), 2500);
  const lessons = store.readMemory('lessons.md').split(/\r?\n/).filter((l) => l.startsWith('- ')).slice(-15).join('\n');
  const docs = store.docIndex(25).map((d) => `- ${d.task}/${d.file}: ${d.summary}`).join('\n');
  let posts = '';
  if (forAnalysis) {
    posts = store.listTasks().filter((x) => x.publish?.result).slice(0, 10).map((x) =>
      `- ${x.publish.result.publishedAt?.slice(0, 16)} "${cut(x.publish.text, 60).replace(/\n/g, ' ')}" 성과: ${x.publish.insights ? JSON.stringify(x.publish.insights) : '아직 측정 안 함'} ${x.publish.result.permalink || ''}`).join('\n');
  }
  return `[회사 기억]\n${mem}\n\n[성공·실패 기록(최근)]\n${lessons || '(없음)'}\n\n[과거 작업 문서 목록 — 한줄요약만]\n${docs || '(없음)'}${forAnalysis ? `\n\n[지난 쓰레드 게시물 실제 데이터]\n${posts || '(게시 기록 없음 — 없다고 솔직히 보고할 것)'}` : ''}`;
}
function ceoBlock(t) {
  const rein = (t.reinforcements || []).map((r) => `- (${r.round}차) ${r.text}`).join('\n');
  return `[CEO 지시] ${t.instruction}
[마감] ${t.deadline}  [토론 강도] ${t.intensity}  [최종 승인자] ${t.approver === 'ceo' ? 'CEO' : '비서실장 전결'}
[쓰레드 게시] ${t.publish?.enabled ? `예${t.publish.videoFile ? ` (영상 파일: ${t.publish.videoFile})` : ' (텍스트)'}` : '아니오'}${rein ? `\n[CEO 보강 지시]\n${rein}` : ''}`;
}
function transcript(t, max = 7000) {
  const lines = t.messages.filter((m) => ['debate', 'reaction', 'ceo', 'chief'].includes(m.kind))
    .map((m) => `${m.from === 'ceo' ? 'CEO' : nm(m.from)}: ${m.text}`);
  let s = lines.join('\n\n');
  return s.length > max ? '…' + s.slice(-max) : s;
}
function roster() {
  return staff().map((a) => `- ${a.id}: ${a.name} / ${a.title} — ${a.role}`).join('\n');
}

// ---------- 단계 ----------
const stage = {};

stage.triage = async (t) => {
  say(t, 'chief', `CEO 지시를 접수했습니다. 관련 담당자를 불러 토론을 소집합니다.`, 'chief');
  const r = await ask({
    task: t, agentId: 'chief', json: true, maxTokens: 800,
    system: systemFor('chief'),
    prompt: `${ceoBlock(t)}

${memoryDigest()}

[직원 명단]
${roster()}

이 지시를 처리하기 위한 토론을 소집하라. 아래 JSON만 출력:
{"taskType":"threads_post|analysis|general 중 하나 (쓰레드 게시가 '예'면 threads_post)",
 "title":"업무 제목 20자 이내",
 "relevant":["먼저 깊게 발언할 관련 직원 id 2~4명, 발언 순서대로"],
 "agenda":"토론 안건 한 문장",
 "keyQuestions":["토론에서 반드시 답해야 할 질문 2~3개"]}`,
    mock: () => mock.triage(t),
  });
  const valid = new Set(staff().map((a) => a.id));
  t.taskType = t.publish?.enabled ? 'threads_post' : (STANDARD_FOR[r.taskType] ? r.taskType : 'general');
  t.title = r.title || t.title;
  t.relevant = (r.relevant || []).filter((id) => valid.has(id)).slice(0, 4);
  if (t.relevant.length < 2) t.relevant = mock.triage(t).relevant;
  t.agenda = r.agenda;
  say(t, 'chief', `[토론 소집] 안건: ${r.agenda}
확인할 질문: ${(r.keyQuestions || []).join(' / ')}
먼저 ${t.relevant.map(nm).join(', ')} 순서로 의견 주세요. 나머지 분들은 내용을 보고 필요한 부분에 짧게 반응해 주세요.`, 'chief');
  return 'debate';
};

stage.debate = async (t) => {
  // 1) 관련 담당자: 깊게 (앞사람 발언을 보고 이어서)
  for (const id of t.relevant) {
    const text = await ask({
      task: t, agentId: id, maxTokens: 700,
      system: systemFor(id),
      prompt: `${ceoBlock(t)}\n\n[안건] ${t.agenda}\n\n[지금까지 토론]\n${transcript(t)}\n\n너의 전문 관점에서 의견을 말하라. 4~7문장. 앞사람 의견에 동의/반박을 분명히 하고, CEO 지시의 문제점이 보이면 거침없이 지적하고, 구체적인 제안을 1개 이상 포함하라. 인사말 없이 바로 본론.`,
      mock: () => mock.opinion(id, t),
    });
    say(t, id, text, 'debate');
  }
  // 2) 관련성 낮은 직원: 한 번의 호출로 짧은 반응만 (토큰 절약)
  if (t.intensity !== 'light') {
    const others = staff().map((a) => a.id).filter((id) => !t.relevant.includes(id));
    const list = await ask({
      task: t, agentId: 'jopalo', json: true, maxTokens: 900,
      system: `너는 ${company().name}의 회의 진행 보조다. 여러 직원의 입장을 각각 대신해 짧은 반응을 쓴다.\n${companyBlock()}`,
      prompt: `${ceoBlock(t)}\n\n[지금까지 토론]\n${transcript(t)}\n\n아래 직원들은 이 업무와 직접 관련은 적다. 각자 자기 전문 관점에서 토론을 보고 "필요한 부분에만" 1~2문장으로 반응한다. 전체 방향을 바꿀 만한 한마디가 있다면 꼭 말한다. 할 말이 없으면 text를 null로.\n\n${others.map((id) => `- ${id}: ${nm(id)} — ${agent(id).role}`).join('\n')}\n\nJSON 배열만 출력: [{"agent":"id","text":"반응 또는 null"}]`,
      mock: () => mock.reactions(t, others),
    });
    let n = 0;
    for (const r of Array.isArray(list) ? list : []) {
      if (!r?.text || !others.includes(r.agent) || n >= (company().policy?.maxReactions || 5)) continue;
      say(t, r.agent, r.text, 'reaction'); n++;
    }
  }
  // 3) 깊은 토론: 관련 담당자 한 바퀴 더
  if (t.intensity === 'deep') {
    for (const id of t.relevant) {
      const text = await ask({
        task: t, agentId: id, maxTokens: 400, system: systemFor(id),
        prompt: `${ceoBlock(t)}\n\n[지금까지 토론]\n${transcript(t)}\n\n다른 사람들의 의견을 듣고 2~3문장으로 최종 입장을 정리하라. 입장이 바뀌었다면 왜 바뀌었는지 말하라.`,
        mock: () => mock.rebuttal(id),
      });
      say(t, id, text, 'debate');
    }
  }
  return 'assign';
};

stage.assign = async (t) => {
  const std = readStandard(t);
  const r = await ask({
    task: t, agentId: 'chief', json: true, maxTokens: 1500, system: systemFor('chief'),
    prompt: `${ceoBlock(t)}\n\n[토론 기록]\n${transcript(t)}\n\n[이 업무의 완료 기준]\n${std.text}\n\n토론을 정리하고 방향을 정해 담당자별로 일을 배정하라.
- 배정은 2~5개, 각 직원의 전문 영역에 맞게.
- 각 업무는 완료 기준의 어떤 항목을 책임지는지 알 수 있게 구체적으로.
${t.publish?.enabled ? '- 쓰레드 게시 업무이므로 "게시 문구"를 만드는 담당(문체리 권장)과 "게시 방식·기술 점검" 담당을 반드시 포함.\n' : ''}- CEO 지시에서 조정한 부분이 있으면 이유와 함께 밝혀라.
JSON만 출력:
{"summary":"토론 요약 2~3문장","direction":"확정 방향 한 문장","decisions":["결정 사항"],"ceoAdjustments":"CEO 지시 조정 내용과 이유 또는 '조정 없음'",
 "assignments":[{"agent":"직원 id","task":"구체적으로 할 일","deliverable":"결과물 이름"}]}`,
    mock: () => mock.assign(t),
  });
  const valid = new Set(staff().map((a) => a.id));
  t.direction = r.direction;
  t.summary = r.summary;
  t.decisions = r.decisions || [];
  t.ceoAdjustments = r.ceoAdjustments;
  t.assignments = (r.assignments || []).filter((a) => valid.has(a.agent)).map((a) => ({ ...a, round: t.round, status: 'todo' }));
  if (!t.assignments.length) throw new Error('비서실장이 업무를 배정하지 못했습니다');
  say(t, 'chief', `[토론 정리] ${r.summary}
[확정 방향] ${r.direction}
[결정] ${(r.decisions || []).join(' / ')}
[CEO 지시 조정] ${r.ceoAdjustments || '조정 없음'}

[업무 배정]
${t.assignments.map((a) => `· ${nm(a.agent)} → ${a.deliverable}: ${a.task}`).join('\n')}`, 'chief');
  return 'execute';
};

stage.execute = async (t) => {
  const std = readStandard(t);
  const todo = t.assignments.filter((a) => a.round === t.round && a.status !== 'done');
  for (const asg of todo) {
    const a = agent(asg.agent);
    const fix = (t.pendingFixes || []).find((f) => f.agent === asg.agent);
    const prev = t.assignments.filter((x) => x.agent === asg.agent && x.round < t.round && x.file).slice(-1)[0];
    const prevText = prev ? store.readDoc(t.id, prev.file) : '';
    let text = await ask({
      task: t, agentId: asg.agent, maxTokens: 2200, system: systemFor(asg.agent),
      prompt: `${ceoBlock(t)}\n\n[확정 방향] ${t.direction}\n[결정 사항] ${(t.decisions || []).join(' / ')}\n\n[너의 업무] ${asg.deliverable}: ${asg.task}
${fix ? `\n[비서실장 반려 사유 — 반드시 해결] ${fix.request}\n` : ''}${prevText ? `\n[네 이전 결과물]\n${cut(prevText, 3000)}\n` : ''}
[완료 기준 — 작업 전에 읽고, 이 기준으로 검수받는다]
${std.text}

${memoryDigest(t.taskType === 'analysis')}

마크다운 문서로 결과물을 작성하라.
- 첫 줄은 반드시 "> 한줄요약: (이 문서를 보면 무엇을 알 수 있는지 한 문장)"
- 그 다음 "## 결론"을 먼저, 그 뒤에 내용.
- 게시 문구를 쓴다면 코드블록(\`\`\`)에 넣고 글자 수를 적어라.`,
      mock: () => mock.execute(a, asg, t),
    });
    if (!/^\s*>\s*한줄요약/.test(text)) text = `> 한줄요약: ${a.name}의 ${asg.deliverable}\n\n${text}`;
    asg.file = `r${t.round}-${asg.agent}.md`;
    asg.summary = store.firstLineSummary(text);
    asg.status = 'done';
    store.saveDoc(t.id, asg.file, text);
    say(t, asg.agent, `작업 완료 — ${asg.deliverable}\n📄 ${asg.summary}`, 'work');
  }
  return 'review';
};

function latestDocs(t) {
  const byAgent = {};
  for (const a of t.assignments.filter((x) => x.file)) byAgent[a.agent] = a;
  return Object.values(byAgent);
}

stage.review = async (t) => {
  const std = readStandard(t);
  const items = checklistItems(std.text);
  const docs = latestDocs(t).map((a) => `### ${nm(a.agent)} — ${a.deliverable}\n${cut(store.readDoc(t.id, a.file), company().policy?.docCharLimit || 6000)}`).join('\n\n');
  say(t, 'chief', `결과물이 모두 올라왔습니다. 완료 기준(${std.file} + ceo-report.md)으로 검수합니다.`, 'chief');
  const r = await ask({
    task: t, agentId: 'chief', json: true, maxTokens: 1800, system: systemFor('chief'),
    prompt: `${ceoBlock(t)}\n\n[확정 방향] ${t.direction}\n\n[완료 기준]\n${std.text}\n\n[체크리스트 항목]\n${items.map((x, i) => `${i + 1}. ${x}`).join('\n')}\n\n[결과물]\n${docs}

체크리스트 항목 하나하나를 결과물 전체 기준으로 판정하라. 기준에 없는 이유로 반려하지 마라. 하나라도 치명적으로 미통과면 반려.
JSON만 출력:
{"verdict":"approve 또는 reject","checklist":[{"item":"항목","pass":true,"note":"짧은 메모"}],"reasons":["판정 이유"],
 "fixRequests":[{"agent":"직원 id","request":"무엇을 어떻게 고칠지 구체적으로"}],
 "lesson":"반려라면 다음에 같은 실수를 막을 교훈 한 문장, 승인이면 빈 문자열"}`,
    mock: () => mock.review(t, items),
  });
  const verdict = r.verdict === 'approve' ? 'approve' : 'reject';
  t.reviews.push({ round: t.round, verdict, checklist: r.checklist || [], reasons: r.reasons || [], fixRequests: r.fixRequests || [], ts: new Date().toISOString() });
  const failed = (r.checklist || []).filter((c) => !c.pass);
  if (verdict === 'reject') {
    t.pendingFixes = (r.fixRequests || []).filter((f) => agent(f.agent));
    if (r.lesson) store.appendMemory('lessons.md', `❌ 실패 · ${t.title}: ${r.lesson}`);
    say(t, 'chief', `🔴 반려합니다.
[미통과] ${failed.map((c) => c.item + (c.note ? ` (${c.note})` : '')).join(' / ') || '-'}
[사유] ${(r.reasons || []).join(' / ')}
[수정 요청]
${t.pendingFixes.map((f) => `· ${nm(f.agent)}: ${f.request}`).join('\n') || '-'}
CEO님, 반려 사유를 보시고 보강 지시를 내려주세요.`, 'review');
    const auto = company().policy?.autoRework || 0;
    if ((t.autoReworkUsed || 0) < auto) {
      t.autoReworkUsed = (t.autoReworkUsed || 0) + 1;
      t.round += 1;
      t.reinforcements.push({ round: t.round, text: '(비서실장 자동 재작업) 반려 사유를 모두 해결할 것', ts: new Date().toISOString() });
      return 'rework';
    }
    return 'rejected';
  }
  t.pendingFixes = [];
  say(t, 'chief', `🟢 검수 통과 (${t.reviews.length}회차). 모든 완료 기준 충족.${company().policy?.strategyEnabled !== false ? ' 전략실장 한수합에게 독립 검토를 요청합니다.' : ''}`, 'review');
  return company().policy?.strategyEnabled !== false ? 'strategy' : 'final';
};

stage.rework = async (t) => {
  const rein = t.reinforcements.slice(-1)[0];
  say(t, 'chief', `CEO 보강 지시를 접수했습니다: "${rein.text}"\n반려 사유와 합쳐서 보강 방향을 짧게 논의하겠습니다.`, 'chief');
  const who = [...new Set([...(t.pendingFixes || []).map((f) => f.agent), ...t.relevant.slice(0, 2)])].filter((id) => agent(id)).slice(0, 4);
  for (const id of who) {
    const fix = (t.pendingFixes || []).find((f) => f.agent === id);
    const text = await ask({
      task: t, agentId: id, maxTokens: 400, system: systemFor(id),
      prompt: `${ceoBlock(t)}\n\n[반려 사유] ${(t.reviews.slice(-1)[0]?.reasons || []).join(' / ')}\n${fix ? `[너에게 온 수정 요청] ${fix.request}\n` : ''}[최근 대화]\n${transcript(t, 3000)}\n\n보강 지시를 어떻게 반영할지 2~3문장으로 말하라.`,
      mock: () => fix ? `반려 사유 확인했습니다. ${fix.request} — 이 부분 바로 고치겠습니다.` : '보강 지시 확인했습니다. 제 파트도 같은 기준으로 다시 점검하겠습니다.',
    });
    say(t, id, text, 'debate');
  }
  const r = await ask({
    task: t, agentId: 'chief', json: true, maxTokens: 1000, system: systemFor('chief'),
    prompt: `${ceoBlock(t)}\n\n[반려 사유와 수정 요청]\n${JSON.stringify(t.reviews.slice(-1)[0] || {}, null, 1)}\n\n[보강 논의]\n${transcript(t, 3000)}\n\n보강 작업을 배정하라. 수정이 필요한 사람만. JSON만 출력:\n{"message":"배정 안내 한 문장","assignments":[{"agent":"id","task":"무엇을 고칠지","deliverable":"결과물 이름"}]}`,
    mock: () => mock.reworkAssign(t),
  });
  const valid = new Set(staff().map((a) => a.id));
  const next = (r.assignments || []).filter((a) => valid.has(a.agent)).map((a) => ({ ...a, round: t.round, status: 'todo' }));
  if (!next.length) throw new Error('보강 작업 배정 실패');
  t.assignments.push(...next);
  say(t, 'chief', `${r.message || '보강 작업을 배정합니다.'}\n${next.map((a) => `· ${nm(a.agent)} → ${a.deliverable}: ${a.task}`).join('\n')}`, 'chief');
  return 'execute';
};

stage.strategy = async (t) => {
  const docs = latestDocs(t).map((a) => `- ${nm(a.agent)} ${a.deliverable}: ${a.summary}\n${cut(store.readDoc(t.id, a.file), 1500)}`).join('\n\n');
  const r = await ask({
    task: t, agentId: 'hansuhap', json: true, maxTokens: 1500, system: systemFor('hansuhap'),
    prompt: `${ceoBlock(t)}\n\n[비서실장이 승인한 방향] ${t.direction}\n[결정] ${(t.decisions || []).join(' / ')}\n\n[승인된 결과물]\n${docs}

너는 승인권이 없다. 같은 모델끼리 검토하면 함께 놓치는 맹점을 찾는 것이 임무다.
이 방향으로 "실제 실행했을 때" 생길 수 있는 문제를 독립적으로 제기하고 권고안을 내라. 최대 4개. 사소한 것 말고 결과를 바꿀 만한 것만.
JSON만 출력:
{"verdict":"go|caution|rethink","summary":"한 문장 총평","concerns":[{"issue":"문제","why":"왜 문제인지","severity":"high|mid|low"}],"recommendations":["권고안"]}`,
    mock: () => mock.strategy(t),
  });
  t.strategy = { ...r, ts: new Date().toISOString(), model: mode().gpt ? company().models?.strategist : mode().claude ? `${company().models?.staff} (GPT 키 없음 → 클로드로 대체)` : 'demo' };
  const label = { go: '🟢 실행 권고', caution: '🟡 주의 후 실행', rethink: '🔴 재검토 권고' }[r.verdict] || r.verdict;
  say(t, 'hansuhap', `${label} — ${r.summary}
[문제 제기]
${(r.concerns || []).map((c) => `· (${c.severity}) ${c.issue}: ${c.why}`).join('\n')}
[권고]
${(r.recommendations || []).map((x) => `· ${x}`).join('\n')}
※ 저는 의견만 드립니다. 반영 여부는 비서실장이 판단합니다.`, 'strategy');
  return 'final';
};

stage.final = async (t) => {
  const limit = company().policy?.threadsTextLimit || 500;
  const docs = latestDocs(t).map((a) => `### ${nm(a.agent)} — ${a.deliverable}\n${cut(store.readDoc(t.id, a.file), 3000)}`).join('\n\n');
  const std = fs.readFileSync(path.join(P.standards, 'ceo-report.md'), 'utf8');
  const r = await ask({
    task: t, agentId: 'chief', json: true, maxTokens: 2500, system: systemFor('chief'),
    prompt: `${ceoBlock(t)}\n\n[확정 방향] ${t.direction}\n\n[전략실장 의견]\n${JSON.stringify(t.strategy || '전략 검토 없음')}\n\n[최종 결과물]\n${docs}\n\n[CEO 보고서 기준]\n${std}

1) 전략실장 권고 각각을 반영할지 판단하라 (근거 포함).
2) CEO 보고서 기준 순서대로 보고서 내용을 작성하라. 요약은 정확히 3개.
${t.publish?.enabled ? `3) 최종 게시 문구를 확정하라. ${limit}자 이내. 결과물 중 가장 좋은 안을 기반으로, 전략 권고 반영.\n` : ''}JSON만 출력:
{"strategyDecisions":[{"recommendation":"권고","accept":true,"reason":"이유"}],
 "report":{"headline":"결론 한 줄","decisionNeeded":"CEO가 결정할 것","summary":["요약1","요약2","요약3"],
   "findings":[{"title":"","detail":"","evidence":""}],"risks":[{"risk":"","mitigation":""}],"nextActions":[{"owner":"담당자 이름","action":"","due":"날짜"}]},
 "post":${t.publish?.enabled ? '{"text":"최종 게시 문구"}' : 'null'},
 "memoryNote":"회사 기억에 남길 의사결정 한 줄"}`,
    mock: () => mock.final(t),
  });
  if (t.publish?.enabled) {
    let text = r.post?.text || '';
    if (!text) throw new Error('비서실장이 게시 문구를 확정하지 못했습니다');
    if (text.length > limit) {
      text = await ask({
        task: t, agentId: 'moncherry', maxTokens: 800, system: systemFor('moncherry'),
        prompt: `아래 쓰레드 게시 문구가 ${text.length}자다. 의미와 톤은 유지하고 ${limit - 20}자 이내로 줄여라. 문구만 출력.\n\n${text}`,
        mock: () => text.slice(0, limit - 20),
      });
      text = text.replace(/^```\w*\n?|```$/g, '').trim().slice(0, limit);
    }
    r.post = { text };
  }
  t.final = { strategyDecisions: r.strategyDecisions || [], report: r.report || {}, post: r.post || null };
  store.saveDoc(t.id, 'final-report.html', report.renderHTML(t));
  store.saveDoc(t.id, 'final-report.md', report.renderMarkdown(t));
  if (r.memoryNote) store.appendMemory('company-memory.md', r.memoryNote);
  store.appendMemory('lessons.md', `✅ 성공 · ${t.title}: 검수 ${t.reviews.length}회 만에 통과${t.reviews.length > 1 ? ` (반려 사유: ${(t.reviews[0].reasons || [])[0] || '-'})` : ''}`);

  const acc = (r.strategyDecisions || []).filter((x) => x.accept).length;
  say(t, 'chief', `[최종 판단] 전략실장 권고 ${(r.strategyDecisions || []).length}건 중 ${acc}건 반영.
[결론] ${r.report?.headline}
📑 최종 보고서가 준비됐습니다.`, 'chief');

  if (t.publish?.enabled) {
    t.publish = { ...t.publish, status: 'pending', text: r.post.text, createdAt: new Date().toISOString() };
    if (t.approver === 'chief') {
      say(t, 'chief', '이번 업무는 비서실장 전결입니다. 바로 게시를 진행합니다.', 'publish');
      return 'publishing';
    }
    say(t, 'chief', 'CEO님, 발행 큐에서 게시 문구를 확인하고 승인해 주세요.', 'publish');
    return 'publish_wait';
  }
  return 'ceo_wait';
};

function mediaFor(t) {
  const s = secrets();
  if (t.publish.videoUrl) return { type: 'VIDEO', url: t.publish.videoUrl };
  if (t.publish.videoFile) {
    if (!s.PUBLIC_URL) throw new Error(`영상 "${t.publish.videoFile}"은 쓰레드 API로 직접 올릴 수 없습니다(공개 인터넷 주소 필요). 발행 큐에서 "수동 게시"를 이용하거나, 설정에 PUBLIC_URL을 입력하세요.`);
    return { type: 'VIDEO', url: `${s.PUBLIC_URL}/media/${encodeURIComponent(t.publish.videoFile)}` };
  }
  return { type: 'TEXT' };
}

stage.publishing = async (t) => {
  try {
    if (!threads.status().connected && mode().demo) {
      t.publish.status = 'simulated';
      t.publish.result = { mediaId: 'demo', permalink: '', publishedAt: new Date().toISOString() };
      say(t, 'jopalo', '🧪 체험 모드라 실제 게시 대신 "모의 게시"로 처리했습니다. 쓰레드를 연결하면 실제로 올라갑니다.', 'publish');
      return 'done';
    }
    const result = await threads.publish(t.publish.text, mediaFor(t));
    t.publish.status = 'published';
    t.publish.result = result;
    say(t, 'jopalo', `✅ 쓰레드에 게시했습니다. ${result.permalink || ''}\n24시간 뒤 소셜 탭에서 "성과 새로고침"을 누르면 수치가 기록됩니다.`, 'publish');
    store.appendMemory('company-memory.md', `쓰레드 게시: "${t.publish.text.split('\n')[0]}" ${result.permalink || ''}`);
    return 'done';
  } catch (e) {
    t.publish.status = 'failed';
    t.publish.error = e.message;
    say(t, 'anberg', `⚠️ 게시 실패: ${e.message}`, 'publish');
    return 'publish_wait';
  }
};

// ---------- 실행 루프 ----------
async function advance(id) {
  if (running.has(id)) return;
  running.add(id);
  try {
    for (;;) {
      const t = store.getTask(id);
      if (!t || WAIT.has(t.stage)) break;
      const fn = stage[t.stage];
      if (!fn) break;
      const next = await fn(t);
      t.stage = next;
      t.status = STAGES[next];
      store.saveTask(t);
    }
  } catch (e) {
    const t = store.getTask(id);
    if (t) {
      t.failedStage = t.stage;
      t.stage = 'failed';
      t.status = STAGES.failed;
      t.error = e.message;
      t.messages.push({ id: t.messages.length + 1, from: 'system', kind: 'system', text: `⚠️ 오류로 멈췄습니다: ${e.message}\n(작업 큐에서 "다시 시도"를 누르면 멈춘 단계부터 이어서 합니다)`, round: t.round, ts: new Date().toISOString() });
      store.saveTask(t);
    }
    console.error('[업무 오류]', id, e);
  } finally {
    running.delete(id);
  }
}

// ---------- CEO 행동 ----------
function create(input) {
  const today = new Date().toISOString().slice(0, 10);
  const instruction = String(input.instruction || '').trim();
  if (!instruction) throw new Error('지시 내용을 입력하세요');
  const videoFile = input.videoFile && fs.existsSync(path.join(P.videos, path.basename(input.videoFile))) ? path.basename(input.videoFile) : '';
  const t = {
    id: store.newId(),
    title: instruction.slice(0, 24),
    instruction,
    deadline: input.deadline || today,
    intensity: ['light', 'normal', 'deep'].includes(input.intensity) ? input.intensity : 'normal',
    approver: input.approver === 'chief' ? 'chief' : 'ceo',
    publish: { enabled: !!input.publish, videoFile, videoUrl: /^https:\/\//.test(input.videoUrl || '') ? input.videoUrl : '' },
    stage: 'triage', status: STAGES.triage, round: 1,
    messages: [], assignments: [], reviews: [], reinforcements: [], relevant: [],
    usage: { calls: 0, in: 0, out: 0 },
    createdAt: new Date().toISOString(),
  };
  t.messages.push({ id: 1, from: 'ceo', kind: 'ceo', text: `${instruction}\n(마감: ${t.deadline} · 토론 강도: ${{ light: '가볍게', normal: '보통', deep: '깊게' }[t.intensity]} · 최종 승인: ${t.approver === 'ceo' ? 'CEO' : '비서실장 전결'})`, round: 1, ts: t.createdAt });
  store.saveTask(t);
  advance(t.id);
  return t;
}

function reinforce(id, text) {
  const t = store.getTask(id);
  if (!t) throw new Error('업무를 찾을 수 없습니다');
  if (!['rejected', 'ceo_wait', 'publish_wait'].includes(t.stage)) throw new Error(`지금 단계(${t.status})에서는 보강 지시를 할 수 없습니다`);
  if (!String(text || '').trim()) throw new Error('보강 지시 내용을 입력하세요');
  if (t.stage !== 'rejected') {
    // 승인 대기 중 보강 → 해당 결과물 전체를 수정 대상으로
    t.pendingFixes = latestDocs(t).map((a) => ({ agent: a.agent, request: `CEO 보강 지시 반영: ${text}` }));
    if (t.publish?.enabled) t.publish = { enabled: true, videoFile: t.publish.videoFile, videoUrl: t.publish.videoUrl };
  }
  t.round += 1;
  t.reinforcements.push({ round: t.round, text: text.trim(), ts: new Date().toISOString() });
  t.messages.push({ id: t.messages.length + 1, from: 'ceo', kind: 'ceo', text: `[보강 지시] ${text.trim()}`, round: t.round, ts: new Date().toISOString() });
  t.stage = 'rework';
  t.status = STAGES.rework;
  store.saveTask(t);
  advance(id);
  return t;
}

function approve(id, { text } = {}) {
  const t = store.getTask(id);
  if (!t) throw new Error('업무를 찾을 수 없습니다');
  if (t.stage === 'ceo_wait') {
    t.messages.push({ id: t.messages.length + 1, from: 'ceo', kind: 'ceo', text: '승인합니다.', round: t.round, ts: new Date().toISOString() });
    t.stage = 'done'; t.status = STAGES.done;
    store.appendMemory('company-memory.md', `CEO 승인: ${t.title} — ${t.final?.report?.headline || ''}`);
    store.saveTask(t);
    return t;
  }
  if (t.stage === 'publish_wait') {
    if (typeof text === 'string' && text.trim()) t.publish.text = text.trim().slice(0, company().policy?.threadsTextLimit || 500);
    t.messages.push({ id: t.messages.length + 1, from: 'ceo', kind: 'ceo', text: '게시를 승인합니다.', round: t.round, ts: new Date().toISOString() });
    t.stage = 'publishing'; t.status = STAGES.publishing;
    store.saveTask(t);
    advance(id);
    return t;
  }
  throw new Error(`지금 단계(${t.status})에서는 승인할 수 없습니다`);
}

function manualPublished(id, permalink) {
  const t = store.getTask(id);
  if (!t || t.stage !== 'publish_wait') throw new Error('발행 대기 중인 업무가 아닙니다');
  t.publish.status = 'manual';
  t.publish.result = { mediaId: '', permalink: permalink || '', publishedAt: new Date().toISOString(), manual: true };
  t.messages.push({ id: t.messages.length + 1, from: 'ceo', kind: 'ceo', text: `직접(수동) 게시했습니다. ${permalink || ''}`, round: t.round, ts: new Date().toISOString() });
  t.stage = 'done'; t.status = STAGES.done;
  store.saveTask(t);
  return t;
}

function cancel(id) {
  const t = store.getTask(id);
  if (!t) throw new Error('업무를 찾을 수 없습니다');
  if (running.has(id)) throw new Error('진행 중인 단계가 끝난 뒤에 취소할 수 있습니다');
  t.stage = 'done'; t.status = '취소됨';
  if (t.publish?.status === 'pending' || t.publish?.status === 'failed') t.publish.status = 'rejected';
  t.messages.push({ id: t.messages.length + 1, from: 'ceo', kind: 'ceo', text: '이 업무는 취소합니다.', round: t.round, ts: new Date().toISOString() });
  store.saveTask(t);
  return t;
}

function retry(id) {
  const t = store.getTask(id);
  if (!t || t.stage !== 'failed') throw new Error('오류로 멈춘 업무가 아닙니다');
  t.stage = t.failedStage || 'triage';
  t.status = STAGES[t.stage];
  t.error = '';
  store.saveTask(t);
  advance(id);
  return t;
}

async function refreshInsights(id) {
  const t = store.getTask(id);
  if (!t?.publish?.result?.mediaId || t.publish.result.mediaId === 'demo') throw new Error('API로 게시된 글만 성과를 불러올 수 있습니다');
  t.publish.insights = await threads.insights(t.publish.result.mediaId);
  store.saveTask(t);
  return t.publish.insights;
}

// 서버가 꺼졌다 켜졌을 때 진행 중이던 업무 이어서 하기
function resumeAll() {
  for (const t of store.listTasks()) if (!WAIT.has(t.stage)) advance(t.id);
}

module.exports = { STAGES, create, reinforce, approve, manualPublished, cancel, retry, refreshInsights, resumeAll, isRunning: (id) => running.has(id) };
